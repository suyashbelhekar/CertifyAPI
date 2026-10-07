"""
Database setup using SQLAlchemy with SQLite.
A single engine and session factory are shared across the application.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# SQLite file stored at project root level
DATABASE_URL = "sqlite:///./certificates.db"

engine = create_engine(
    DATABASE_URL,
    # Required for SQLite to allow usage across threads (needed for BackgroundTasks)
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def get_db():
    """
    FastAPI dependency that yields a database session
    and ensures it is closed after each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
