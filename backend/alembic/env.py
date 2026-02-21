import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

# agregamos la ruta de tu app
sys.path.append(".")

from app.infrastructure.database import Base, DATABASE_URL
from app.domain import *

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# Target metadata
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode using DATABASE_URL from app config."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "pyformat"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode using DATABASE_URL from app config."""
    # Create engine from DATABASE_URL (not from alembic.ini)
    # Convert asyncpg URL to psycopg (sync) URL for migrations
    sync_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg://")
    
    connectable = create_engine(sync_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
