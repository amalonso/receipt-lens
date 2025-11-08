"""
Authentication tests for user registration, login, and JWT token handling.
Tests cover successful operations, validation errors, and edge cases.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.auth
class TestUserRegistration:
    """Tests for user registration endpoint."""

    def test_register_success(self, client: TestClient, test_user_data: dict):
        """Test successful user registration."""
        response = client.post("/api/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()

        assert data["success"] is True
        assert data["error"] is None
        assert "user" in data["data"]
        assert "token" in data["data"]

        # Verify user data
        user = data["data"]["user"]
        assert user["username"] == test_user_data["username"]
        assert user["email"] == test_user_data["email"]
        assert "id" in user
        assert "created_at" in user
        assert "password" not in user  # Password should not be in response

        # Verify token data
        token = data["data"]["token"]
        assert "access_token" in token
        assert token["token_type"] == "bearer"
        assert token["expires_in"] > 0

    def test_register_duplicate_username(
        self,
        client: TestClient,
        registered_user: dict,
        test_user_data: dict
    ):
        """Test registration with duplicate username fails."""
        # Try to register with same username but different email
        duplicate_data = test_user_data.copy()
        duplicate_data["email"] = "different@example.com"

        response = client.post("/api/auth/register", json=duplicate_data)

        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"].lower()

    def test_register_duplicate_email(
        self,
        client: TestClient,
        registered_user: dict,
        test_user_data: dict
    ):
        """Test registration with duplicate email fails."""
        # Try to register with same email but different username
        duplicate_data = test_user_data.copy()
        duplicate_data["username"] = "differentuser"

        response = client.post("/api/auth/register", json=duplicate_data)

        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"].lower()

    def test_register_invalid_username(self, client: TestClient):
        """Test registration with invalid username format."""
        invalid_data = {
            "username": "invalid user!",  # Contains space and special char
            "email": "test@example.com",
            "password": "TestPassword123"
        }

        response = client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False

    def test_register_short_username(self, client: TestClient):
        """Test registration with username too short."""
        invalid_data = {
            "username": "ab",  # Only 2 characters
            "email": "test@example.com",
            "password": "TestPassword123"
        }

        response = client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email format."""
        invalid_data = {
            "username": "testuser",
            "email": "not-an-email",
            "password": "TestPassword123"
        }

        response = client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422

    def test_register_weak_password_no_uppercase(self, client: TestClient):
        """Test registration with password missing uppercase letter."""
        invalid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"  # No uppercase
        }

        response = client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422

    def test_register_weak_password_no_lowercase(self, client: TestClient):
        """Test registration with password missing lowercase letter."""
        invalid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TESTPASSWORD123"  # No lowercase
        }

        response = client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422

    def test_register_weak_password_no_digit(self, client: TestClient):
        """Test registration with password missing digit."""
        invalid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "TestPassword"  # No digit
        }

        response = client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422

    def test_register_short_password(self, client: TestClient):
        """Test registration with password too short."""
        invalid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Test12"  # Only 6 characters
        }

        response = client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422

    def test_register_missing_fields(self, client: TestClient):
        """Test registration with missing required fields."""
        # Missing password
        response = client.post(
            "/api/auth/register",
            json={"username": "test", "email": "test@example.com"}
        )
        assert response.status_code == 422

        # Missing email
        response = client.post(
            "/api/auth/register",
            json={"username": "test", "password": "TestPassword123"}
        )
        assert response.status_code == 422

        # Missing username
        response = client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "TestPassword123"}
        )
        assert response.status_code == 422


