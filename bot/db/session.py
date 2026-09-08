"""Асинхронный движок и фабрика сессий SQLAlchemy.

Локально — SQLite (`sqlite+aiosqlite://`). В проде — общий с CRM Postgres
(Supabase), `postgresql+asyncpg://…`; тогда бот подключается к схеме, которую
создаёт `crm/supabase/migrations/0001_init.sql`, а Alembic не запускается
(см. `bot/main.py`).
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import settings

_url = settings.database_url
is_postgres = _url.startswith("postgresql")


def _ensure_sqlite_dir(url: str) -> None:
    """Создать каталог для файловой SQLite-базы, если его ещё нет."""
    if not url.startswith("sqlite"):
        return
    path_part = url.split("///", 1)[-1]
    if not path_part or path_part == ":memory:":
        return
    Path(path_part).parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_dir(_url)

_engine_kwargs: dict = {"future": True}
if is_postgres:
    # Supabase: TLS обязателен. Для бота используйте Session pooler (порт 5432)
    # или прямое подключение — не Transaction pooler (пункт в CRM README).
    _engine_kwargs["connect_args"] = {"ssl": True}
    _engine_kwargs["pool_pre_ping"] = True

engine = create_async_engine(_url, **_engine_kwargs)

Sessionmaker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)
