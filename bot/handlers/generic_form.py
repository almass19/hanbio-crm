"""Универсальный движок линейных форм (сценарии 3, 4, 6, 7, 8, 9).

Читает конфиг из :mod:`bot.scenarios` и прогоняет пользователя по шагам.
Отдельных хендлеров под каждый сценарий нет.
"""

from __future__ import annotations

import logging
from datetime import date

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from bot import texts as T
from bot.db import repo
from bot.handlers.common import Event, go_home, render, send_fresh
from bot.keyboards import (
    CalCB,
    ChoiceCB,
    ConfirmCB,
    NavCB,
    build_calendar,
    choice_kb,
    confirm_kb,
    contact_kb,
    step_nav_kb,
    to_menu_kb,
)
from bot.scenarios import SCENARIOS, Scenario, Step
from bot.services import notify
from bot.states import GenericFormSG
from bot.utils.dates import format_date, format_dt, is_bookable_date, now_tz, today_tz
from bot.utils.validators import normalize_phone, validate_full_name

log = logging.getLogger(__name__)
router = Router(name="generic_form")


# --- Навигация по конфигу ---
def _visible(step: Step, answers: dict) -> bool:
    if not step.show_if:
        return True
    return all(answers.get(key) == value for key, value in step.show_if.items())


def _forward_index(scenario: Scenario, answers: dict, start: int) -> int:
    index = start
    while index < len(scenario.steps) and not _visible(scenario.steps[index], answers):
        index += 1
    return index


def _back_index(scenario: Scenario, answers: dict, start: int) -> int:
    index = start - 1
    while index >= 0 and not _visible(scenario.steps[index], answers):
        index -= 1
    return index


def _current(data: dict) -> tuple[Scenario, Step]:
    scenario = SCENARIOS[data["scenario_key"]]
    return scenario, scenario.steps[data["step_index"]]


# --- Точка входа ---
async def start_scenario(event: Event, state: FSMContext, key: str) -> None:
    scenario = SCENARIOS[key]
    await state.set_state(GenericFormSG.step)
    await state.set_data(
        {"scenario_key": key, "answers": {}, "step_index": _forward_index(scenario, {}, 0)}
    )
    await _ask(event, state, edit=True)


async def _ask(event: Event, state: FSMContext, *, edit: bool) -> None:
    data = await state.get_data()
    scenario = SCENARIOS[data["scenario_key"]]
    answers = data["answers"]

    index = _forward_index(scenario, answers, data["step_index"])
    await state.update_data(step_index=index)

    if index >= len(scenario.steps):
        await _show_confirm(event, state)
        return

    step = scenario.steps[index]
    text = f"<b>{scenario.title}</b>\n\n{step.question}"

    if step.type == "choice":
        await render(event, text, choice_kb(step.options, optional=step.optional), edit=edit)
    elif step.type == "date":
        today = today_tz()
        await render(event, text, build_calendar(today.year, today.month), edit=edit)
    elif step.type == "contact":
        await send_fresh(event, text, contact_kb())
    else:  # text
        await render(event, text, step_nav_kb(optional=step.optional), edit=edit)


async def _store_and_advance(
    event: Event, state: FSMContext, step: Step, value: str, *, drop_reply_kb: bool = False
) -> None:
    data = await state.get_data()
    answers = dict(data["answers"])
    answers[step.id] = value
    await state.update_data(answers=answers, step_index=data["step_index"] + 1)
    if drop_reply_kb:
        await send_fresh(event, T.PHONE_SAVED, ReplyKeyboardRemove())
    await _ask(event, state, edit=False)


async def _go_back(event: Event, state: FSMContext) -> None:
    data = await state.get_data()
    scenario = SCENARIOS[data["scenario_key"]]
    prev = _back_index(scenario, data["answers"], data["step_index"])
    if prev < 0:
        await go_home(event, state)
        return
    answers = dict(data["answers"])
    answers.pop(scenario.steps[prev].id, None)
    await state.update_data(answers=answers, step_index=prev)
    await _ask(event, state, edit=isinstance(event, CallbackQuery))


# --- Callback-шаги ---
@router.callback_query(GenericFormSG.step, ChoiceCB.filter())
async def on_choice(cb: CallbackQuery, callback_data: ChoiceCB, state: FSMContext) -> None:
    _, step = _current(await state.get_data())
    if step.type != "choice":
        await cb.answer()
        return
    await _store_and_advance(cb, state, step, step.options[callback_data.index])
    await cb.answer()


@router.callback_query(GenericFormSG.step, CalCB.filter(F.action == "nav"))
async def on_calendar_nav(cb: CallbackQuery, callback_data: CalCB, state: FSMContext) -> None:
    if cb.message is not None:
        await cb.message.edit_reply_markup(
            reply_markup=build_calendar(callback_data.year, callback_data.month)
        )
    await cb.answer()


