from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.engine import Engine
from typing import Generator
import os
from app.core.config import settings


# Enable foreign key constraints for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key support in SQLite."""
    if 'sqlite' in str(dbapi_conn):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Ensure the data directory exists (only if parent directory is writable)
try:
    os.makedirs(os.path.dirname(settings.db_path), exist_ok=True)
except (PermissionError, OSError):
    # In test/CI environments, directory creation may fail
    # The actual database path will be overridden in tests anyway
    pass

# Create SQLite engine
SQLALCHEMY_DATABASE_URL = f"sqlite:///{settings.db_path}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database sessions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
