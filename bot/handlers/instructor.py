"""Сценарий 2 — запись к инструктору.

Флоу: дата → время → ФИО → телефон → подтверждение.
Слоты — та же сеансовая сетка клиники, что и у зала (`gym_sheet.GYM_SLOTS`,
диапазоны вида "10:10 - 10:40"), но без выбора аппарата; лимит записей на слот —
`INSTRUCTOR_SLOTS_PER_HOUR` (макс. записей на один сеанс).
"""

from __future__ import annotations

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
    SlotCB,
    build_calendar,
    confirm_kb,
    contact_kb,
    slots_kb,
    step_nav_kb,
    to_menu_kb,
)
from bot.services import notify
from bot.services.gym_sheet import session_slots_for_date
from bot.states import InstructorSG
from bot.utils.dates import format_date, format_dt, is_bookable_date, now_tz, today_tz
from bot.utils.validators import normalize_phone, validate_full_name

router = Router(name="instructor")


async def start(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(InstructorSG.date)
    await state.set_data({})
    today = today_tz()
    await render(cb, T.INSTRUCTOR_PICK_DATE, build_calendar(today.year, today.month), edit=True)


@router.callback_query(InstructorSG.date, CalCB.filter(F.action == "nav"))
async def pick_month(cb: CallbackQuery, callback_data: CalCB, state: FSMContext) -> None:
    if cb.message is not None:
        await cb.message.edit_reply_markup(
            reply_markup=build_calendar(callback_data.year, callback_data.month)
        )
    await cb.answer()


@router.callback_query(InstructorSG.date, CalCB.filter(F.action == "day"))
async def pick_date(
    cb: CallbackQuery, callback_data: CalCB, state: FSMContext, sessionmaker
) -> None:
    picked = date(callback_data.year, callback_data.month, callback_data.day)
    if not is_bookable_date(picked):
        await cb.answer(T.DATE_UNAVAILABLE, show_alert=True)
        return
    await state.update_data(session_date=picked.isoformat())
    await state.set_state(InstructorSG.time)
    await _show_slots(cb, state, sessionmaker)
    await cb.answer()


async def _show_slots(event: Event, state: FSMContext, sessionmaker) -> None:
    day = date.fromisoformat((await state.get_data())["session_date"])
    times = session_slots_for_date(day)
    async with sessionmaker() as session:
        loads = await repo.instructor_slot_loads(
            session, day, times, settings.instructor_slots_per_hour
        )
    await state.update_data(slot_options=times)
    items = [(t, *loads[t]) for t in times]
    await render(
        event,
        T.INSTRUCTOR_PICK_TIME.format(date=format_date(day)),
        slots_kb(items),
        edit=isinstance(event, CallbackQuery),
    )


@router.callback_query(InstructorSG.time, SlotCB.filter())
async def pick_slot(cb: CallbackQuery, callback_data: SlotCB, state: FSMContext) -> None:
    data = await state.get_data()
    session_time = data["slot_options"][int(callback_data.value)]
    await state.update_data(session_time=session_time)
    await state.set_state(InstructorSG.full_name)
    await render(cb, T.ASK_FULL_NAME, step_nav_kb(), edit=True)
    await cb.answer()


@router.message(InstructorSG.full_name, F.text)
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
    await state.set_state(InstructorSG.phone)
    await message.answer(T.ASK_PHONE, reply_markup=contact_kb())


@router.message(InstructorSG.phone, F.contact)
async def set_phone_contact(message: Message, state: FSMContext) -> None:
    phone = normalize_phone(message.contact.phone_number)
    if phone is None:
        await message.answer(T.BAD_PHONE, reply_markup=contact_kb())
        return
    await _to_confirm(message, state, phone)


@router.message(InstructorSG.phone, F.text)
async def set_phone_text(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text == T.BTN_CANCEL:
        await go_home(message, state)
        return
    if text == T.BTN_BACK:
        await state.set_state(InstructorSG.full_name)
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
    await state.set_state(InstructorSG.confirm)
    data = await state.get_data()
    day = date.fromisoformat(data["session_date"])
    summary = (
        f"{T.INSTRUCTOR_CONFIRM_TITLE}\n\n"
        f"• Дата: <b>{format_date(day)}</b>\n"
        f"• Время: <b>{data['session_time']}</b>\n"
        f"• ФИО: <b>{data['full_name']}</b>\n"
        f"• Телефон: <b>{phone}</b>"
    )
    await message.answer(T.PHONE_SAVED, reply_markup=ReplyKeyboardRemove())
    await message.answer(summary, reply_markup=confirm_kb())


@router.callback_query(InstructorSG.confirm, ConfirmCB.filter(F.action == "edit"))
async def edit(cb: CallbackQuery, state: FSMContext) -> None:
    await start(cb, state)
    await cb.answer()


@router.callback_query(InstructorSG.confirm, ConfirmCB.filter(F.action == "ok"))
async def confirm(cb: CallbackQuery, state: FSMContext, sessionmaker, bot) -> None:
    data = await state.get_data()
    day = date.fromisoformat(data["session_date"])
    slot_time = data["session_time"]
    full_name = data["full_name"]
    phone = data["phone"]

    try:
        async with sessionmaker() as session:
            async with session.begin():
                user = await repo.get_or_create_user(session, cb.from_user)
                user.phone = phone
                booking = await repo.create_instructor_booking(
                    session,
                    user_id=user.id,
                    day=day,
                    slot_time=slot_time,
                    capacity=settings.instructor_slots_per_hour,
                    full_name=full_name,
                    phone=phone,
                )
                await session.flush()
                booking_id = booking.id
                await repo.enqueue_sheet_row(
                    session,
                    T.SHEET_REQUESTS,
                    [
                        format_dt(now_tz()),
                        "Запись к инструктору",
                        cb.from_user.id,
                        cb.from_user.username or "",
                        full_name,
                        phone,
                        f"Дата: {format_date(day)}; Время: {slot_time}",
                        "new",
                    ],
                )
    except repo.SlotFullError:
        await cb.answer(T.INSTRUCTOR_SLOT_FULL, show_alert=True)
        await state.set_state(InstructorSG.time)
        await _show_slots(cb, state, sessionmaker)
        return

    await notify.notify_admins(
        bot, notify.format_instructor(full_name, phone, day, slot_time, cb.from_user)
    )
    await state.clear()
    await render(cb, T.INSTRUCTOR_DONE.format(id=booking_id), to_menu_kb(), edit=True)
    await cb.answer()
