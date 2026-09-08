"""Сценарий 5 — реакция обострения. Это не форма, а медицинская срочность.

Порядок:
1. Сразу показать контакт дежурного администратора и кликабельный `tel:`-номер.
2. Немедленно (до записи в БД) разослать `ADMIN_CHAT_IDS` яркое уведомление.
3. Предложить необязательно описать состояние; описание уходит админам вторым
   сообщением, затем заявка фиксируется в БД (для критерия «все сценарии пишут в БД»).
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts as T
from bot.config import settings
from bot.db import repo
from bot.handlers.common import go_home, render
from bot.keyboards import NavCB, emergency_kb, to_menu_kb
from bot.services import notify
from bot.states import EmergencySG
from bot.utils.dates import format_dt, now_tz

router = Router(name="emergency")


async def start(cb: CallbackQuery, state: FSMContext, sessionmaker, bot) -> None:
    async with sessionmaker() as session:
        user = await repo.get_or_create_user(session, cb.from_user)
        await session.commit()
        known_phone = user.phone

    # Уведомление админам — первым делом, до любых форм и записей.
    await notify.notify_admins(
        bot, notify.format_emergency(cb.from_user, known_phone, description=None)
    )

    await state.set_state(EmergencySG.description)
    await state.set_data({"known_phone": known_phone or ""})
    await render(
        cb,
        T.EMERGENCY_INTRO.format(phone=settings.emergency_phone),
        emergency_kb(),
        edit=True,
    )
    await cb.answer()


async def _persist(session_factory, tg_user, description: str) -> int:
    async with session_factory() as session:
        async with session.begin():
            user = await repo.get_or_create_user(session, tg_user)
            request = await repo.create_request(
                session,
                user_id=user.id,
                scenario_key="emergency",
                payload={"description": description},
                full_name=user.first_name or "—",
                phone=user.phone or "—",
            )
            await session.flush()
            request_id = request.id
            await repo.enqueue_sheet_row(
                session,
                T.SHEET_REQUESTS,
                [
                    format_dt(now_tz()),
                    T.MENU_EMERGENCY_TITLE,
                    tg_user.id,
                    tg_user.username or "",
                    user.first_name or "",
                    user.phone or "",
                    description or "(без описания)",
                    "new",
                ],
            )
    return request_id


@router.message(EmergencySG.description, F.text)
async def describe(message: Message, state: FSMContext, sessionmaker, bot) -> None:
    text = message.text.strip()
    if text in {T.BTN_CANCEL, T.BTN_TO_MENU}:
        await go_home(message, state)
        return

    data = await state.get_data()
    await notify.notify_admins(
        bot,
        notify.format_emergency(message.from_user, data.get("known_phone"), description=text),
    )
    request_id = await _persist(sessionmaker, message.from_user, text)
    await state.clear()
    await message.answer(T.EMERGENCY_DONE.format(id=request_id), reply_markup=to_menu_kb())


@router.callback_query(EmergencySG.description, NavCB.filter(F.action == "skip"))
async def skip(cb: CallbackQuery, state: FSMContext, sessionmaker) -> None:
    await _persist(sessionmaker, cb.from_user, "")
    await state.clear()
    await render(cb, T.EMERGENCY_DONE_NO_TEXT, to_menu_kb(), edit=True)
    await cb.answer()
