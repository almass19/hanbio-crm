"""Сборка клавиатур: главное меню, календарь, слоты, сетка мест, навигация."""

from __future__ import annotations

import calendar as _calendar
from collections.abc import Iterable, Sequence
from datetime import timedelta

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from bot import texts as T
from bot.config import settings
from bot.utils.dates import WEEKDAYS_SHORT, horizon_dates, month_name_nom, today_tz

NOOP = "noop"


# --- CallbackData-фабрики ---
class MenuCB(CallbackData, prefix="menu"):
    action: str  # ключ сценария


class NavCB(CallbackData, prefix="nav"):
    action: str  # back | cancel | home | skip


class CalCB(CallbackData, prefix="cal"):
    action: str  # day | nav
    year: int
    month: int
    day: int


class SlotCB(CallbackData, prefix="slot"):
    # Индекс в списке слотов, показанном пользователю (не само время — двоеточие
    # нельзя класть в callback_data, а подписи слотов зала вида "10:10 - 10:40"
    # и без того не влезли бы в лимит). Список для расшифровки индекса хендлер
    # хранит в данных FSM (см. `slot_options`).
    value: str


class SeatCB(CallbackData, prefix="seat"):
    number: int  # номер аппарата/места


class ChoiceCB(CallbackData, prefix="choice"):
    index: int


class ConfirmCB(CallbackData, prefix="confirm"):
    action: str  # ok | edit


# --- Навигация ---
def _nav_row(*, back: bool = True) -> list[InlineKeyboardButton]:
    row = []
    if back:
        row.append(InlineKeyboardButton(text=T.BTN_BACK, callback_data=NavCB(action="back").pack()))
    row.append(InlineKeyboardButton(text=T.BTN_CANCEL, callback_data=NavCB(action="cancel").pack()))
    return row


def main_menu_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=label, callback_data=MenuCB(action=key).pack())]
        for key, label in T.MENU_ITEMS
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=T.BTN_TO_MENU, callback_data=NavCB(action="home").pack())]
        ]
    )


def step_nav_kb(*, back: bool = True, optional: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if optional:
        rows.append(
            [InlineKeyboardButton(text=T.BTN_SKIP, callback_data=NavCB(action="skip").pack())]
        )
    rows.append(_nav_row(back=back))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def choice_kb(options: Sequence[str], *, optional: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=opt, callback_data=ChoiceCB(index=i).pack())]
        for i, opt in enumerate(options)
    ]
    if optional:
        rows.append(
            [InlineKeyboardButton(text=T.BTN_SKIP, callback_data=NavCB(action="skip").pack())]
        )
    rows.append(_nav_row())
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=T.BTN_CONFIRM, callback_data=ConfirmCB(action="ok").pack())],
            [InlineKeyboardButton(text=T.BTN_EDIT, callback_data=ConfirmCB(action="edit").pack())],
            [InlineKeyboardButton(text=T.BTN_CANCEL, callback_data=NavCB(action="cancel").pack())],
        ]
    )


def contact_kb() -> ReplyKeyboardMarkup:
    """Reply-клавиатура: «Поделиться номером» + текстовые «Назад» / «Отмена»."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=T.BTN_SHARE_PHONE, request_contact=True)],
            [KeyboardButton(text=T.BTN_BACK), KeyboardButton(text=T.BTN_CANCEL)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="+7XXXXXXXXXX",
    )


def emergency_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=T.BTN_SKIP, callback_data=NavCB(action="skip").pack())],
            [InlineKeyboardButton(text=T.BTN_TO_MENU, callback_data=NavCB(action="home").pack())],
        ]
    )


# --- Календарь ---
def build_calendar(year: int, month: int) -> InlineKeyboardMarkup:
    """Месячный календарь. Кликабельны только рабочие дни в пределах горизонта."""
    bookable = set(horizon_dates())
    today = today_tz()
    max_date = today + timedelta(days=settings.booking_horizon_days)

    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text=f"{month_name_nom(month)} {year}", callback_data=NOOP)],
        [InlineKeyboardButton(text=wd, callback_data=NOOP) for wd in WEEKDAYS_SHORT],
    ]

    for week in _calendar.Calendar(firstweekday=0).monthdatescalendar(year, month):
        row: list[InlineKeyboardButton] = []
        for day in week:
            if day.month != month:
                row.append(InlineKeyboardButton(text=" ", callback_data=NOOP))
            elif day in bookable:
                row.append(
                    InlineKeyboardButton(
                        text=str(day.day),
                        callback_data=CalCB(
                            action="day", year=day.year, month=day.month, day=day.day
                        ).pack(),
                    )
                )
            else:
                row.append(InlineKeyboardButton(text="·", callback_data=NOOP))
        rows.append(row)

    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)

    nav: list[InlineKeyboardButton] = []
    if (prev_year, prev_month) >= (today.year, today.month):
        nav.append(
            InlineKeyboardButton(
                text="◀",
                callback_data=CalCB(action="nav", year=prev_year, month=prev_month, day=1).pack(),
            )
        )
    if (next_year, next_month) <= (max_date.year, max_date.month):
        nav.append(
            InlineKeyboardButton(
                text="▶",
                callback_data=CalCB(action="nav", year=next_year, month=next_month, day=1).pack(),
            )
        )
    if nav:
        rows.append(nav)

    rows.append(
        [InlineKeyboardButton(text=T.BTN_CANCEL, callback_data=NavCB(action="cancel").pack())]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


# --- Слоты и аппараты ---
def slots_kb(items: Sequence[tuple[str, int, int]]) -> InlineKeyboardMarkup:
    """`items`: [(подпись слота, свободно, всего), ...], по порядку показа —
    этот же порядок хендлер обязан сохранить в `slot_options`, чтобы расшифровать
    индекс из `SlotCB.value`. Полностью занятые слоты некликабельны."""
    rows: list[list[InlineKeyboardButton]] = []
    for index, (label, free, total) in enumerate(items):
        if free <= 0:
            rows.append([InlineKeyboardButton(text=f"{label} — 🚫 занято", callback_data=NOOP)])
        else:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"{label} — свободно {free} из {total}",
                        callback_data=SlotCB(value=str(index)).pack(),
                    )
                ]
            )
    if not rows:
        rows.append([InlineKeyboardButton(text="Нет свободных слотов", callback_data=NOOP)])
    rows.append(_nav_row())
    return InlineKeyboardMarkup(inline_keyboard=rows)


def apparatus_kb(taken: Iterable[int], total: int) -> InlineKeyboardMarkup:
    """Сетка аппаратов зала. Занятые (по живой таблице) некликабельны."""
    taken_set = set(taken)
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for number in range(1, total + 1):
        if number in taken_set:
            row.append(InlineKeyboardButton(text=f"Аппарат {number} 🚫", callback_data=NOOP))
        else:
            row.append(
                InlineKeyboardButton(
                    text=f"Аппарат {number} ✅", callback_data=SeatCB(number=number).pack()
                )
            )
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append(_nav_row())
    return InlineKeyboardMarkup(inline_keyboard=rows)
