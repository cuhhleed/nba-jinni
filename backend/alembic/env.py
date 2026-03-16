import asyncio
import os

from dotenv import load_dotenv
load_dotenv()

from logging.config import fileConfig

from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

from alembic import context

from app.db.base import Base
import app.models



config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Wire up metadata here once models are defined
# from app.db.base import Base
# target_metadata = Base.metadata
target_metadata = Base.metadata

def get_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        return None
    return url


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
elif get_url():
    asyncio.run(run_migrations_online())