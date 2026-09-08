"""Слой доступа к данным. Функции не знают про aiogram и не коммитят —
транзакцией управляет вызывающий код.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import (
    GymBooking,
    InstructorBooking,
    Request,
    SheetSyncQueue,
    User,
)


class SlotFullError(RuntimeError):
    """Слот к инструктору заполнен (проверка внутри транзакции)."""


async def get_or_create_user(session: AsyncSession, tg_user) -> User:
    """Найти пользователя по telegram_id или создать; освежить username/first_name."""
    user = (
        await session.execute(select(User).where(User.telegram_id == tg_user.id))
    ).scalar_one_or_none()

    if user is None:
        user = User(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
        )
        session.add(user)
        await session.flush()
        return user

    if (user.username, user.first_name) != (tg_user.username, tg_user.first_name):
        user.username = tg_user.username
        user.first_name = tg_user.first_name
    return user


# --- Заявки (линейные сценарии + сценарий 5) ---
async def create_request(
    session: AsyncSession,
    *,
    user_id: int,
    scenario_key: str,
    payload: dict,
    full_name: str | None,
    phone: str | None,
) -> Request:
    request = Request(
        user_id=user_id,
        scenario_key=scenario_key,
        payload=payload,
        full_name=full_name,
        phone=phone,
        status="new",
    )
    session.add(request)
    return request


# --- Общий зал ---
# Занятость проверяется по живой Google-таблице (bot.services.gym_sheet), не по
# БД — администратор может вписать клиента в ячейку мимо бота. create_gym_booking
# только зеркалирует уже подтверждённую (таблицей) бронь для истории/уведомлений.
async def create_gym_booking(
    session: AsyncSession,
    *,
    user_id: int,
    day: date,
    slot_time: str,
    seat_number: int,
    full_name: str,
    phone: str,
) -> GymBooking:
    """Добавить бронь в сессию. `IntegrityError` на flush — если место заняли."""
    booking = GymBooking(
        user_id=user_id,
        session_date=day,
        session_time=slot_time,
        seat_number=seat_number,
        full_name=full_name,
        phone=phone,
    )
    session.add(booking)
    return booking


# --- Инструктор ---
async def instructor_slot_loads(
    session: AsyncSession, day: date, times: list[str], capacity: int
) -> dict[str, tuple[int, int]]:
    rows = (
        await session.execute(
            select(InstructorBooking.session_time, func.count())
            .where(InstructorBooking.session_date == day)
            .group_by(InstructorBooking.session_time)
        )
    ).all()
    booked = {slot_time: count for slot_time, count in rows}
    return {t: (capacity - booked.get(t, 0), capacity) for t in times}


async def instructor_slot_count(session: AsyncSession, day: date, slot_time: str) -> int:
    return (
        await session.execute(
            select(func.count()).where(
                InstructorBooking.session_date == day,
                InstructorBooking.session_time == slot_time,
            )
        )
    ).scalar_one()


async def create_instructor_booking(
    session: AsyncSession,
    *,
    user_id: int,
    day: date,
    slot_time: str,
    capacity: int,
    full_name: str,
    phone: str,
) -> InstructorBooking:
    """Проверить лимит слота и создать запись. Иначе — :class:`SlotFullError`."""
    if await instructor_slot_count(session, day, slot_time) >= capacity:
        raise SlotFullError

    booking = InstructorBooking(
        user_id=user_id,
        session_date=day,
        session_time=slot_time,
        full_name=full_name,
        phone=phone,
    )
    session.add(booking)
    return booking


# --- Очередь Google Sheets ---
async def enqueue_sheet_row(
    session: AsyncSession, sheet_name: str, row_data: list
) -> None:
    session.add(SheetSyncQueue(sheet_name=sheet_name, row_data=row_data))
