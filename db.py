import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Base class for models (shared)
Base = declarative_base()

# Module-level placeholders (set by init_db)
engine = None
SessionLocal = None


def init_db(database_url: Optional[str] = None):
    """Initialize the SQLAlchemy engine and session factory.

    If `database_url` is not provided, the function will read
    `DB_BACKEND` from the environment and choose a default.
    Returns the created engine.
    """
    global engine, SessionLocal

    DB_BACKEND = os.getenv("DB_BACKEND", "sqlite")

    if database_url is None:
        if DB_BACKEND == "postgres":
            database_url = "postgresql://user:password@localhost/invoices_db"
            connect_args = {}
        else:
            database_url = "sqlite:///./invoices.db"
            connect_args = {"check_same_thread": False}
    else:
        # allow caller to override connect_args for sqlite in-memory tests
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

    engine = create_engine(database_url, connect_args=connect_args)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # expose for imports
    globals()["engine"] = engine
    globals()["SessionLocal"] = SessionLocal
    return engine


def get_db():
    """FastAPI dependency generator that yields a DB session.

    Requires `init_db()` to have been called first.
    """
    if SessionLocal is None:
        # Lazily initialize with defaults if not already initialized
        init_db()

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
