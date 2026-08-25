"""
Task 4.2 — Scenario API validation tests.

Covers:
* POST /api/v1/scenarios/                              — create scenario (auth required)
* GET  /api/v1/scenarios/organization/{org_id}         — list by org
* GET  /api/v1/scenarios/{scenario_id}                 — get single
* FK violation rejected (unknown org)
* Unauthenticated requests rejected
"""
import uuid

import pytest
from fastapi.testclient import TestClient

USERS_API = "/api/v1/users"
ORGS_API = "/api/v1/organizations"
AUTH_API = "/api/v1/auth/login"
SCENARIOS_API = "/api/v1/scenarios"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _create_user(client: TestClient) -> dict:
    resp = client.post(
        f"{USERS_API}/",
        json={
            "full_name": "Scenario Test User",
            "email": f"scenario_{uuid.uuid4().hex[:8]}@example.com",
            "password": "ValidPass123!",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post(AUTH_API, data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def org(client: TestClient):
    slug = f"scen-org-{uuid.uuid4().hex[:8]}"
    resp = client.post(f"{ORGS_API}/", json={"name": "Scenario Org", "slug": slug})
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def auth_headers(client: TestClient):
    password = "ValidPass123!"
    email = f"scen_auth_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        f"{USERS_API}/",
        json={"full_name": "Auth User", "email": email, "password": password},
    )
    token = _login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def scenario(client: TestClient, org, auth_headers):
    resp = client.post(
        f"{SCENARIOS_API}/",
        json={
            "organization_id": org["id"],
            "name": "Test Scenario",
            "description": "A test scenario",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCreateScenario:
    def test_create_returns_201(self, scenario):
        assert "id" in scenario
        assert scenario["name"] == "Test Scenario"
        assert scenario["description"] == "A test scenario"
        assert scenario["is_active"] is True
        assert "created_by_user_id" in scenario

    def test_creator_is_set_from_token(self, scenario):
        # created_by_user_id must be populated automatically from the JWT
        assert scenario["created_by_user_id"] is not None

    def test_create_without_auth_returns_401(self, client: TestClient, org):
        resp = client.post(
            f"{SCENARIOS_API}/",
            json={"organization_id": org["id"], "name": "No Auth"},
        )
        assert resp.status_code == 401

    def test_create_unknown_org_returns_400(self, client: TestClient, auth_headers):
        resp = client.post(
            f"{SCENARIOS_API}/",
            json={"organization_id": str(uuid.uuid4()), "name": "Ghost Org"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_create_minimal_fields(self, client: TestClient, org, auth_headers):
        """Only required fields — description is optional."""
        resp = client.post(
            f"{SCENARIOS_API}/",
            json={"organization_id": org["id"], "name": "Minimal"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["description"] is None

    def test_missing_name_returns_422(self, client: TestClient, org, auth_headers):
        resp = client.post(
            f"{SCENARIOS_API}/",
            json={"organization_id": org["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestListScenariosByOrg:
    def test_list_returns_200_and_contains_created(
        self, client: TestClient, scenario, auth_headers
    ):
        resp = client.get(
            f"{SCENARIOS_API}/organization/{scenario['organization_id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()]
        assert scenario["id"] in ids

    def test_list_unknown_org_returns_empty(self, client: TestClient, auth_headers):
        resp = client.get(
            f"{SCENARIOS_API}/organization/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_without_auth_returns_401(self, client: TestClient, scenario):
        resp = client.get(
            f"{SCENARIOS_API}/organization/{scenario['organization_id']}"
        )
        assert resp.status_code == 401


class TestGetScenario:
    def test_get_by_id_returns_200(self, client: TestClient, scenario, auth_headers):
        resp = client.get(f"{SCENARIOS_API}/{scenario['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == scenario["id"]

    def test_unknown_id_returns_404(self, client: TestClient, auth_headers):
        resp = client.get(f"{SCENARIOS_API}/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_without_auth_returns_401(self, client: TestClient, scenario):
        resp = client.get(f"{SCENARIOS_API}/{scenario['id']}")
        assert resp.status_code == 401
