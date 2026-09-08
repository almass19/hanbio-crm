"""`/start`, главное меню и общая навигация (Отмена / В главное меню)."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from bot import texts as T
from bot.db import repo
from bot.handlers import emergency, generic_form, gym, instructor
from bot.handlers.common import go_home
from bot.keyboards import NOOP, MenuCB, NavCB, main_menu_kb
from bot.scenarios import GENERIC_KEYS
from bot.states import MenuSG

router = Router(name="menu")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, sessionmaker) -> None:
    """`/start` в любой момент сбрасывает FSM и показывает меню."""
    await state.clear()
    async with sessionmaker() as session:
        await repo.get_or_create_user(session, message.from_user)
        await session.commit()
    await message.answer(T.GREETING, reply_markup=ReplyKeyboardRemove())
    await state.set_state(MenuSG.home)
    await message.answer(T.MENU_TITLE, reply_markup=main_menu_kb())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await go_home(message, state)


@router.callback_query(NavCB.filter(F.action.in_({"cancel", "home"})))
async def nav_home(cb: CallbackQuery, state: FSMContext) -> None:
    await go_home(cb, state)
    await cb.answer()


@router.callback_query(F.data == NOOP)
async def noop(cb: CallbackQuery) -> None:
    await cb.answer()


@router.callback_query(MenuCB.filter())
async def menu_pick(
    cb: CallbackQuery, callback_data: MenuCB, state: FSMContext, sessionmaker, bot
) -> None:
    key = callback_data.action
    if key == "gym":
        await gym.start(cb, state)
    elif key == "instructor":
        await instructor.start(cb, state)
    elif key == "emergency":
        await emergency.start(cb, state, sessionmaker, bot)
    elif key in GENERIC_KEYS:
        await generic_form.start_scenario(cb, state, key)
    else:
        await cb.answer("Неизвестный пункт меню", show_alert=True)
        return
    await cb.answer()
