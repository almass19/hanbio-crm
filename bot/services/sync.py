"""Фоновая задача досылки строк в Google Sheets с ретраями и backoff."""

from __future__ import annotations

import asyncio
import logging
import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.config import settings
from bot.db.models import SheetSyncQueue
from bot.services.sheets import SheetsClient
from bot.utils.dates import now_tz

log = logging.getLogger(__name__)

_MAX_BACKOFF_SECONDS = 600
_BASE_BACKOFF_SECONDS = 30


async def sheet_sync_loop(
    stop: asyncio.Event,
    sessionmaker: async_sessionmaker,
    sheets: SheetsClient,
) -> None:
    """Крутится до установки `stop`. Каждый тик пытается отправить неотправленные строки."""
    if not sheets.enabled:
        log.warning("sheet_sync_loop: Google Sheets отключены, задача простаивает")

    backoff_until: dict[int, float] = {}

    while not stop.is_set():
        try:
            await _process_pending(sessionmaker, sheets, backoff_until)
        except Exception:
            log.exception("тик синхронизации Google Sheets упал")

        try:
            await asyncio.wait_for(stop.wait(), timeout=settings.sheet_sync_interval_seconds)
        except asyncio.TimeoutError:
            pass


async def _process_pending(
    sessionmaker: async_sessionmaker,
    sheets: SheetsClient,
    backoff_until: dict[int, float],
) -> None:
    if not sheets.enabled:
        return

    async with sessionmaker() as session:
        rows = (
            await session.execute(
                select(SheetSyncQueue)
                .where(
                    SheetSyncQueue.synced_at.is_(None),
                    SheetSyncQueue.attempts < settings.sheet_sync_max_attempts,
                )
                .order_by(SheetSyncQueue.id)
                .limit(25)
            )
        ).scalars().all()

        now = time.monotonic()
        for row in rows:
            if backoff_until.get(row.id, 0.0) > now:
                continue
            try:
                await asyncio.to_thread(sheets.append, row.sheet_name, row.row_data)
                row.synced_at = now_tz()
                row.last_error = None
                backoff_until.pop(row.id, None)
            except Exception as exc:  # noqa: BLE001 — сохраняем текст ошибки в очередь
                row.attempts += 1
                row.last_error = str(exc)[:500]
                delay = min(
                    _MAX_BACKOFF_SECONDS,
                    _BASE_BACKOFF_SECONDS * (2 ** min(row.attempts, 5)),
                )
                backoff_until[row.id] = now + delay
                log.warning(
                    "строка %s в Sheets не ушла (попытка %s): %s",
                    row.id, row.attempts, exc,
                )

        await session.commit()
