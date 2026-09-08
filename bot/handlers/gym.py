"""Сценарий 1 — запись в общий зал (единственный нелинейный).

Флоу: дата → время → аппарат → ФИО → телефон → подтверждение.

Занятость проверяется по живой Google-таблице расписания клиники
(`bot.services.gym_sheet`) — она источник истины, не БД. Финальная запись
делается под локом на дату и с повторной проверкой ячейки прямо перед записью,
поэтому два одновременных подтверждения на один аппарат не могут оба пройти:
второму придёт «Аппарат уже занят» и он вернётся к выбору аппарата.
"""

from __future__ import annotations

import logging
from datetime import date

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from bot import texts as T
from bot.config import settings
from bot.db import repo
from bot.handlers.common import Event, go_home, render
from bot.keyboards import (
    CalCB,
    ConfirmCB,
    SeatCB,
    SlotCB,
    apparatus_kb,
    build_calendar,
    confirm_kb,
    contact_kb,
    slots_kb,
    step_nav_kb,
    to_menu_kb,
)
from bot.services import notify
from bot.services.gym_sheet import gym_schedule, session_slots_for_date
from bot.states import GymSG
from bot.utils.dates import format_date, is_bookable_date, today_tz
from bot.utils.validators import normalize_phone, validate_full_name

log = logging.getLogger(__name__)
router = Router(name="gym")


