"""
infrastructure/persistence/database.py

Database engine and session factory.
FastAPI dependency `get_db_session` is kept here rather than in the
presentation layer because it belongs to infrastructure concerns.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.config.settings import get_settings


def _build_engine():
    settings = get_settings()
    return create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},  # required for SQLite
    )


_engine = _build_engine()
_SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_engine():
    return _engine


def get_db_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and ensures it is closed."""
    session = _SessionFactory()
    try:
        yield session
    finally:
        session.close()
