"""widen gym_bookings.session_time

Реальные слоты зала — диапазоны вида "10:10 - 10:40" (до 14 символов),
а не "HH:MM" как предполагалось изначально.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-05
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("gym_bookings") as batch_op:
        batch_op.alter_column(
            "session_time",
            existing_type=sa.String(length=5),
            type_=sa.String(length=20),
        )


def downgrade() -> None:
    with op.batch_alter_table("gym_bookings") as batch_op:
        batch_op.alter_column(
            "session_time",
            existing_type=sa.String(length=20),
            type_=sa.String(length=5),
        )
