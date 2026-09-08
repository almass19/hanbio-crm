"""CRM fields on requests & instructor_bookings

- requests: admin_comment / processed_at / processed_by (заполняет CRM)
- instructor_bookings: widen session_time; add instructor / age / status /
  programs_comment (как в листе «Запись к Инструктору Новая»)

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-08
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("requests") as batch_op:
        batch_op.add_column(sa.Column("admin_comment", sa.String(length=2000)))
        batch_op.add_column(
            sa.Column("processed_at", sa.DateTime(timezone=True))
        )
        batch_op.add_column(sa.Column("processed_by", sa.String(length=36)))

    with op.batch_alter_table("instructor_bookings") as batch_op:
        batch_op.alter_column(
            "session_time",
            existing_type=sa.String(length=5),
            type_=sa.String(length=20),
        )
        batch_op.add_column(sa.Column("instructor", sa.String(length=120)))
        batch_op.add_column(sa.Column("age", sa.Integer()))
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(length=20),
                nullable=False,
                server_default="Не обработан",
            )
        )
        batch_op.add_column(
            sa.Column("programs_comment", sa.String(length=2000))
        )
        batch_op.create_index(
            "ix_instructor_bookings_status", ["status"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("instructor_bookings") as batch_op:
        batch_op.drop_index("ix_instructor_bookings_status")
        batch_op.drop_column("programs_comment")
        batch_op.drop_column("status")
        batch_op.drop_column("age")
        batch_op.drop_column("instructor")
        batch_op.alter_column(
            "session_time",
            existing_type=sa.String(length=20),
            type_=sa.String(length=5),
        )

    with op.batch_alter_table("requests") as batch_op:
        batch_op.drop_column("processed_by")
        batch_op.drop_column("processed_at")
        batch_op.drop_column("admin_comment")
