"""Точка входа: миграции, bootstrap Google Sheets, регистрация роутеров,
запуск long polling и фоновой задачи синхронизации.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.db.session import Sessionmaker, engine
from bot.handlers import get_routers
from bot.services.sheets import sheets
from bot.services.sync import sheet_sync_loop

BASE_DIR = Path(__file__).resolve().parent.parent
log = logging.getLogger("bot")


def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )


def _run_migrations_sync() -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(BASE_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BASE_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url.replace("+aiosqlite", ""))
    cfg.attributes["embedded"] = True  # env.py: не переопределять логирование приложения
    command.upgrade(cfg, "head")


async def _on_startup() -> None:
    if settings.database_url.startswith("sqlite"):
        await asyncio.to_thread(_run_migrations_sync)
        log.info("миграции применены")
    else:
        # Postgres (Supabase) — схема создаётся из crm/supabase/migrations/,
        # Alembic здесь не запускаем.
        log.info("Postgres: схема управляется извне, Alembic пропущен")
    await asyncio.to_thread(sheets.ensure_structure)
    log.info("Google Sheets: enabled=%s", sheets.enabled)


async def main() -> None:
    setup_logging()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp["sessionmaker"] = Sessionmaker

    for router in get_routers():
        dp.include_router(router)

    await _on_startup()

    stop_event = asyncio.Event()
    sync_task = asyncio.create_task(
        sheet_sync_loop(stop_event, Sessionmaker, sheets), name="sheet-sync"
    )

    try:
        await _start_polling_with_retry(bot, dp)
    finally:
        stop_event.set()
        sync_task.cancel()
        await asyncio.gather(sync_task, return_exceptions=True)
        await bot.session.close()
        await engine.dispose()


async def _start_polling_with_retry(bot: Bot, dp: Dispatcher) -> None:
    """`dp.start_polling` сам ретраит сбои внутри цикла get_updates, но первый
    вызов — `bot.me()` — ничем не защищён: если DNS/сеть моргнёт ровно в этот
    момент, необработанное исключение валит процесс целиком (а не просто
    сессию). Оборачиваем старт в свой ретрай с backoff, чтобы временный сбой
    в момент запуска не убивал бота — сторожу тогда нечего перезапускать.
    """
    delay = 1.0
    while True:
        try:
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
            return  # штатная остановка (SIGINT/SIGTERM обработаны внутри aiogram)
        except (asyncio.CancelledError, KeyboardInterrupt):
            raise
        except Exception:
            log.exception("polling упал на старте, ретрай через %.0f с", delay)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 60.0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("остановлено")
