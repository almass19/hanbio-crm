"""Уведомления администраторам о новых заявках и записях."""

from __future__ import annotations

import html
import logging
from datetime import date

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bot.config import settings
from bot.utils.dates import format_date

log = logging.getLogger(__name__)


async def notify_admins(bot: Bot, text: str) -> None:
    """Разослать сообщение всем `ADMIN_CHAT_IDS`. Ошибки не пробрасываются."""
    for chat_id in settings.admin_chat_ids:
        try:
            await bot.send_message(chat_id, text, disable_web_page_preview=True)
        except TelegramAPIError:
            log.exception("не удалось уведомить админа %s", chat_id)


def _e(value: object) -> str:
    return html.escape(str(value if value is not None else "—"))


def _user_line(tg_user) -> str:
    name = _e(getattr(tg_user, "full_name", None) or tg_user.id)
    handle = f"@{tg_user.username}" if getattr(tg_user, "username", None) else "—"
    return f'<a href="tg://user?id={tg_user.id}">{name}</a> ({_e(handle)})'


def format_request(
    title: str, full_name: str, phone: str, details: str, tg_user
) -> str:
    return (
        "🆕 <b>Новая заявка</b>\n"
        f"Тип: {_e(title)}\n"
        f"ФИО: {_e(full_name)}\n"
        f"Телефон: {_e(phone)}\n"
        f"Детали: {_e(details) or '—'}\n"
        f"Пользователь: {_user_line(tg_user)}"
    )


def format_gym(full_name: str, phone: str, day: date, slot_time: str, seat: int, tg_user) -> str:
    return (
        "🏟️ <b>Новая запись в общий зал</b>\n"
        f"Когда: {format_date(day)}, {_e(slot_time)}\n"
        f"Место: {seat}\n"
        f"ФИО: {_e(full_name)}\n"
        f"Телефон: {_e(phone)}\n"
        f"Пользователь: {_user_line(tg_user)}"
    )


def format_instructor(full_name: str, phone: str, day: date, slot_time: str, tg_user) -> str:
    return (
        "🧑‍🏫 <b>Новая запись к инструктору</b>\n"
        f"Когда: {format_date(day)}, {_e(slot_time)}\n"
        f"ФИО: {_e(full_name)}\n"
        f"Телефон: {_e(phone)}\n"
        f"Пользователь: {_user_line(tg_user)}"
    )


def format_emergency(tg_user, phone: str | None, description: str | None) -> str:
    lines = [
        "🔴 <b>СРОЧНО — РЕАКЦИЯ ОБОСТРЕНИЯ</b>",
        f"Пользователь: {_user_line(tg_user)}",
        f"Телефон: {_e(phone)}",
    ]
    lines.append(
        f"Состояние: {_e(description)}" if description else "Состояние: (пока не описано)"
    )
    return "\n".join(lines)
