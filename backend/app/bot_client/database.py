"""
Database session management for the Telegram bot.
Uses the same PostgreSQL database as the main application.
"""
from contextlib import contextmanager
from typing import Generator

from sqlmodel import Session

from app.core.db import engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session for bot operations."""
    with Session(engine) as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


def get_db_session() -> Session:
    """Create a new database session."""
    return Session(engine)
