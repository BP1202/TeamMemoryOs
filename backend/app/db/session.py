from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
import pgvector.psycopg as _pgvector_psycopg

from app.core.settings import settings

engine = create_engine(settings.DATABASE_URL)


@event.listens_for(engine, "connect")
def _register_pgvector(dbapi_conn, _connection_record):
    """Register pgvector types with each new psycopg connection.

    The guard allows the app to start and migrations to run even before
    CREATE EXTENSION vector has been executed in the target database.
    """
    try:
        _pgvector_psycopg.register_vector(dbapi_conn)
    except Exception:
        pass  # extension not yet installed


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

