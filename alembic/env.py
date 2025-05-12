from logging.config import fileConfig
from alembic import context

from src.backend.models import SQLModel
from src.backend.database import engine

# Alembic Config
config = context.config

# Logging setup
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use SQLModel metadata
target_metadata = SQLModel.metadata


def run_migrations_online() -> None:
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
    raise RuntimeError("❌ Offline mode is not supported. Use online mode with a database connection.")
else:
    run_migrations_online()

