"""Конфигурация приложения из переменных окружения (`.env`).

Сеансовая сетка времени (12 слотов вида "10:10 - 10:40") — общая для зала и
инструктора — задана в :mod:`bot.services.gym_sheet` как факт о клинике, а не
выводится из настроек.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_int_list(raw: str) -> list[int]:
    return [int(part.strip()) for part in raw.split(",") if part.strip()]


class Settings(BaseSettings):
    """Типизированные настройки бота."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    # --- Telegram ---
    bot_token: str
    # Списки читаем как строку и парсим в свойствах — не зависим от версии
    # pydantic-settings и её JSON-декодера для сложных типов.
    admin_chat_ids_raw: str = Field(default="", alias="ADMIN_CHAT_IDS")
    emergency_phone: str = "+70000000000"

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./data/bot.db"

    # --- Google Sheets: плоский лог заявок (сценарии 3-9) ---
    google_sheet_id: str = ""
    google_credentials_path: str = "./credentials.json"

    # --- Google Sheets: реальная таблица расписания зала (сценарий 1) ---
    # Отдельная от лога заявок таблица «РАСПИСАНИЕ …» — один лист на день,
    # сетка «слот × аппарат», ФИО прямо в ячейке. Источник истины по занятости.
    # Тот же service account (google_credentials_path) должен быть Editor'ом и на ней.
    gym_schedule_sheet_id: str = Field(default="", alias="GYM_SCHEDULE_SHEET_ID")
    gym_template_weekday: str = Field(default="копия пн-пт", alias="GYM_TEMPLATE_WEEKDAY")
    gym_template_saturday: str = Field(default="копия сб", alias="GYM_TEMPLATE_SATURDAY")
    gym_apparatus_count: int = Field(default=8, alias="GYM_APPARATUS_COUNT")

    # --- Расписание записи ---
    timezone: str = "Asia/Almaty"
    booking_horizon_days: int = 14
    working_days_raw: str = Field(default="1,2,3,4,5,6", alias="WORKING_DAYS")
    # Макс. записей к инструктору на один сеанс (слоты — та же сетка, что у зала).
    instructor_slots_per_hour: int = Field(default=2, alias="INSTRUCTOR_SLOTS_PER_HOUR")

    # --- Прочее ---
    log_level: str = "INFO"
    sheet_sync_interval_seconds: int = 30
    sheet_sync_max_attempts: int = 20

    @property
    def admin_chat_ids(self) -> list[int]:
        return _parse_int_list(self.admin_chat_ids_raw)

    @property
    def working_days(self) -> list[int]:
        """Рабочие дни в формате `isoweekday()`: 1=Пн ... 7=Вс."""
        return _parse_int_list(self.working_days_raw)


settings = Settings()  # type: ignore[call-arg]
