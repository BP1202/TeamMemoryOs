"""
Task 4.2 — Memory Entry API validation tests.

Covers:
* POST /api/v1/memory/                                 — create entry (auth required)
* GET  /api/v1/memory/organization/{org_id}            — list by org
* GET  /api/v1/memory/scenario/{scenario_id}           — list by scenario
* GET  /api/v1/memory/{entry_id}                       — get single
* FK violation rejected (unknown org)
* Invalid memory_type rejected (422)
* Unauthenticated requests rejected
"""
import uuid

import pytest
from fastapi.testclient import TestClient

USERS_API = "/api/v1/users"
ORGS_API = "/api/v1/organizations"
SCENARIOS_API = "/api/v1/scenarios"
AUTH_API = "/api/v1/auth/login"
MEMORY_API = "/api/v1/memory"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post(AUTH_API, data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def org(client: TestClient):
    slug = f"mem-org-{uuid.uuid4().hex[:8]}"
    resp = client.post(f"{ORGS_API}/", json={"name": "Memory Org", "slug": slug})
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def auth_headers(client: TestClient):
    password = "ValidPass123!"
    email = f"mem_auth_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        f"{USERS_API}/",
        json={"full_name": "Mem Auth User", "email": email, "password": password},
    )
    token = _login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def scenario(client: TestClient, org, auth_headers):
    resp = client.post(
        f"{SCENARIOS_API}/",
        json={"organization_id": org["id"], "name": "Memory Test Scenario"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def memory_entry(client: TestClient, org, scenario, auth_headers):
    resp = client.post(
        f"{MEMORY_API}/",
        json={
            "organization_id": org["id"],
            "scenario_id": scenario["id"],
            "memory_type": "decision",
            "title": "Use PostgreSQL",
            "content": "We decided to use PostgreSQL for the primary datastore.",
            "meta": {"tags": ["database", "architecture"], "confidence": 0.95},
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCreateMemoryEntry:
    def test_create_returns_201(self, memory_entry):
        assert "id" in memory_entry
        assert memory_entry["memory_type"] == "decision"
        assert memory_entry["title"] == "Use PostgreSQL"
        assert memory_entry["content"] == "We decided to use PostgreSQL for the primary datastore."
        assert memory_entry["meta"]["tags"] == ["database", "architecture"]

    def test_creator_is_set_from_token(self, memory_entry):
        assert memory_entry["created_by_user_id"] is not None

    def test_create_without_scenario(self, client: TestClient, org, auth_headers):
        """scenario_id is optional — entry should be created without it."""
        resp = client.post(
            f"{MEMORY_API}/",
            json={
                "organization_id": org["id"],
                "memory_type": "context",
                "content": "Background context with no scenario.",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["scenario_id"] is None

    def test_create_without_auth_returns_401(self, client: TestClient, org):
        resp = client.post(
            f"{MEMORY_API}/",
            json={
                "organization_id": org["id"],
                "memory_type": "insight",
                "content": "No auth attempt.",
            },
        )
        assert resp.status_code == 401

    def test_create_unknown_org_returns_400(self, client: TestClient, auth_headers):
        resp = client.post(
            f"{MEMORY_API}/",
            json={
                "organization_id": str(uuid.uuid4()),
                "memory_type": "decision",
                "content": "Ghost org content.",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_invalid_memory_type_returns_422(
        self, client: TestClient, org, auth_headers
    ):
        resp = client.post(
            f"{MEMORY_API}/",
            json={
                "organization_id": org["id"],
                "memory_type": "not_a_valid_type",
                "content": "Bad type.",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_missing_content_returns_422(
        self, client: TestClient, org, auth_headers
    ):
        resp = client.post(
            f"{MEMORY_API}/",
            json={"organization_id": org["id"], "memory_type": "decision"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_all_memory_types_accepted(self, client: TestClient, org, auth_headers):
        for mtype in ("decision", "context", "artifact", "insight", "discussion"):
            resp = client.post(
                f"{MEMORY_API}/",
                json={
                    "organization_id": org["id"],
                    "memory_type": mtype,
                    "content": f"Content for type {mtype}.",
                },
                headers=auth_headers,
            )
            assert resp.status_code == 201, f"Failed for type {mtype!r}: {resp.text}"
            assert resp.json()["memory_type"] == mtype


class TestListMemoryEntriesByOrg:
    def test_list_returns_200_and_contains_created(
        self, client: TestClient, memory_entry, auth_headers
    ):
        resp = client.get(
            f"{MEMORY_API}/organization/{memory_entry['organization_id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        ids = [e["id"] for e in resp.json()]
        assert memory_entry["id"] in ids

    def test_list_unknown_org_returns_empty(self, client: TestClient, auth_headers):
        resp = client.get(
            f"{MEMORY_API}/organization/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_without_auth_returns_401(self, client: TestClient, memory_entry):
        resp = client.get(
            f"{MEMORY_API}/organization/{memory_entry['organization_id']}"
        )
        assert resp.status_code == 401


class TestListMemoryEntriesByScenario:
    def test_list_by_scenario_returns_entry(
        self, client: TestClient, memory_entry, auth_headers
    ):
        resp = client.get(
            f"{MEMORY_API}/scenario/{memory_entry['scenario_id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        ids = [e["id"] for e in resp.json()]
        assert memory_entry["id"] in ids

    def test_list_unknown_scenario_returns_empty(
        self, client: TestClient, auth_headers
    ):
        resp = client.get(
            f"{MEMORY_API}/scenario/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetMemoryEntry:
    def test_get_by_id_returns_200(
        self, client: TestClient, memory_entry, auth_headers
    ):
        resp = client.get(
            f"{MEMORY_API}/{memory_entry['id']}", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == memory_entry["id"]
        assert data["content"] == memory_entry["content"]

    def test_unknown_id_returns_404(self, client: TestClient, auth_headers):
        resp = client.get(f"{MEMORY_API}/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_without_auth_returns_401(self, client: TestClient, memory_entry):
        resp = client.get(f"{MEMORY_API}/{memory_entry['id']}")
        assert resp.status_code == 401
