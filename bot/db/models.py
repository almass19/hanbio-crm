"""ORM-модели (SQLAlchemy 2.0).

БД — источник правды. Google Sheets получает копию данных отдельно
через таблицу-очередь :class:`SheetSyncQueue`.

Временные метки хранятся в UTC (`created_at`); отображение в часовом поясе
центра делается на слое представления (:mod:`bot.utils.dates`).
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# JSON на SQLite (локальная разработка), JSONB на Postgres (Supabase — общая
# база с CRM). Одна модель работает в обоих случаях.
JSONType = JSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(128))
    phone: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Request(Base):
    """Заявка по любому линейному сценарию (3, 4, 6, 7, 8, 9) и сценарию 5."""

    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    scenario_key: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSONType, default=dict)
    full_name: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="new")  # new | processed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    # заполняются в CRM, бот их не трогает
    admin_comment: Mapped[str | None] = mapped_column(String(2000))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processed_by: Mapped[str | None] = mapped_column(String(36))


class GymBooking(Base):
    """Запись в общий зал. Двойная бронь исключена на уровне БД."""

    __tablename__ = "gym_bookings"
    __table_args__ = (
        UniqueConstraint(
            "session_date", "session_time", "seat_number", name="uq_gym_slot_seat"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))  # None = из CRM
    session_date: Mapped[date] = mapped_column(Date, index=True)
    session_time: Mapped[str] = mapped_column(String(20))  # "10:10 - 10:40"
    seat_number: Mapped[int] = mapped_column(Integer)  # номер аппарата
    full_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class InstructorBooking(Base):
    """Запись к инструктору. Лимит на слот — `INSTRUCTOR_SLOTS_PER_HOUR`.

    Бот заполняет `session_date / session_time / full_name / phone`; поля
    `instructor / age / status / programs_comment` ведёт администратор в CRM
    (как в листе «Запись к Инструктору Новая»).
    """

    __tablename__ = "instructor_bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))  # None = из CRM
    session_date: Mapped[date] = mapped_column(Date, index=True)
    session_time: Mapped[str] = mapped_column(String(20))  # "10:10 - 10:40"
    full_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20))
    instructor: Mapped[str | None] = mapped_column(String(120))
    age: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(20), default="Не обработан", index=True
    )  # Не обработан | Обработан
    programs_comment: Mapped[str | None] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class SheetSyncQueue(Base):
    """Очередь строк на отправку в Google Sheets (отказоустойчивая витрина)."""

    __tablename__ = "sheet_sync_queue"

    id: Mapped[int] = mapped_column(primary_key=True)
    sheet_name: Mapped[str] = mapped_column(String(64))
    row_data: Mapped[list] = mapped_column(JSONType)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(String(500))
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
