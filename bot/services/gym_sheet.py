"""Интеграция сценария 1 с реальной Google-таблицей расписания клиники.

В отличие от остальных сценариев, запись в общий зал пишется не плоским логом,
а прямо в существующую таблицу администратора: один лист на календарный день
(«31.08 ПН», «01.09 ВТ», …), сетка «слот × аппарат», ФИО прямо в ячейке.

Эта таблица — источник истины по занятости (если ячейка непустая — место занято,
даже если это вписал администратор вручную мимо бота). `bot.db.models.GymBooking`
остаётся только зеркалом для истории и не используется для проверки доступности.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import date

import gspread
from google.oauth2.service_account import Credentials

from bot.config import settings

log = logging.getLogger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Реальная сетка сеансов зала клиники: нерегулярный шаг (не выводится формулой),
# поэтому задана явным списком, как в таблице администратора.
GYM_SLOTS: list[str] = [
    "10:10 - 10:40", "11:00 - 11:30", "11:50 - 12:20", "12:40 - 13:10",
    "13:30 - 14:00", "14:20 - 14:50", "15:10 - 15:40", "16:00 - 16:30",
    "16:50 - 17:20", "17:40 - 18:10", "18:30 - 19:00", "19:20 - 19:50",
]

BOOKED_BY_BOT_SUFFIX = " (бот)"

_WEEKDAY_ABBR = {1: "ПН", 2: "ВТ", 3: "СР", 4: "ЧТ", 5: "ПТ", 6: "СБ", 7: "ВС"}
_TITLE_DATE_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})")
_APPARATUS_RE = re.compile(r"Аппарат\s*(\d+)", re.IGNORECASE)


def slot_start(slot_label: str) -> str:
    """"10:10 - 10:40" -> "10:10" (для отсева прошедших слотов сегодняшнего дня)."""
    return slot_label.split("-", 1)[0].strip()


def session_slots_for_date(day: date) -> list[str]:
    """Сеансовая сетка клиники на дату (та же для зала и для инструктора).
    Для сегодняшнего дня прошедшие слоты отфильтрованы.
    """
    from bot.utils.dates import now_tz, today_tz

    if day != today_tz():
        return list(GYM_SLOTS)
    now_hm = now_tz().strftime("%H:%M")
    return [s for s in GYM_SLOTS if slot_start(s) > now_hm]


def sheet_title_for(day: date) -> str:
    """Каноничное имя листа для создаваемой даты, напр. "05.09 СБ"."""
    return f"{day.day:02d}.{day.month:02d} {_WEEKDAY_ABBR[day.isoweekday()]}"


def _parse_title_date(title: str, today: date) -> date | None:
    """Достать дату из имени листа независимо от того, как её набили руками
    (с ведущим нулём или без — в таблице клиники оба варианта встречаются)."""
    match = _TITLE_DATE_RE.match(title.strip())
    if not match:
        return None
    day, month = int(match.group(1)), int(match.group(2))
    for year in (today.year, today.year + 1, today.year - 1):
        try:
            candidate = date(year, month, day)
        except ValueError:
            continue
        if abs((candidate - today).days) <= 200:
            return candidate
    return None


class GymScheduleClient:
    """Клиент таблицы расписания зала. Отдельный от лога заявок (services.sheets)."""

    def __init__(self) -> None:
        self.enabled = bool(settings.gym_schedule_sheet_id)
        self._spreadsheet = None
        self._locks: dict[str, asyncio.Lock] = {}

    def _open(self):
        if self._spreadsheet is None:
            creds = Credentials.from_service_account_file(
                settings.google_credentials_path, scopes=_SCOPES
            )
            self._spreadsheet = gspread.authorize(creds).open_by_key(
                settings.gym_schedule_sheet_id
            )
        return self._spreadsheet

    def _lock_for(self, key: str) -> asyncio.Lock:
        lock = self._locks.get(key)
        if lock is None:
            lock = self._locks[key] = asyncio.Lock()
        return lock

    def _find_or_create_ws_sync(self, day: date):
        spreadsheet = self._open()
        for worksheet in spreadsheet.worksheets():
            if _parse_title_date(worksheet.title, day) == day:
                return worksheet

        template_name = (
            settings.gym_template_saturday
            if day.isoweekday() == 6
            else settings.gym_template_weekday
        )
        template = spreadsheet.worksheet(template_name)
        log.info("создаю лист расписания на %s из шаблона «%s»", day, template_name)
        return template.duplicate(new_sheet_name=sheet_title_for(day))

    async def get_worksheet(self, day: date):
        return await asyncio.to_thread(self._find_or_create_ws_sync, day)

    @staticmethod
    def _parse_grid(values: list[list[str]]) -> tuple[dict[int, int], dict[str, int]]:
        """Вернуть {номер аппарата: индекс столбца} и {подпись слота: индекс строки}.

        Ищем по заголовкам и подписям времени, а не по фиксированным номерам ячеек —
        так лист остаётся рабочим, даже если в нём слегка поменяли раскладку.
        """
        header = values[0] if values else []
        apparatus_cols: dict[int, int] = {}
        for col_idx, cell in enumerate(header):
            match = _APPARATUS_RE.search(cell or "")
            if match:
                apparatus_cols[int(match.group(1))] = col_idx

        slot_rows: dict[str, int] = {}
        for row_idx, row in enumerate(values):
            label = (row[0] if row else "").strip()
            if label in GYM_SLOTS:
                slot_rows[label] = row_idx

        return apparatus_cols, slot_rows

    @staticmethod
    def _row_free_apparatuses(
        row: list[str], apparatus_cols: dict[int, int], apparatus_count: int
    ) -> set[int]:
        free: set[int] = set()
        for number in range(1, apparatus_count + 1):
            col = apparatus_cols.get(number)
            cell = row[col].strip() if col is not None and col < len(row) else ""
            if not cell:
                free.add(number)
        return free

    async def slot_loads(
        self, day: date, slot_labels: list[str], apparatus_count: int
    ) -> dict[str, tuple[int, int]]:
        """Подпись слота -> (свободно, всего) по текущему состоянию листа."""
        worksheet = await self.get_worksheet(day)
        values = await asyncio.to_thread(worksheet.get_all_values)
        apparatus_cols, slot_rows = self._parse_grid(values)

        loads: dict[str, tuple[int, int]] = {}
        for label in slot_labels:
            row_idx = slot_rows.get(label)
            row = values[row_idx] if row_idx is not None else []
            free = self._row_free_apparatuses(row, apparatus_cols, apparatus_count)
            loads[label] = (len(free), apparatus_count)
        return loads

    async def free_apparatuses(
        self, day: date, slot_label: str, apparatus_count: int
    ) -> set[int]:
        worksheet = await self.get_worksheet(day)
        values = await asyncio.to_thread(worksheet.get_all_values)
        apparatus_cols, slot_rows = self._parse_grid(values)
        row_idx = slot_rows.get(slot_label)
        row = values[row_idx] if row_idx is not None else []
        return self._row_free_apparatuses(row, apparatus_cols, apparatus_count)

    async def book(
        self, day: date, slot_label: str, apparatus_no: int, full_name: str
    ) -> bool:
        """Записать ФИО в ячейку, если она пустая. `False`, если уже занято.

        Сериализовано локом на дату — исключает гонку между двумя пользователями
        бота, читающими и пишущими один и тот же лист почти одновременно.
        """
        async with self._lock_for(day.isoformat()):
            worksheet = await self.get_worksheet(day)

            def _book_sync() -> bool:
                values = worksheet.get_all_values()
                apparatus_cols, slot_rows = self._parse_grid(values)
                row_idx = slot_rows.get(slot_label)
                col_idx = apparatus_cols.get(apparatus_no)
                if row_idx is None or col_idx is None:
                    raise RuntimeError(
                        f"не найдены строка/столбец для слота {slot_label!r} "
                        f"/ аппарата {apparatus_no} на листе {worksheet.title!r}"
                    )
                row = values[row_idx]
                current = row[col_idx].strip() if col_idx < len(row) else ""
                if current:
                    return False
                a1 = gspread.utils.rowcol_to_a1(row_idx + 1, col_idx + 1)
                worksheet.update(range_name=a1, values=[[full_name + BOOKED_BY_BOT_SUFFIX]])
                return True

            return await asyncio.to_thread(_book_sync)


gym_schedule = GymScheduleClient()
