"""
Shared pytest fixtures.

Key decisions:
  - A separate in-memory SQLite database is used for every test session so
    tests never touch the real certificates.db file.
  - A temporary directory replaces the production 'generated/' folder so
    test PDFs don't accumulate on disk and don't interfere with each other.
  - The TestClient runs BackgroundTasks synchronously within the request
    cycle (FastAPI's default behavior with TestClient), which means tests
    can check final job state immediately after the POST /jobs call.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


# ---------------------------------------------------------------------------
# In-memory test database
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///./test_certificates.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Replace the production DB session with the test session."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function", autouse=True)
def setup_test_db():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(tmp_path, monkeypatch):
    """
    Return a FastAPI TestClient wired to:
      - the test database (via dependency override)
      - a per-test temp directory for generated PDFs
    """
    # Override the DB dependency
    app.dependency_overrides[get_db] = override_get_db

    # Redirect generated certificates to a temp folder
    monkeypatch.setattr("app.services.GENERATED_DIR", str(tmp_path))

    # Also patch SessionLocal used inside the background task wrapper
    monkeypatch.setattr("app.main.SessionLocal", TestSessionLocal)

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()
