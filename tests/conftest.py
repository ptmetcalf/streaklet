import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from datetime import date
import os
from freezegun import freeze_time

from app.core.db import Base, get_db
from app.main import app
from app.core.config import settings


# Freeze time to a consistent datetime for all tests
# Using 2025-12-14 12:00 PM America/Chicago timezone
@pytest.fixture(scope="function", autouse=True)
def frozen_time():
    """Freeze time to ensure consistent dates across all test environments."""
    with freeze_time("2025-12-14 12:00:00", tz_offset=-6):  # America/Chicago is UTC-6
        yield


@pytest.fixture(scope="session", autouse=True)
def test_secret_key():
    """Provide a deterministic secret key for encryption during tests."""
    os.environ.setdefault("APP_SECRET_KEY", "test-secret-key")
    settings.app_secret_key = os.environ["APP_SECRET_KEY"]
    yield


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test."""
    test_db_path = "/tmp/test_streaklet.db"

    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False}
    )

    # Enable foreign keys for SQLite test database
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSessionLocal()

    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture(scope="function")
def client(test_db: Session):
    """Create a test client with dependency override."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_profiles(test_db: Session):
    """Create sample profiles for testing."""
    from app.models.profile import Profile

    profiles = [
        Profile(id=1, name="Test Profile 1", color="#3b82f6"),
        Profile(id=2, name="Test Profile 2", color="#10b981"),
    ]

    for profile in profiles:
        test_db.add(profile)
    test_db.commit()

    return profiles


@pytest.fixture
def sample_tasks(test_db: Session, sample_profiles):
    """Create sample tasks for testing (for profile 1)."""
    from app.models.task import Task

    # Set active_since to a date in the past to ensure tasks count toward completion
    # Using 2024-11-01 so tasks are active for December 2024 tests
    past_date = date(2024, 11, 1)

    tasks = [
        Task(id=1, user_id=1, title="Task 1", sort_order=1, is_required=True, is_active=True, active_since=past_date),
        Task(id=2, user_id=1, title="Task 2", sort_order=2, is_required=True, is_active=True, active_since=past_date),
        Task(id=3, user_id=1, title="Task 3", sort_order=3, is_required=False, is_active=True, active_since=past_date),
    ]

    for task in tasks:
        test_db.add(task)
    test_db.commit()

    return tasks
