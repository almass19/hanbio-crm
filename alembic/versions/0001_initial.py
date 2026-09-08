"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=64)),
        sa.Column("first_name", sa.String(length=128)),
        sa.Column("phone", sa.String(length=20)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("scenario_key", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("full_name", sa.String(length=120)),
        sa.Column("phone", sa.String(length=20)),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_requests_scenario_key", "requests", ["scenario_key"])

    op.create_table(
        "gym_bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("session_time", sa.String(length=5), nullable=False),
        sa.Column("seat_number", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint(
            "session_date", "session_time", "seat_number", name="uq_gym_slot_seat"
        ),
    )
    op.create_index("ix_gym_bookings_session_date", "gym_bookings", ["session_date"])

    op.create_table(
        "instructor_bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("session_time", sa.String(length=5), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_instructor_bookings_session_date", "instructor_bookings", ["session_date"]
    )

    op.create_table(
        "sheet_sync_queue",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sheet_name", sa.String(length=64), nullable=False),
        sa.Column("row_data", sa.JSON(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.String(length=500)),
        sa.Column("synced_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("sheet_sync_queue")
    op.drop_index("ix_instructor_bookings_session_date", "instructor_bookings")
    op.drop_table("instructor_bookings")
    op.drop_index("ix_gym_bookings_session_date", "gym_bookings")
    op.drop_table("gym_bookings")
    op.drop_index("ix_requests_scenario_key", "requests")
    op.drop_table("requests")
    op.drop_index("ix_users_telegram_id", "users")
    op.drop_table("users")
