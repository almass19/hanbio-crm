"""Декларативные конфиги линейных сценариев (3, 4, 6, 7, 8, 9).

Один универсальный обработчик (:mod:`bot.handlers.generic_form`) прогоняет
любой из этих конфигов — отдельных хендлеров под каждый сценарий нет.

Типы шагов:
    * ``choice``  — выбор из вариантов (inline-кнопки)
    * ``text``    — свободный ввод
    * ``contact`` — «Поделиться номером» + ручной ввод
    * ``date``    — выбор даты из календаря

``show_if`` — шаг показывается, только если ранее данный ответ совпал со всеми
парами из словаря. ``optional=True`` добавляет кнопку «Пропустить».
``validate`` — ``"name"`` прогоняет значение через проверку ФИО.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

StepType = Literal["choice", "text", "contact", "date"]


@dataclass(frozen=True)
class Step:
    id: str
    type: StepType
    question: str
    options: tuple[str, ...] = ()
    show_if: dict[str, str] | None = None
    optional: bool = False
    validate: Literal["name"] | None = None


@dataclass(frozen=True)
class Scenario:
    key: str
    title: str
    steps: tuple[Step, ...] = field(default_factory=tuple)


_NAME_STEP = Step("full_name", "text", "Укажите ваше ФИО (имя и фамилия).", validate="name")
_PHONE_STEP = Step("phone", "contact", "Оставьте номер телефона.")


SCENARIOS: dict[str, Scenario] = {
    # 3. Запись на домашнюю программу
    "home_program": Scenario(
        key="home_program",
        title="Запись на домашнюю программу",
        steps=(
            Step(
                "visit_type",
                "choice",
                "Тип обращения:",
                options=("Первичный выезд", "Повторное обращение"),
            ),
            Step(
                "repeat_reason",
                "text",
                "Укажите причину повторного выезда.",
                show_if={"visit_type": "Повторное обращение"},
            ),
            _NAME_STEP,
            Step("desired_date", "date", "Выберите желаемую дату выезда."),
            _PHONE_STEP,
        ),
    ),
    # 4. Расписать домашнюю программу
    "home_program_plan": Scenario(
        key="home_program_plan",
        title="Расписать домашнюю программу",
        steps=(
            _NAME_STEP,
            _PHONE_STEP,
            Step("comment", "text", "Комментарий (необязательно).", optional=True),
        ),
    ),
    # 6. Покупка расходных материалов
    "consumables": Scenario(
        key="consumables",
        title="Покупка расходных материалов",
        steps=(
            Step(
                "item",
                "choice",
                "Что нужно приобрести?",
                options=("Гель", "Кабель", "Другое"),
            ),
            Step(
                "item_other",
                "text",
                "Уточните, что именно нужно.",
                show_if={"item": "Другое"},
            ),
            _NAME_STEP,
            _PHONE_STEP,
        ),
    ),
    # 7. Техосмотр оборудования
    "inspection": Scenario(
        key="inspection",
        title="Техосмотр оборудования",
        steps=(
            _NAME_STEP,
            _PHONE_STEP,
            Step("comment", "text", "Комментарий (необязательно).", optional=True),
        ),
    ),
    # 8. Вопросы по договору
    "contract": Scenario(
        key="contract",
        title="Вопросы по договору",
        steps=(
            Step(
                "topic",
                "choice",
                "Выберите вопрос:",
                options=(
                    "Расторжение договора",
                    "Докупить количество занятий",
                    "Другое",
                ),
            ),
            Step(
                "topic_other",
                "text",
                "Уточните ваш вопрос.",
                show_if={"topic": "Другое"},
            ),
            _NAME_STEP,
            _PHONE_STEP,
        ),
    ),
    # 9. Другое
    "other": Scenario(
        key="other",
        title="Другое обращение",
        steps=(
            Step("message", "text", "Опишите ваше обращение."),
            _NAME_STEP,
            _PHONE_STEP,
        ),
    ),
}

GENERIC_KEYS: frozenset[str] = frozenset(SCENARIOS)
