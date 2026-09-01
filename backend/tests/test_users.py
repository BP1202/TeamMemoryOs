"""
Task 3.3 / 3.4 — User API validation tests.

Covers:
* POST /api/v1/users/     — create user, duplicate rejection
* GET  /api/v1/users/     — list users
* GET  /api/v1/users/{id} — get single user, 404 handling
* password_hash not exposed in response
"""
import uuid

import pytest
from fastapi.testclient import TestClient


API = "/api/v1/users"


@pytest.fixture()
def created_user(client: TestClient):
    """Create a user and yield the response body; delete nothing (no DELETE endpoint yet)."""
    payload = {
        "full_name": "Alice Test",
        "email": f"alice_{uuid.uuid4().hex[:8]}@example.com",
        "password": "securepassword1",
        "is_active": True,
    }
    resp = client.post(f"{API}/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestCreateUser:
    def test_create_returns_201(self, client: TestClient):
        payload = {
            "full_name": "Bob Test",
            "email": f"bob_{uuid.uuid4().hex[:8]}@example.com",
            "password": "securepassword1",
        }
        resp = client.post(f"{API}/", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["full_name"] == "Bob Test"
        assert data["email"] == payload["email"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_password_not_in_response(self, client: TestClient):
        payload = {
            "full_name": "Carol Test",
            "email": f"carol_{uuid.uuid4().hex[:8]}@example.com",
            "password": "supersecret99",
        }
        resp = client.post(f"{API}/", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert "password" not in data
        assert "password_hash" not in data

    def test_duplicate_email_rejected(self, client: TestClient, created_user):
        payload = {
            "full_name": "Duplicate",
            "email": created_user["email"],
            "password": "anotherpassword1",
        }
        resp = client.post(f"{API}/", json=payload)
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"]

    def test_short_password_rejected(self, client: TestClient):
        payload = {
            "full_name": "Short Pass",
            "email": f"short_{uuid.uuid4().hex[:8]}@example.com",
            "password": "short",
        }
        resp = client.post(f"{API}/", json=payload)
        assert resp.status_code == 422

    def test_invalid_email_rejected(self, client: TestClient):
        payload = {
            "full_name": "Bad Email",
            "email": "not-an-email",
            "password": "securepassword1",
        }
        resp = client.post(f"{API}/", json=payload)
        assert resp.status_code == 422


class TestListUsers:
    def test_list_returns_200(self, client: TestClient, created_user):
        resp = client.get(f"{API}/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_created_user_in_list(self, client: TestClient, created_user):
        resp = client.get(f"{API}/", params={"limit": 10000})
        ids = [u["id"] for u in resp.json()]
        assert created_user["id"] in ids


class TestGetUser:
    def test_get_by_id_returns_200(self, client: TestClient, created_user):
        user_id = created_user["id"]
        resp = client.get(f"{API}/{user_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == user_id

    def test_unknown_id_returns_404(self, client: TestClient):
        resp = client.get(f"{API}/{uuid.uuid4()}")
        assert resp.status_code == 404