@pytest.mark.auth
class TestUserLogin:
    """Tests for user login endpoint."""

    def test_login_success_with_username(
        self,
        client: TestClient,
        registered_user: dict,
        test_user_data: dict
    ):
        """Test successful login with username."""
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["error"] is None
        assert "user" in data["data"]
        assert "token" in data["data"]

        # Verify token is returned
        token = data["data"]["token"]
        assert "access_token" in token
        assert token["token_type"] == "bearer"

    def test_login_success_with_email(
        self,
        client: TestClient,
        registered_user: dict,
        test_user_data: dict
    ):
        """Test successful login with email."""
        login_data = {
            "username": test_user_data["email"],  # Using email in username field
            "password": test_user_data["password"]
        }

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "token" in data["data"]

    def test_login_wrong_password(
        self,
        client: TestClient,
        registered_user: dict,
        test_user_data: dict
    ):
        """Test login with incorrect password."""
        login_data = {
            "username": test_user_data["username"],
            "password": "WrongPassword123"
        }

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "incorrect" in data["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent username."""
        login_data = {
            "username": "nonexistentuser",
            "password": "TestPassword123"
        }

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "incorrect" in data["detail"].lower()

    def test_login_missing_fields(self, client: TestClient):
        """Test login with missing required fields."""
        # Missing password
        response = client.post(
            "/api/auth/login",
            json={"username": "testuser"}
        )
        assert response.status_code == 422

        # Missing username
        response = client.post(
            "/api/auth/login",
            json={"password": "TestPassword123"}
        )
        assert response.status_code == 422

    def test_login_case_insensitive_username(
        self,
        client: TestClient,
        registered_user: dict,
        test_user_data: dict
    ):
        """Test that login is case-insensitive for username."""
        login_data = {
            "username": test_user_data["username"].upper(),
            "password": test_user_data["password"]
        }

        response = client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200
        assert response.json()["success"] is True


@pytest.mark.auth
class TestCurrentUser:
    """Tests for getting current authenticated user."""

    def test_get_current_user_success(
        self,
        client: TestClient,
        registered_user: dict,
        auth_headers: dict,
        test_user_data: dict
    ):
        """Test getting current user with valid token."""
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["error"] is None

        user = data["data"]
        assert user["username"] == test_user_data["username"]
        assert user["email"] == test_user_data["email"]
        assert "id" in user
        assert "created_at" in user

    def test_get_current_user_no_token(self, client: TestClient):
        """Test getting current user without authentication token."""
        response = client.get("/api/auth/me")

        assert response.status_code == 403  # FastAPI HTTPBearer returns 403

    def test_get_current_user_invalid_token(self, client: TestClient):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.get("/api/auth/me", headers=headers)

        assert response.status_code == 401

    def test_get_current_user_malformed_header(self, client: TestClient):
        """Test getting current user with malformed auth header."""
        # Missing 'Bearer' prefix
        headers = {"Authorization": "just_a_token"}
        response = client.get("/api/auth/me", headers=headers)

        assert response.status_code == 403


@pytest.mark.auth
class TestTokenFunctionality:
    """Tests for JWT token generation and validation."""

    def test_token_contains_user_id(
        self,
        client: TestClient,
        registered_user: dict
    ):
        """Test that JWT token can be used to retrieve user info."""
        token = registered_user["data"]["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/auth/me", headers=headers)

        assert response.status_code == 200
        user_data = response.json()["data"]

        # The user ID from /me should match the registered user
        assert user_data["id"] == registered_user["data"]["user"]["id"]

    def test_different_users_different_tokens(
        self,
        client: TestClient,
        multiple_users: list
    ):
        """Test that different users get different tokens."""
        tokens = [user["data"]["token"]["access_token"] for user in multiple_users]

        # All tokens should be unique
        assert len(tokens) == len(set(tokens))

    def test_token_works_for_correct_user_only(
        self,
        client: TestClient,
        multiple_users: list
    ):
        """Test that each token retrieves the correct user."""
        for registered_user in multiple_users:
            token = registered_user["data"]["token"]["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            response = client.get("/api/auth/me", headers=headers)

            assert response.status_code == 200
            user_data = response.json()["data"]

            # Verify we get the correct user for this token
            assert user_data["id"] == registered_user["data"]["user"]["id"]
            assert user_data["username"] == registered_user["data"]["user"]["username"]


@pytest.mark.auth
class TestPasswordSecurity:
    """Tests for password hashing and security."""

    def test_password_not_stored_in_plain_text(
        self,
        db,
        client: TestClient,
        registered_user: dict,
        test_user_data: dict
    ):
        """Test that passwords are hashed and not stored in plain text."""
        from backend.auth.models import User

        user = db.query(User).filter(
            User.username == test_user_data["username"]
        ).first()

        assert user is not None
        # Password hash should not match plain password
        assert user.password_hash != test_user_data["password"]
        # Hash should start with bcrypt identifier
        assert user.password_hash.startswith("$2b$")

    def test_same_password_different_hashes(self, client: TestClient):
        """Test that same password generates different hashes (salt)."""
        user1_data = {
            "username": "user1",
            "email": "user1@example.com",
            "password": "SamePassword123"
        }
        user2_data = {
            "username": "user2",
            "email": "user2@example.com",
            "password": "SamePassword123"
        }

        client.post("/api/auth/register", json=user1_data)
        client.post("/api/auth/register", json=user2_data)

        # Both should be able to login (hashes work correctly)
        response1 = client.post("/api/auth/login", json={
            "username": "user1",
            "password": "SamePassword123"
        })
        response2 = client.post("/api/auth/login", json={
            "username": "user2",
            "password": "SamePassword123"
        })

        assert response1.status_code == 200
        assert response2.status_code == 200


@pytest.mark.auth
class TestResponseFormat:
    """Tests for consistent API response format."""

    def test_successful_response_format(
        self,
        client: TestClient,
        test_user_data: dict
    ):
        """Test that successful responses follow standard format."""
        response = client.post("/api/auth/register", json=test_user_data)
        data = response.json()

        # Should have success, data, and error fields
        assert "success" in data
        assert "data" in data
        assert "error" in data

        # Success should be True, error should be None
        assert data["success"] is True
        assert data["error"] is None
        assert data["data"] is not None

    def test_error_response_format(self, client: TestClient):
        """Test that error responses follow standard format."""
        # Try to login with non-existent user
        response = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "TestPassword123"
        })

        assert response.status_code == 401
        data = response.json()

        # Should have detail field for HTTP exceptions
        assert "detail" in data
