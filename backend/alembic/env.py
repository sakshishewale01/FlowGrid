import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from alembic import context

# ------------------------------------------------------------------------------
# 1. Path Configuration
# ------------------------------------------------------------------------------
# Ensure the backend root directory is on the Python module search path.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import application settings and SQLAlchemy Base
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

# Alembic Config object
config = context.config

# Overwrite sqlalchemy.url dynamically from app settings (.env)
config.set_main_option("sqlalchemy.url", settings.database_url)

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ------------------------------------------------------------------------------
# 2. Model Metadata Target
# ------------------------------------------------------------------------------
# Connect Alembic to our SQLAlchemy Base metadata for 'autogenerate' support.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    Configures the context with just a URL and emits SQL statements to stdout/script.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    Connects to the database and applies migrations within a transaction.
    """
    # Reuse our configured SQLAlchemy engine
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
