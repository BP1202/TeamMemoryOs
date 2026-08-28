import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# ---------------------------------------------------------------------------
# Make the backend package importable when alembic is run from backend/
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.settings import settings  # noqa: E402
from app.db.base import Base            # noqa: E402
import app.models  # noqa: F401 — registers all models with Base.metadata

# Register pgvector types with psycopg on each new connection so Alembic
# can introspect vector columns during autogenerate.  The try/except guard
# allows migrations to run even before CREATE EXTENSION vector has executed.
from sqlalchemy import event
from sqlalchemy.engine import Engine
import pgvector.psycopg as _pgvector_psycopg


@event.listens_for(Engine, "connect")
def _register_pgvector(dbapi_conn, _connection_record):
    try:
        _pgvector_psycopg.register_vector(dbapi_conn)
    except Exception:
        pass  # extension not yet installed — migration will create it

# ---------------------------------------------------------------------------
# Alembic Config object — access to values in alembic.ini
# ---------------------------------------------------------------------------
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Supply the database URL from project settings, not from alembic.ini.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Target metadata for autogenerate support.
target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Autogenerate exclusions — indexes created via raw SQL in older migrations
# that Alembic cannot track through metadata inspection.
# ---------------------------------------------------------------------------
_EXCLUDED_INDEXES = frozenset({
    "ix_memory_entries_embedding_hnsw",  # created by 581c2cdd5ce2 via op.execute()
})


def include_object(obj, name, type_, reflected, compare_to):
    """Prevent autogenerate from touching raw-SQL-managed objects."""
    if type_ == "index" and name in _EXCLUDED_INDEXES:
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL and not an Engine, so no live
    database connection is required to generate SQL scripts.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine from the config and associates a connection with the
    migration context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
