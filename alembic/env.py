"""Окружение Alembic. Работает с синхронным драйвером SQLite
(URL из настроек, `+aiosqlite` отбрасывается).
"""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bot.config import settings  # noqa: E402
from bot.db.models import Base  # noqa: E402

config = context.config
# При запуске из bot.main (embedded) не трогаем конфигурацию логирования —
# иначе fileConfig затрёт настройки приложения и заглушит рантайм-логи.
if config.config_file_name is not None and not config.attributes.get("embedded"):
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _sync_url() -> str:
    return settings.database_url.replace("+aiosqlite", "")


def run_migrations_offline() -> None:
    context.configure(
        url=_sync_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = _sync_url()
    connectable = engine_from_config(
        section, prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
