"""
conftest.py

Provides:
- An isolated Postgres test database (tables created fresh and dropped for
  every test function, so tests never see leftover data from previous runs
  and never touch your real dev/prod database).
- A dependency override for get_db so the app under test uses this DB.
- A dependency override + factory helpers for get_current_user so auth
  tests can simulate different logged-in reviewers without hitting a
  real login flow or password hashing.

REQUIRES: a running Postgres instance and a database that already exists
for tests to connect to (SQLAlchemy can create/drop tables, but not the
database itself). This MUST be a separate database from whatever you use
for normal dev work - not "tech" - or tests will read/write real data.
Create it once, e.g.:

    createdb -U postgres -h localhost tech_test
    # or, from psql:
    CREATE DATABASE tech_test;

Then point TEST_DATABASE_URL at it (see below) - via env var or by editing
the default inline.

Adjust the import paths below (`app.db_connection`, `app.auth.dependencies`,
etc.) to match your actual project layout.
"""
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from main import app
from app.db_connection import Base, get_db
from app.auth.dependencies import get_current_user   

# Point this at a dedicated *test* Postgres database - never your dev/prod one.
# Override via env var, e.g.:
#   export TEST_DATABASE_URL="postgresql://user:password@localhost:5432/techkraft_test"
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:1234@localhost:5432/tech_test",
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Fresh tables for every single test, dropped afterwards."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """TestClient wired to the isolated test DB instead of the real one."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class FakeUser:
    """Minimal stand-in for whatever user object get_current_user normally returns."""

    def __init__(self, id: int, role: str = "reviewer"):
        self.id = id
        self.role = role


@pytest.fixture
def as_user(client):
    """
    Usage in a test:

        def test_something(client, as_user):
            as_user(FakeUser(id=6, role="reviewer"))
            response = client.get(...)

    Overrides get_current_user for the duration of the test so you don't
    need a real login/token flow to exercise role-based logic.
    """

    def _set(fake_user: FakeUser):
        app.dependency_overrides[get_current_user] = lambda: fake_user
        return fake_user

    yield _set