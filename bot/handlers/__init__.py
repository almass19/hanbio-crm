"""Реестр роутеров. Порядок подключения важен: `menu` идёт первым, чтобы
`/start` и общая навигация перехватывались всегда.
"""

from __future__ import annotations

from aiogram import Router

# Порядок импорта — от независимых модулей к зависимым (menu импортирует остальные).
from bot.handlers import gym, instructor, emergency, generic_form, menu


def get_routers() -> list[Router]:
    return [
        menu.router,
        emergency.router,
        gym.router,
        instructor.router,
        generic_form.router,
    ]
