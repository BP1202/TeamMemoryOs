"""
Task 3.5 — Authentication Foundation tests.

Covers:
* POST /api/v1/auth/login — valid credentials, wrong password, unknown email
* GET  /api/v1/users/me   — authenticated access, missing token, invalid token
* JWT token structure
"""
import uuid

import pytest
from fastapi.testclient import TestClient

AUTH_URL = "/api/v1/auth/login"
ME_URL = "/api/v1/users/me"
USERS_URL = "/api/v1/users"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_user(client: TestClient, email: str | None = None) -> dict:
    """Register a fresh user and return the response JSON."""
    payload = {
        "full_name": "Auth Test User",
        "email": email or f"auth_{uuid.uuid4().hex[:8]}@example.com",
        "password": "ValidPass123!",
    }
    resp = client.post(f"{USERS_URL}/", json=payload)
    assert resp.status_code == 201, resp.text
    return {**resp.json(), "password": payload["password"], "email": payload["email"]}


def _login(client: TestClient, email: str, password: str) -> dict:
    """POST login form data and return the response."""
    return client.post(AUTH_URL, data={"username": email, "password": password})


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def registered_user(client: TestClient) -> dict:
    """Create a user for auth tests and return combined dict with credentials."""
    return _create_user(client)


@pytest.fixture()
def auth_headers(client: TestClient, registered_user: dict) -> dict:
    """Return Authorization headers for the registered user."""
    resp = _login(client, registered_user["email"], registered_user["password"])
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------

class TestAuthLogin:
    def test_login_returns_200_and_token(self, client: TestClient, registered_user: dict):
        resp = _login(client, registered_user["email"], registered_user["password"])
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20

    def test_token_is_jwt_format(self, client: TestClient, registered_user: dict):
        resp = _login(client, registered_user["email"], registered_user["password"])
        token = resp.json()["access_token"]
        # JWT is three base64url segments separated by dots
        parts = token.split(".")
        assert len(parts) == 3

    def test_wrong_password_returns_401(self, client: TestClient, registered_user: dict):
        resp = _login(client, registered_user["email"], "WrongPassword!")
        assert resp.status_code == 401
        assert "Incorrect" in resp.json()["detail"]

    def test_unknown_email_returns_401(self, client: TestClient):
        resp = _login(client, "nobody@nowhere.com", "SomePass123!")
        assert resp.status_code == 401

    def test_missing_credentials_returns_422(self, client: TestClient):
        resp = client.post(AUTH_URL, data={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Protected endpoint: GET /users/me
# ---------------------------------------------------------------------------

class TestGetMe:
    def test_me_with_valid_token_returns_200(
        self, client: TestClient, registered_user: dict, auth_headers: dict
    ):
        resp = client.get(ME_URL, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == registered_user["email"]
        assert data["id"] == registered_user["id"]
        assert "password" not in data
        assert "password_hash" not in data

    def test_me_without_token_returns_401(self, client: TestClient):
        resp = client.get(ME_URL)
        assert resp.status_code == 401

    def test_me_with_invalid_token_returns_401(self, client: TestClient):
        resp = client.get(ME_URL, headers={"Authorization": "Bearer not.a.valid.jwt"})
        assert resp.status_code == 401

    def test_me_with_malformed_header_returns_401(self, client: TestClient):
        resp = client.get(ME_URL, headers={"Authorization": "NotBearer sometoken"})
        assert resp.status_code == 401
