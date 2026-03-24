import sys
import os
from logging.config import fileConfig
from sqlalchemy import create_engine
from alembic import context

# добавляем app/ в путь
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "app"))

from core.config import settings
from db.base import Base
from models.user import User
from models.item import Item

# метадата всех моделей
target_metadata = Base.metadata

# Alembic Config
config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = create_engine(settings.database_url)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