async def start(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(GymSG.date)
    await state.set_data({})
    today = today_tz()
    await render(cb, T.GYM_PICK_DATE, build_calendar(today.year, today.month), edit=True)


# --- Дата ---
@router.callback_query(GymSG.date, CalCB.filter(F.action == "nav"))
async def pick_month(cb: CallbackQuery, callback_data: CalCB, state: FSMContext) -> None:
    if cb.message is not None:
        await cb.message.edit_reply_markup(
            reply_markup=build_calendar(callback_data.year, callback_data.month)
        )
    await cb.answer()


@router.callback_query(GymSG.date, CalCB.filter(F.action == "day"))
async def pick_date(cb: CallbackQuery, callback_data: CalCB, state: FSMContext) -> None:
    picked = date(callback_data.year, callback_data.month, callback_data.day)
    if not is_bookable_date(picked):
        await cb.answer(T.DATE_UNAVAILABLE, show_alert=True)
        return
    await state.update_data(session_date=picked.isoformat())
    await state.set_state(GymSG.time)
    await _show_slots(cb, state)
    await cb.answer()


async def _unavailable(event: Event, state: FSMContext) -> None:
    await state.clear()
    await render(event, T.GYM_UNAVAILABLE, to_menu_kb(), edit=isinstance(event, CallbackQuery))


async def _show_slots(event: Event, state: FSMContext) -> None:
    day = date.fromisoformat((await state.get_data())["session_date"])
    labels = session_slots_for_date(day)

    if not gym_schedule.enabled:
        await _unavailable(event, state)
        return
    try:
        loads = await gym_schedule.slot_loads(day, labels, settings.gym_apparatus_count)
    except Exception:
        log.exception("не удалось прочитать таблицу расписания зала")
        await _unavailable(event, state)
        return

    await state.update_data(slot_options=labels)
    items = [(label, *loads[label]) for label in labels]
    await render(
        event,
        T.GYM_PICK_TIME.format(date=format_date(day)),
        slots_kb(items),
        edit=isinstance(event, CallbackQuery),
    )


# --- Время ---
@router.callback_query(GymSG.time, SlotCB.filter())
async def pick_slot(cb: CallbackQuery, callback_data: SlotCB, state: FSMContext) -> None:
    data = await state.get_data()
    slot_label = data["slot_options"][int(callback_data.value)]
    await state.update_data(session_time=slot_label)
    await state.set_state(GymSG.seat)
    await _show_seats(cb, state)
    await cb.answer()


async def _show_seats(event: Event, state: FSMContext) -> None:
    data = await state.get_data()
    day = date.fromisoformat(data["session_date"])
    slot_label = data["session_time"]

    try:
        free = await gym_schedule.free_apparatuses(day, slot_label, settings.gym_apparatus_count)
    except Exception:
        log.exception("не удалось прочитать таблицу расписания зала")
        await _unavailable(event, state)
        return

    taken = set(range(1, settings.gym_apparatus_count + 1)) - free
    await render(
        event,
        T.GYM_PICK_SEAT.format(date=format_date(day), time=slot_label),
        apparatus_kb(taken, settings.gym_apparatus_count),
        edit=isinstance(event, CallbackQuery),
    )


# --- Аппарат ---
@router.callback_query(GymSG.seat, SeatCB.filter())
async def pick_seat(cb: CallbackQuery, callback_data: SeatCB, state: FSMContext) -> None:
    data = await state.get_data()
    day = date.fromisoformat(data["session_date"])
    slot_label = data["session_time"]

    try:
        free = await gym_schedule.free_apparatuses(day, slot_label, settings.gym_apparatus_count)
    except Exception:
        log.exception("не удалось прочитать таблицу расписания зала")
        await _unavailable(cb, state)
        return

    if callback_data.number not in free:
        await cb.answer(T.SEAT_TAKEN_RETRY, show_alert=True)
        await _show_seats(cb, state)
        return

    await state.update_data(seat_number=callback_data.number)
    await state.set_state(GymSG.full_name)
    await render(cb, T.ASK_FULL_NAME, step_nav_kb(), edit=True)
    await cb.answer()


# --- ФИО ---
@router.message(GymSG.full_name, F.text)
async def set_name(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text == T.BTN_CANCEL:
        await go_home(message, state)
        return
    name = validate_full_name(text)
    if name is None:
        await message.answer(T.BAD_FULL_NAME, reply_markup=step_nav_kb())
        return
    await state.update_data(full_name=name)
    await state.set_state(GymSG.phone)
    await message.answer(T.ASK_PHONE, reply_markup=contact_kb())


# --- Телефон ---
@router.message(GymSG.phone, F.contact)
async def set_phone_contact(message: Message, state: FSMContext) -> None:
    phone = normalize_phone(message.contact.phone_number)
    if phone is None:
        await message.answer(T.BAD_PHONE, reply_markup=contact_kb())
        return
    await _to_confirm(message, state, phone)


@router.message(GymSG.phone, F.text)
async def set_phone_text(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text == T.BTN_CANCEL:
        await go_home(message, state)
        return
    if text == T.BTN_BACK:
        await state.set_state(GymSG.full_name)
        await message.answer("↩️", reply_markup=ReplyKeyboardRemove())
        await message.answer(T.ASK_FULL_NAME, reply_markup=step_nav_kb())
        return
    phone = normalize_phone(text)
    if phone is None:
        await message.answer(T.BAD_PHONE, reply_markup=contact_kb())
        return
    await _to_confirm(message, state, phone)


async def _to_confirm(message: Message, state: FSMContext, phone: str) -> None:
    await state.update_data(phone=phone)
    await state.set_state(GymSG.confirm)
    data = await state.get_data()
    day = date.fromisoformat(data["session_date"])
    summary = (
        f"{T.GYM_CONFIRM_TITLE}\n\n"
        f"• Дата: <b>{format_date(day)}</b>\n"
        f"• Время: <b>{data['session_time']}</b>\n"
        f"• Аппарат: <b>{data['seat_number']}</b>\n"
        f"• ФИО: <b>{data['full_name']}</b>\n"
        f"• Телефон: <b>{phone}</b>"
    )
    await message.answer(T.PHONE_SAVED, reply_markup=ReplyKeyboardRemove())
    await message.answer(summary, reply_markup=confirm_kb())


# --- Подтверждение ---
@router.callback_query(GymSG.confirm, ConfirmCB.filter(F.action == "edit"))
async def edit(cb: CallbackQuery, state: FSMContext) -> None:
    await start(cb, state)
    await cb.answer()


@router.callback_query(GymSG.confirm, ConfirmCB.filter(F.action == "ok"))
async def confirm(cb: CallbackQuery, state: FSMContext, sessionmaker, bot) -> None:
    data = await state.get_data()
    day = date.fromisoformat(data["session_date"])
    slot_label = data["session_time"]
    apparatus = data["seat_number"]
    full_name = data["full_name"]
    phone = data["phone"]

    try:
        booked = await gym_schedule.book(day, slot_label, apparatus, full_name)
    except Exception:
        log.exception("не удалось записать в таблицу расписания зала")
        await cb.answer(T.GYM_UNAVAILABLE, show_alert=True)
        return

    if not booked:
        await cb.answer(T.SEAT_TAKEN_RETRY, show_alert=True)
        await state.set_state(GymSG.seat)
        await _show_seats(cb, state)
        return

    # Таблица — источник истины и уже обновлена; БД — необязательное зеркало
    # для истории/уведомлений, его сбой не должен откатывать успешную запись.
    booking_id: int | None = None
    try:
        async with sessionmaker() as session:
            async with session.begin():
                user = await repo.get_or_create_user(session, cb.from_user)
                user.phone = phone
                booking = await repo.create_gym_booking(
                    session,
                    user_id=user.id,
                    day=day,
                    slot_time=slot_label,
                    seat_number=apparatus,
                    full_name=full_name,
                    phone=phone,
                )
                await session.flush()
                booking_id = booking.id
    except Exception:
        log.exception("запись в таблицу прошла, но зеркало в БД не сохранилось")

    await notify.notify_admins(
        bot, notify.format_gym(full_name, phone, day, slot_label, apparatus, cb.from_user)
    )
    await state.clear()
    id_text = str(booking_id) if booking_id is not None else "—"
    await render(cb, T.GYM_DONE.format(id=id_text), to_menu_kb(), edit=True)
    await cb.answer()
