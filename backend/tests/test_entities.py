"""
Sprint 5.1 — Entity Extraction Foundation tests.

Covers:
* POST /api/v1/entities/                              — create entity (auth required)
* GET  /api/v1/entities/organization/{org_id}         — list by org
* GET  /api/v1/entities/organization/{org_id}?type=X  — filter by type
* GET  /api/v1/entities/{entity_id}                   — get single entity
* POST /api/v1/entities/memory/{id}/attach            — attach entity to memory
* GET  /api/v1/entities/memory/{id}                   — list entities on memory
* POST /api/v1/entities/extract                       — extract entities from text
* Duplicate entity returns 409
* Organisation isolation (entities not visible across orgs)
* Unauthenticated requests rejected

Unit tests for entity_extraction service:
* PR number extraction
* Branch extraction
* File path extraction
* API endpoint extraction
* Technology detection
* Service name detection
* Deduplication
* Normalisation
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.services.entity_extraction import extract_entities, RawEntity
from app.models.entity import EntityType

USERS_API = "/api/v1/users"
ORGS_API = "/api/v1/organizations"
SCENARIOS_API = "/api/v1/scenarios"
AUTH_API = "/api/v1/auth/login"
MEMORY_API = "/api/v1/memory"
ENTITIES_API = "/api/v1/entities"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post(AUTH_API, data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _make_user(client: TestClient) -> tuple[str, dict]:
    """Create a user and return (token, headers)."""
    password = "ValidPass123!"
    email = f"entity_user_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        f"{USERS_API}/",
        json={"full_name": "Entity Test User", "email": email, "password": password},
    )
    token = _login(client, email, password)
    return token, {"Authorization": f"Bearer {token}"}


def _make_org(client: TestClient) -> dict:
    slug = f"entity-org-{uuid.uuid4().hex[:8]}"
    resp = client.post(f"{ORGS_API}/", json={"name": "Entity Org", "slug": slug})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _make_memory(client: TestClient, org_id: str, headers: dict) -> dict:
    resp = client.post(
        f"{MEMORY_API}/",
        json={
            "organization_id": org_id,
            "memory_type": "decision",
            "content": "Decided to use PostgreSQL for storage.",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def org(client: TestClient):
    return _make_org(client)


@pytest.fixture()
def auth_headers(client: TestClient):
    _, headers = _make_user(client)
    return headers


@pytest.fixture()
def entity(client: TestClient, org, auth_headers):
    resp = client.post(
        f"{ENTITIES_API}/",
        json={
            "organization_id": org["id"],
            "entity_type": "TECHNOLOGY",
            "name": "PostgreSQL",
            "description": "Primary database",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def memory_entry(client: TestClient, org, auth_headers):
    return _make_memory(client, org["id"], auth_headers)


# ===========================================================================
# API Tests
# ===========================================================================


class TestCreateEntity:
    def test_create_returns_201(self, entity):
        assert "id" in entity
        assert entity["entity_type"] == "TECHNOLOGY"
        assert entity["name"] == "PostgreSQL"
        assert entity["organization_id"] is not None
        assert entity["created_at"] is not None

    def test_create_all_entity_types(self, client: TestClient, auth_headers):
        org = _make_org(client)
        for etype in (
            "PERSON", "REPOSITORY", "FILE", "SERVICE", "TECHNOLOGY",
            "INCIDENT", "PULL_REQUEST", "BRANCH", "API_ENDPOINT"
        ):
            resp = client.post(
                f"{ENTITIES_API}/",
                json={
                    "organization_id": org["id"],
                    "entity_type": etype,
                    "name": f"test-{etype.lower()}",
                },
                headers=auth_headers,
            )
            assert resp.status_code == 201, f"Failed for type {etype}: {resp.text}"
            assert resp.json()["entity_type"] == etype

    def test_duplicate_entity_returns_409(self, client: TestClient, entity, auth_headers):
        """Same (org, type, name) must be rejected with 409."""
        resp = client.post(
            f"{ENTITIES_API}/",
            json={
                "organization_id": entity["organization_id"],
                "entity_type": entity["entity_type"],
                "name": entity["name"],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 409, resp.text

    def test_same_name_different_type_is_allowed(self, client: TestClient, entity, auth_headers):
        """Same name under a different entity type is a distinct entity."""
        resp = client.post(
            f"{ENTITIES_API}/",
            json={
                "organization_id": entity["organization_id"],
                "entity_type": "SERVICE",
                "name": entity["name"],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text

    def test_same_name_different_org_is_allowed(self, client: TestClient, entity, auth_headers):
        """Same name + type is permitted for a different organisation."""
        other_org = _make_org(client)
        resp = client.post(
            f"{ENTITIES_API}/",
            json={
                "organization_id": other_org["id"],
                "entity_type": entity["entity_type"],
                "name": entity["name"],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text

    def test_create_without_auth_returns_401(self, client: TestClient, org):
        resp = client.post(
            f"{ENTITIES_API}/",
            json={
                "organization_id": org["id"],
                "entity_type": "TECHNOLOGY",
                "name": "NoAuth",
            },
        )
        assert resp.status_code == 401

    def test_create_invalid_type_returns_422(self, client: TestClient, org, auth_headers):
        resp = client.post(
            f"{ENTITIES_API}/",
            json={
                "organization_id": org["id"],
                "entity_type": "INVALID_TYPE",
                "name": "WontWork",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_create_missing_name_returns_422(self, client: TestClient, org, auth_headers):
        resp = client.post(
            f"{ENTITIES_API}/",
            json={
                "organization_id": org["id"],
                "entity_type": "TECHNOLOGY",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestListEntitiesByOrg:
    def test_list_returns_created_entity(self, client: TestClient, entity, auth_headers):
        resp = client.get(
            f"{ENTITIES_API}/organization/{entity['organization_id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        ids = [e["id"] for e in resp.json()]
        assert entity["id"] in ids

    def test_list_filter_by_type(self, client: TestClient, entity, auth_headers):
        org_id = entity["organization_id"]
        # Create a REPOSITORY entity in the same org
        client.post(
            f"{ENTITIES_API}/",
            json={"organization_id": org_id, "entity_type": "REPOSITORY", "name": "myorg/myrepo"},
            headers=auth_headers,
        )
        resp = client.get(
            f"{ENTITIES_API}/organization/{org_id}?entity_type=REPOSITORY",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        types = {e["entity_type"] for e in resp.json()}
        assert types == {"REPOSITORY"}

    def test_list_unknown_org_returns_empty(self, client: TestClient, auth_headers):
        resp = client.get(
            f"{ENTITIES_API}/organization/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_organisation_isolation(self, client: TestClient, entity, auth_headers):
        """Entities from org A must not appear in a list for org B."""
        other_org = _make_org(client)
        resp = client.get(
            f"{ENTITIES_API}/organization/{other_org['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        ids = [e["id"] for e in resp.json()]
        assert entity["id"] not in ids

    def test_list_without_auth_returns_401(self, client: TestClient, entity):
        resp = client.get(f"{ENTITIES_API}/organization/{entity['organization_id']}")
        assert resp.status_code == 401


class TestGetEntity:
    def test_get_by_id_returns_200(self, client: TestClient, entity, auth_headers):
        resp = client.get(f"{ENTITIES_API}/{entity['id']}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == entity["id"]
        assert data["name"] == entity["name"]

    def test_unknown_id_returns_404(self, client: TestClient, auth_headers):
        resp = client.get(f"{ENTITIES_API}/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_without_auth_returns_401(self, client: TestClient, entity):
        resp = client.get(f"{ENTITIES_API}/{entity['id']}")
        assert resp.status_code == 401


class TestMemoryEntityAttachment:
    def test_attach_returns_201(self, client: TestClient, entity, memory_entry, auth_headers):
        resp = client.post(
            f"{ENTITIES_API}/memory/{memory_entry['id']}/attach",
            json={
                "memory_entry_id": memory_entry["id"],
                "entity_id": entity["id"],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["memory_entry_id"] == memory_entry["id"]
        assert data["entity_id"] == entity["id"]

    def test_duplicate_attachment_returns_409(
        self, client: TestClient, entity, memory_entry, auth_headers
    ):
        """Attaching the same entity twice to the same memory must return 409."""
        payload = {
            "memory_entry_id": memory_entry["id"],
            "entity_id": entity["id"],
        }
        resp1 = client.post(
            f"{ENTITIES_API}/memory/{memory_entry['id']}/attach",
            json=payload,
            headers=auth_headers,
        )
        # First attachment may already exist from a previous test — either 201 or 409 is valid
        assert resp1.status_code in (201, 409)

        resp2 = client.post(
            f"{ENTITIES_API}/memory/{memory_entry['id']}/attach",
            json=payload,
            headers=auth_headers,
        )
        assert resp2.status_code == 409, resp2.text

    def test_mismatched_url_body_returns_400(
        self, client: TestClient, entity, memory_entry, auth_headers
    ):
        """memory_entry_id in body must match the URL path parameter."""
        resp = client.post(
            f"{ENTITIES_API}/memory/{memory_entry['id']}/attach",
            json={
                "memory_entry_id": str(uuid.uuid4()),  # Different UUID
                "entity_id": entity["id"],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_attach_without_auth_returns_401(
        self, client: TestClient, entity, memory_entry
    ):
        resp = client.post(
            f"{ENTITIES_API}/memory/{memory_entry['id']}/attach",
            json={"memory_entry_id": memory_entry["id"], "entity_id": entity["id"]},
        )
        assert resp.status_code == 401

    def test_list_entities_for_memory(
        self, client: TestClient, entity, memory_entry, auth_headers
    ):
        # Attach first
        client.post(
            f"{ENTITIES_API}/memory/{memory_entry['id']}/attach",
            json={"memory_entry_id": memory_entry["id"], "entity_id": entity["id"]},
            headers=auth_headers,
        )
        resp = client.get(
            f"{ENTITIES_API}/memory/{memory_entry['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        ids = [e["id"] for e in resp.json()]
        assert entity["id"] in ids

    def test_list_entities_for_empty_memory(
        self, client: TestClient, auth_headers, org
    ):
        mem = _make_memory(client, org["id"], auth_headers)
        resp = client.get(
            f"{ENTITIES_API}/memory/{mem['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []


class TestExtractEndpoint:
    def test_extract_returns_entities(self, client: TestClient, org, auth_headers):
        text = (
            "We merged PR-42 from feat/auth-service into main. "
            "The AuthService now uses PostgreSQL and JWT."
        )
        resp = client.post(
            f"{ENTITIES_API}/extract",
            json={"text": text, "organization_id": org["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        entities = resp.json()
        assert len(entities) > 0
        names = [e["name"] for e in entities]
        # Should extract PostgreSQL as a technology
        assert any("PostgreSQL" in n for n in names)

    def test_extract_without_auth_returns_401(self, client: TestClient, org):
        resp = client.post(
            f"{ENTITIES_API}/extract",
            json={"text": "Some text with PR-1", "organization_id": org["id"]},
        )
        assert resp.status_code == 401

    def test_extract_empty_text_returns_422(self, client: TestClient, org, auth_headers):
        resp = client.post(
            f"{ENTITIES_API}/extract",
            json={"text": "", "organization_id": org["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ===========================================================================
# Unit tests for deterministic extraction service
# ===========================================================================


class TestEntityExtraction:
    def test_extract_pr_hash_notation(self):
        results = extract_entities("Fixed the bug in #123")
        pr = [e for e in results if e.entity_type == EntityType.PULL_REQUEST]
        assert any(e.name == "PR-123" for e in pr)

    def test_extract_pr_prefix_notation(self):
        results = extract_entities("See PR-456 for the implementation")
        pr = [e for e in results if e.entity_type == EntityType.PULL_REQUEST]
        assert any(e.name == "PR-456" for e in pr)

    def test_extract_pr_gitlab_notation(self):
        results = extract_entities("Merged !789 into main")
        pr = [e for e in results if e.entity_type == EntityType.PULL_REQUEST]
        assert any(e.name == "PR-789" for e in pr)

    def test_extract_branch(self):
        results = extract_entities("Checkout feat/user-auth before building")
        branches = [e for e in results if e.entity_type == EntityType.BRANCH]
        assert any("feat/user-auth" in e.name for e in branches)

    def test_branch_normalised_to_lowercase(self):
        results = extract_entities("branch Fix/Critical-Bug is ready")
        branches = [e for e in results if e.entity_type == EntityType.BRANCH]
        assert any(e.name == "fix/critical-bug" for e in branches)

    def test_extract_python_file(self):
        results = extract_entities("Updated backend/app/services/entity.py")
        files = [e for e in results if e.entity_type == EntityType.FILE]
        assert any("entity.py" in e.name for e in files)

    def test_extract_api_endpoint(self):
        results = extract_entities("The route GET /api/v1/users returns a list")
        endpoints = [e for e in results if e.entity_type == EntityType.API_ENDPOINT]
        assert any("GET" in e.name and "/api/v1/users" in e.name for e in endpoints)

    def test_api_endpoint_method_uppercased(self):
        results = extract_entities("called post /api/v1/entities to create an entity")
        endpoints = [e for e in results if e.entity_type == EntityType.API_ENDPOINT]
        assert any(e.name.startswith("POST") for e in endpoints)

    def test_extract_technology(self):
        results = extract_entities("We use PostgreSQL and Redis for storage")
        techs = [e.name for e in results if e.entity_type == EntityType.TECHNOLOGY]
        assert "PostgreSQL" in techs
        assert "Redis" in techs

    def test_extract_service_name(self):
        results = extract_entities("The AuthService delegates to UserRepository")
        services = [e.name for e in results if e.entity_type == EntityType.SERVICE]
        assert "AuthService" in services
        assert "UserRepository" in services

    def test_deduplication(self):
        results = extract_entities("PR-100 was merged. Also see PR-100.")
        pr = [e for e in results if e.entity_type == EntityType.PULL_REQUEST]
        assert len(pr) == 1

    def test_empty_text_returns_empty(self):
        results = extract_entities("")
        assert results == []

    def test_no_entities_in_plain_text(self):
        results = extract_entities("The quick brown fox jumps over the lazy dog")
        # Should not produce PR, Branch, File, API_ENDPOINT results
        for e in results:
            assert e.entity_type not in (
                EntityType.PULL_REQUEST,
                EntityType.BRANCH,
                EntityType.API_ENDPOINT,
            )

    def test_multiple_types_extracted_together(self):
        text = (
            "feat/auth branch: added POST /api/v1/login. "
            "See PR-7. Uses JWT and PostgreSQL. "
            "Modified backend/app/api/v1/auth.py."
        )
        results = extract_entities(text)
        types_found = {e.entity_type for e in results}
        assert EntityType.BRANCH in types_found
        assert EntityType.PULL_REQUEST in types_found
        assert EntityType.TECHNOLOGY in types_found
        assert EntityType.FILE in types_found
        assert EntityType.API_ENDPOINT in types_found
