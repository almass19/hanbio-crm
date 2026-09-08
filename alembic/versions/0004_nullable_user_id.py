"""nullable user_id on gym_bookings & instructor_bookings

Записи можно создавать/править в CRM без привязки к Telegram-пользователю.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-08
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ("gym_bookings", "instructor_bookings"):
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                "user_id", existing_type=sa.Integer(), nullable=True
            )


def downgrade() -> None:
    for table in ("gym_bookings", "instructor_bookings"):
        with op.batch_alter_table(table) as batch_op:
            batch_op.alter_column(
                "user_id", existing_type=sa.Integer(), nullable=False
            )
