"""
Pytest configuration and fixtures for testing.
Provides database setup, test client, and common fixtures.
"""

import os
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from backend.database.base import Base
from backend.main import app
from backend.dependencies import get_db
from backend.config import settings

# Test database URL (use in-memory SQLite for fast testing)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with StaticPool to keep in-memory database alive
from sqlalchemy.pool import StaticPool

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite specific
    poolclass=StaticPool  # Keep in-memory database alive
)

# Create test session factory
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Create a fresh database for each test.
    Drops all tables after the test completes.

    Yields:
        Session: SQLAlchemy database session
    """
    # Import all models to ensure they are registered
    from backend.database.base import import_models
    import_models()

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with dependency overrides.

    Args:
        db: Database session fixture

    Yields:
        TestClient: FastAPI test client
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user_data() -> dict:
    """
    Fixture providing test user registration data.

    Returns:
        dict: User registration data
    """
    return {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "TestPassword123"
    }


@pytest.fixture(scope="function")
def test_user_data_alt() -> dict:
    """
    Fixture providing alternative test user data.

    Returns:
        dict: Alternative user registration data
    """
    return {
        "username": "altuser",
        "email": "altuser@example.com",
        "password": "AltPassword456"
    }


@pytest.fixture(scope="function")
def registered_user(client: TestClient, test_user_data: dict) -> dict:
    """
    Fixture that registers a test user and returns the response.

    Args:
        client: Test client fixture
        test_user_data: User data fixture

    Returns:
        dict: Registration response with user and token
    """
    response = client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture(scope="function")
def auth_headers(registered_user: dict) -> dict:
    """
    Fixture providing authentication headers with JWT token.

    Args:
        registered_user: Registered user fixture

    Returns:
        dict: Authorization headers
    """
    token = registered_user["data"]["token"]["access_token"]
    return {
        "Authorization": f"Bearer {token}"
    }


@pytest.fixture(scope="function")
def multiple_users(client: TestClient) -> list[dict]:
    """
    Fixture creating multiple test users.

    Args:
        client: Test client fixture

    Returns:
        list[dict]: List of registered user responses
    """
    users_data = [
        {
            "username": f"user{i}",
            "email": f"user{i}@example.com",
            "password": f"Password{i}23"
        }
        for i in range(1, 4)
    ]

    registered = []
    for user_data in users_data:
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        registered.append(response.json())

    return registered


# Note: Using in-memory SQLite database, no need for file cleanup
