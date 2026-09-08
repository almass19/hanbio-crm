"""Работа с датами и слотами в часовом поясе центра."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from bot.config import settings

_MONTHS_NOM = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]
_MONTHS_GEN = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]
WEEKDAYS_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def get_tz() -> ZoneInfo:
    return ZoneInfo(settings.timezone)


def now_tz() -> datetime:
    return datetime.now(get_tz())


def today_tz() -> date:
    return now_tz().date()


def is_working_day(day: date) -> bool:
    """`isoweekday()`: Пн=1 ... Вс=7 — совпадает с форматом `WORKING_DAYS`."""
    return day.isoweekday() in settings.working_days


def horizon_dates() -> list[date]:
    """Доступные для записи даты: рабочие дни в пределах горизонта, начиная с сегодня."""
    start = today_tz()
    return [
        start + timedelta(days=offset)
        for offset in range(settings.booking_horizon_days + 1)
        if is_working_day(start + timedelta(days=offset))
    ]


def is_bookable_date(day: date) -> bool:
    return day in set(horizon_dates())


def month_name_nom(month: int) -> str:
    return _MONTHS_NOM[month - 1]


def format_date(day: date) -> str:
    """`5 марта 2026`."""
    return f"{day.day} {_MONTHS_GEN[day.month - 1]} {day.year}"


def format_dt(moment: datetime) -> str:
    """`05.03.2026 14:30` в часовом поясе центра."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=ZoneInfo("UTC"))
    return moment.astimezone(get_tz()).strftime("%d.%m.%Y %H:%M")
