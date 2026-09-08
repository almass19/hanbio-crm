"""Общие помощники хендлеров: рендер сообщений и возврат в меню.

Не импортирует другие модули из ``bot.handlers`` — чтобы не создавать циклы.
"""

from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.fsm.context import FSMContext

from bot import texts as T
from bot.keyboards import main_menu_kb
from bot.states import MenuSG

Event = CallbackQuery | Message


async def render(
    event: Event,
    text: str,
    markup: InlineKeyboardMarkup | None = None,
    *,
    edit: bool = True,
) -> None:
    """Показать текст: отредактировать сообщение (для callback) либо отправить новое."""
    if isinstance(event, CallbackQuery):
        if edit and event.message is not None:
            try:
                await event.message.edit_text(text, reply_markup=markup)
                return
            except TelegramBadRequest:
                pass
        if event.message is not None:
            await event.message.answer(text, reply_markup=markup)
        return
    await event.answer(text, reply_markup=markup)


async def send_fresh(event: Event, text: str, markup=None) -> None:
    """Всегда отправить новое сообщение (нужно для reply-клавиатур)."""
    target = event.message if isinstance(event, CallbackQuery) else event
    if target is not None:
        await target.answer(text, reply_markup=markup)


async def go_home(event: Event, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(MenuSG.home)
    await render(event, T.MENU_TITLE, main_menu_kb(), edit=isinstance(event, CallbackQuery))