@router.callback_query(GenericFormSG.step, CalCB.filter(F.action == "day"))
async def on_calendar_day(cb: CallbackQuery, callback_data: CalCB, state: FSMContext) -> None:
    picked = date(callback_data.year, callback_data.month, callback_data.day)
    if not is_bookable_date(picked):
        await cb.answer(T.DATE_UNAVAILABLE, show_alert=True)
        return
    _, step = _current(await state.get_data())
    await _store_and_advance(cb, state, step, picked.isoformat())
    await cb.answer()


@router.callback_query(GenericFormSG.step, NavCB.filter(F.action == "skip"))
async def on_skip(cb: CallbackQuery, state: FSMContext) -> None:
    _, step = _current(await state.get_data())
    if not step.optional:
        await cb.answer()
        return
    await _store_and_advance(cb, state, step, "")
    await cb.answer()


@router.callback_query(GenericFormSG.step, NavCB.filter(F.action == "back"))
async def on_back(cb: CallbackQuery, state: FSMContext) -> None:
    await _go_back(cb, state)
    await cb.answer()


# --- Сообщения (text / contact) ---
@router.message(GenericFormSG.step, F.contact)
async def on_contact(message: Message, state: FSMContext) -> None:
    _, step = _current(await state.get_data())
    if step.type != "contact":
        return
    phone = normalize_phone(message.contact.phone_number)
    if phone is None:
        await message.answer(T.BAD_PHONE, reply_markup=contact_kb())
        return
    await _store_and_advance(message, state, step, phone, drop_reply_kb=True)


@router.message(GenericFormSG.step, F.text)
async def on_text(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text == T.BTN_CANCEL:
        await go_home(message, state)
        return
    if text == T.BTN_BACK:
        await _go_back(message, state)
        return

    _, step = _current(await state.get_data())

    if step.type == "contact":
        phone = normalize_phone(text)
        if phone is None:
            await message.answer(T.BAD_PHONE, reply_markup=contact_kb())
            return
        await _store_and_advance(message, state, step, phone, drop_reply_kb=True)
        return

    if step.type == "text":
        value = text
        if step.validate == "name":
            cleaned = validate_full_name(text)
            if cleaned is None:
                await message.answer(
                    T.BAD_FULL_NAME, reply_markup=step_nav_kb(optional=step.optional)
                )
                return
            value = cleaned
        await _store_and_advance(message, state, step, value)
        return

    await message.answer(T.USE_BUTTONS)


# --- Подтверждение и отправка ---
def _answer_display(step: Step, raw: str) -> str:
    if raw == "":
        return "—"
    if step.type == "date":
        return format_date(date.fromisoformat(raw))
    return raw


def _format_details(scenario: Scenario, answers: dict) -> str:
    parts: list[str] = []
    for step in scenario.steps:
        if step.id in {"full_name", "phone"} or not _visible(step, answers):
            continue
        raw = answers.get(step.id, "")
        if raw == "":
            continue
        parts.append(f"{step.question} {_answer_display(step, raw)}")
    return "; ".join(parts)


async def _show_confirm(event: Event, state: FSMContext) -> None:
    data = await state.get_data()
    scenario = SCENARIOS[data["scenario_key"]]
    answers = data["answers"]

    lines = [
        f"• {step.question}\n  <b>{_answer_display(step, answers.get(step.id, ''))}</b>"
        for step in scenario.steps
        if _visible(step, answers)
    ]
    text = T.CONFIRM_TITLE.format(title=scenario.title) + "\n\n" + "\n".join(lines)

    await state.set_state(GenericFormSG.confirm)
    await render(event, text, confirm_kb(), edit=isinstance(event, CallbackQuery))


@router.callback_query(GenericFormSG.confirm, ConfirmCB.filter(F.action == "edit"))
async def on_edit(cb: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await start_scenario(cb, state, data["scenario_key"])
    await cb.answer()


@router.callback_query(GenericFormSG.confirm, ConfirmCB.filter(F.action == "ok"))
async def on_submit(cb: CallbackQuery, state: FSMContext, sessionmaker, bot) -> None:
    data = await state.get_data()
    scenario = SCENARIOS[data["scenario_key"]]
    answers = data["answers"]

    full_name = answers.get("full_name") or "—"
    phone = answers.get("phone") or "—"
    details = _format_details(scenario, answers)

    async with sessionmaker() as session:
        async with session.begin():
            user = await repo.get_or_create_user(session, cb.from_user)
            if phone.startswith("+"):
                user.phone = phone
            request = await repo.create_request(
                session,
                user_id=user.id,
                scenario_key=scenario.key,
                payload=answers,
                full_name=full_name,
                phone=phone,
            )
            await session.flush()
            request_id = request.id
            await repo.enqueue_sheet_row(
                session,
                T.SHEET_REQUESTS,
                [
                    format_dt(now_tz()),
                    scenario.title,
                    cb.from_user.id,
                    cb.from_user.username or "",
                    full_name,
                    phone,
                    details,
                    "new",
                ],
            )

    await notify.notify_admins(
        bot, notify.format_request(scenario.title, full_name, phone, details, cb.from_user)
    )
    await state.clear()
    await render(cb, T.REQUEST_DONE.format(id=request_id), to_menu_kb(), edit=True)
    await cb.answer()
