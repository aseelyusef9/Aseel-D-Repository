# db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database backend selection
DB_BACKEND = os.getenv("DB_BACKEND", "sqlite")  # default: sqlite

if DB_BACKEND == "postgres":
    DATABASE_URL = "postgresql://user:password@localhost/invoices_db"
    connect_args = {}
else:
    DATABASE_URL = "sqlite:///./invoices.db"
    connect_args = {"check_same_thread": False}  # Needed for SQLite + FastAPI

# SQLAlchemy Engine & Session
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base class for models
Base = declarative_base()

# FastAPI dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
