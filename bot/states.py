"""FSM-состояния (aiogram 3.x)."""

from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class MenuSG(StatesGroup):
    home = State()


class GymSG(StatesGroup):
    """Сценарий 1 — нелинейный: дата → время → место → ФИО → телефон → подтверждение."""

    date = State()
    time = State()
    seat = State()
    full_name = State()
    phone = State()
    confirm = State()


class InstructorSG(StatesGroup):
    """Сценарий 2: дата → время → ФИО → телефон → подтверждение."""

    date = State()
    time = State()
    full_name = State()
    phone = State()
    confirm = State()


class GenericFormSG(StatesGroup):
    """Универсальный движок линейных форм (сценарии 3, 4, 6, 7, 8, 9).

    Текущий шаг и накопленные ответы хранятся в данных FSM, а не в отдельных
    состояниях под каждый сценарий.
    """

    step = State()
    confirm = State()


class EmergencySG(StatesGroup):
    description = State()
