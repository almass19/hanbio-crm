"""Клиент плоского лога заявок (сценарии 2-9) в Google Sheets. Все вызовы
синхронные — из async-кода дёргать через ``asyncio.to_thread``
(см. :mod:`bot.services.sync`).

Google Sheets — только витрина. Если `GOOGLE_SHEET_ID` пуст или креды битые,
клиент переходит в режим ``enabled = False`` и бот продолжает работать.

Запись в общий зал (сценарий 1) сюда не пишет — она использует настоящую
таблицу расписания клиники, см. :mod:`bot.services.gym_sheet`.
"""

from __future__ import annotations

import logging

import gspread
from google.oauth2.service_account import Credentials

from bot import texts as T
from bot.config import settings

log = logging.getLogger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

REQUESTS_HEADERS = [
    "Дата создания", "Тип обращения", "Telegram ID", "Username",
    "ФИО", "Телефон", "Детали", "Статус",
]
_HEADERS: dict[str, list[str]] = {
    T.SHEET_REQUESTS: REQUESTS_HEADERS,
}


class SheetsClient:
    def __init__(self) -> None:
        self.enabled = bool(settings.google_sheet_id)
        self._spreadsheet = None

    def _open(self):
        if self._spreadsheet is None:
            creds = Credentials.from_service_account_file(
                settings.google_credentials_path, scopes=_SCOPES
            )
            self._spreadsheet = gspread.authorize(creds).open_by_key(settings.google_sheet_id)
        return self._spreadsheet

    def ensure_structure(self) -> None:
        """Создать листы и заголовки, если их нет. Битые креды -> режим отключён."""
        if not self.enabled:
            log.warning("Google Sheets отключены: GOOGLE_SHEET_ID пуст")
            return
        try:
            spreadsheet = self._open()
            existing = {ws.title: ws for ws in spreadsheet.worksheets()}
            for name, headers in _HEADERS.items():
                worksheet = existing.get(name)
                if worksheet is None:
                    worksheet = spreadsheet.add_worksheet(
                        title=name, rows=1000, cols=len(headers)
                    )
                if worksheet.row_values(1) != headers:
                    worksheet.update(values=[headers], range_name="A1")
        except Exception:
            self.enabled = False
            log.exception("Google Sheets недоступны при старте — синхронизация отключена")

    def append(self, sheet_name: str, row: list) -> None:
        if not self.enabled:
            raise RuntimeError("Google Sheets отключены")
        worksheet = self._open().worksheet(sheet_name)
        worksheet.append_row(
            ["" if value is None else str(value) for value in row],
            value_input_option="USER_ENTERED",
        )


sheets = SheetsClient()
