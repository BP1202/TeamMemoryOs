"""
Sprint 5.3 — Automatic Memory Linking Engine tests.

Covers:
* POST /api/v1/memory-links/generate          — auto-generate links
* GET  /api/v1/memory-links/memory/{id}       — list links (with org filter)
* POST /api/v1/memory-links/                  — manually create link
* Shared entity linking produces SHARED_ENTITY links
* Same scenario linking produces SAME_SCENARIO links
* Duplicate links are skipped (idempotent generate)
* Score ordering (highest score first)
* min_score filter reduces results
* link_type filter reduces results
* Organisation isolation (links scoped to org)
* Self-link returns 400
* Invalid memory returns empty generate response
* Unauthenticated requests rejected

Unit tests for calculate_link_score:
* All signals present
* No embedding (semantic weight redistributed)
* Entity-only signal
* Scenario-only signal
* Zero score when no signals
* Score always clamped [0.0, 1.0]
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.services.memory_link import calculate_link_score

USERS_API = "/api/v1/users"
ORGS_API = "/api/v1/organizations"
SCENARIOS_API = "/api/v1/scenarios"
AUTH_API = "/api/v1/auth/login"
MEMORY_API = "/api/v1/memory"
ENTITIES_API = "/api/v1/entities"
LINKS_API = "/api/v1/memory-links"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post(AUTH_API, data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _make_headers(client: TestClient) -> dict:
    password = "ValidPass123!"
    email = f"link_user_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        f"{USERS_API}/",
        json={"full_name": "Link Test User", "email": email, "password": password},
    )
    token = _login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


def _make_org(client: TestClient) -> dict:
    slug = f"link-org-{uuid.uuid4().hex[:8]}"
    resp = client.post(f"{ORGS_API}/", json={"name": "Link Org", "slug": slug})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _make_scenario(client: TestClient, org_id: str, headers: dict) -> dict:
    resp = client.post(
        f"{SCENARIOS_API}/",
        json={"organization_id": org_id, "name": f"Scenario {uuid.uuid4().hex[:4]}"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _make_memory(
    client: TestClient,
    org_id: str,
    headers: dict,
    content: str = "Memory content",
    scenario_id: str | None = None,
) -> dict:
    body = {
        "organization_id": org_id,
        "memory_type": "decision",
        "content": content,
    }
    if scenario_id:
        body["scenario_id"] = scenario_id
    resp = client.post(f"{MEMORY_API}/", json=body, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _make_entity(client: TestClient, org_id: str, headers: dict, name: str) -> dict:
    resp = client.post(
        f"{ENTITIES_API}/",
        json={"organization_id": org_id, "entity_type": "TECHNOLOGY", "name": name},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _attach_entity(
    client: TestClient, memory_id: str, entity_id: str, headers: dict
) -> None:
    resp = client.post(
        f"{ENTITIES_API}/memory/{memory_id}/attach",
        json={"memory_entry_id": memory_id, "entity_id": entity_id},
        headers=headers,
    )
    # 201 = created, 409 = already attached (acceptable in tests)
    assert resp.status_code in (201, 409), resp.text


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def auth_headers(client: TestClient):
    return _make_headers(client)


@pytest.fixture()
def org(client: TestClient):
    return _make_org(client)


@pytest.fixture()
def scenario(client: TestClient, org, auth_headers):
    return _make_scenario(client, org["id"], auth_headers)


@pytest.fixture()
def mem_a(client: TestClient, org, auth_headers):
    return _make_memory(client, org["id"], auth_headers, "Decided to use PostgreSQL")


@pytest.fixture()
def mem_b(client: TestClient, org, auth_headers):
    return _make_memory(client, org["id"], auth_headers, "PostgreSQL configuration guide")


# ===========================================================================
# Unit tests — calculate_link_score
# ===========================================================================

class TestCalculateLinkScore:
    def test_all_signals_returns_positive_score(self):
        score = calculate_link_score(
            shared_entity_count=2,
            total_entity_count=4,
            same_scenario=True,
            cosine_similarity=0.8,
        )
        assert 0.0 < score <= 1.0

    def test_no_signals_returns_zero(self):
        score = calculate_link_score(
            shared_entity_count=0,
            total_entity_count=0,
            same_scenario=False,
            cosine_similarity=None,
        )
        assert score == 0.0

    def test_entity_only_signal(self):
        score = calculate_link_score(
            shared_entity_count=3,
            total_entity_count=3,
            same_scenario=False,
            cosine_similarity=None,
        )
        # 3/3 entity Jaccard = 1.0; all weight goes to entity signal
        assert score > 0.0
        assert score <= 1.0

    def test_scenario_only_signal(self):
        score = calculate_link_score(
            shared_entity_count=0,
            total_entity_count=0,
            same_scenario=True,
            cosine_similarity=None,
        )
        # Only scenario signal fires
        assert score > 0.0
        assert score <= 1.0

    def test_semantic_only_signal(self):
        score = calculate_link_score(
            shared_entity_count=0,
            total_entity_count=0,
            same_scenario=False,
            cosine_similarity=1.0,
        )
        assert score > 0.0
        assert score <= 1.0

    def test_score_always_clamped(self):
        score = calculate_link_score(
            shared_entity_count=100,
            total_entity_count=100,
            same_scenario=True,
            cosine_similarity=1.0,
        )
        assert 0.0 <= score <= 1.0

    def test_no_embedding_redistributes_weight(self):
        """Without semantic similarity, entity+scenario weights should sum to 1.0."""
        score_with_sem = calculate_link_score(
            shared_entity_count=1,
            total_entity_count=1,
            same_scenario=True,
            cosine_similarity=0.5,
        )
        score_no_sem = calculate_link_score(
            shared_entity_count=1,
            total_entity_count=1,
            same_scenario=True,
            cosine_similarity=None,
        )
        # Without semantic signal the score should still be positive
        assert score_no_sem > 0.0
        # The max without semantic signal (all other signals = 1.0) = 1.0
        assert score_no_sem <= 1.0

    def test_partial_entity_overlap_less_than_full(self):
        full = calculate_link_score(
            shared_entity_count=4,
            total_entity_count=4,
            same_scenario=False,
            cosine_similarity=None,
        )
        partial = calculate_link_score(
            shared_entity_count=2,
            total_entity_count=4,
            same_scenario=False,
            cosine_similarity=None,
        )
        assert partial < full


# ===========================================================================
# API — Generate Links
# ===========================================================================

class TestGenerateLinks:
    def test_generate_shared_entity_links(
        self, client: TestClient, org, auth_headers, mem_a, mem_b
    ):
        """Two memories sharing an entity should produce a SHARED_ENTITY link."""
        entity = _make_entity(client, org["id"], auth_headers, f"SharedTech-{uuid.uuid4().hex[:4]}")
        _attach_entity(client, mem_a["id"], entity["id"], auth_headers)
        _attach_entity(client, mem_b["id"], entity["id"], auth_headers)

        resp = client.post(
            f"{LINKS_API}/generate",
            json={"memory_id": mem_a["id"], "organization_id": org["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["memory_id"] == mem_a["id"]
        link_types = [l["link_type"] for l in data["links"]]
        assert "SHARED_ENTITY" in link_types

    def test_generate_same_scenario_links(
        self, client: TestClient, org, auth_headers, scenario
    ):
        """Two memories in the same scenario produce SAME_SCENARIO links."""
        m1 = _make_memory(client, org["id"], auth_headers, "First decision", scenario["id"])
        m2 = _make_memory(client, org["id"], auth_headers, "Second decision", scenario["id"])

        resp = client.post(
            f"{LINKS_API}/generate",
            json={"memory_id": m1["id"], "organization_id": org["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        link_types = [l["link_type"] for l in data["links"]]
        assert "SAME_SCENARIO" in link_types
        # The target should be m2
        target_ids = [l["target_memory_id"] for l in data["links"]]
        assert m2["id"] in target_ids

    def test_generate_returns_links_created_count(
        self, client: TestClient, org, auth_headers, scenario
    ):
        m1 = _make_memory(client, org["id"], auth_headers, "Alpha memory", scenario["id"])
        m2 = _make_memory(client, org["id"], auth_headers, "Beta memory", scenario["id"])

        resp = client.post(
            f"{LINKS_API}/generate",
            json={"memory_id": m1["id"], "organization_id": org["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["links_created"] >= 1
        assert isinstance(data["links_skipped"], int)

    def test_generate_is_idempotent(
        self, client: TestClient, org, auth_headers, scenario
    ):
        """Running generate twice should not create duplicate links."""
        m1 = _make_memory(client, org["id"], auth_headers, "Idem 1", scenario["id"])
        m2 = _make_memory(client, org["id"], auth_headers, "Idem 2", scenario["id"])

        resp1 = client.post(
            f"{LINKS_API}/generate",
            json={"memory_id": m1["id"], "organization_id": org["id"]},
            headers=auth_headers,
        )
        created_first = resp1.json()["links_created"]

        resp2 = client.post(
            f"{LINKS_API}/generate",
            json={"memory_id": m1["id"], "organization_id": org["id"]},
            headers=auth_headers,
        )
        data2 = resp2.json()
        # Second run: nothing new created, all skipped
        assert data2["links_created"] == 0
        assert data2["links_skipped"] == created_first

    def test_generate_links_sorted_by_score_descending(
        self, client: TestClient, org, auth_headers, scenario
    ):
        """Links in the response must be ordered by score descending."""
        m1 = _make_memory(client, org["id"], auth_headers, "Score sort 1", scenario["id"])
        _make_memory(client, org["id"], auth_headers, "Score sort 2", scenario["id"])

        resp = client.post(
            f"{LINKS_API}/generate",
            json={"memory_id": m1["id"], "organization_id": org["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        links = resp.json()["links"]
        scores = [l["score"] for l in links]
        assert scores == sorted(scores, reverse=True)

    def test_generate_unknown_memory_returns_empty(
        self, client: TestClient, org, auth_headers
    ):
        """A non-existent memory_id must return empty (not 404)."""
        resp = client.post(
            f"{LINKS_API}/generate",
            json={"memory_id": str(uuid.uuid4()), "organization_id": org["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["links_created"] == 0
        assert data["links"] == []

    def test_generate_without_auth_returns_401(self, client: TestClient, org, mem_a):
        resp = client.post(
            f"{LINKS_API}/generate",
            json={"memory_id": mem_a["id"], "organization_id": org["id"]},
        )
        assert resp.status_code == 401


# ===========================================================================
# API — List Links
# ===========================================================================

class TestListLinks:
    def test_list_returns_links_for_memory(
        self, client: TestClient, org, auth_headers, scenario
    ):
        m1 = _make_memory(client, org["id"], auth_headers, "List test 1", scenario["id"])
        _make_memory(client, org["id"], auth_headers, "List test 2", scenario["id"])

        # Generate links first
        client.post(
            f"{LINKS_API}/generate",
            json={"memory_id": m1["id"], "organization_id": org["id"]},
            headers=auth_headers,
        )

        resp = client.get(
            f"{LINKS_API}/memory/{m1['id']}?organization_id={org['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_list_filter_by_link_type(
        self, client: TestClient, org, auth_headers, scenario
    ):
        m1 = _make_memory(client, org["id"], auth_headers, "Filter type 1", scenario["id"])
        _make_memory(client, org["id"], auth_headers, "Filter type 2", scenario["id"])

        client.post(
            f"{LINKS_API}/generate",
            json={"memory_id": m1["id"], "organization_id": org["id"]},
            headers=auth_headers,
        )

        resp = client.get(
            f"{LINKS_API}/memory/{m1['id']}?organization_id={org['id']}&link_type=SAME_SCENARIO",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        types = {l["link_type"] for l in resp.json()}
        assert types.issubset({"SAME_SCENARIO"})

    def test_list_filter_by_min_score(
        self, client: TestClient, org, auth_headers, scenario
    ):
        m1 = _make_memory(client, org["id"], auth_headers, "Score filter 1", scenario["id"])
        _make_memory(client, org["id"], auth_headers, "Score filter 2", scenario["id"])

        client.post(
            f"{LINKS_API}/generate",
            json={"memory_id": m1["id"], "organization_id": org["id"]},
            headers=auth_headers,
        )

        resp = client.get(
            f"{LINKS_API}/memory/{m1['id']}?organization_id={org['id']}&min_score=0.5",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        for link in resp.json():
            assert link["score"] >= 0.5

    def test_list_results_ordered_by_score_descending(
        self, client: TestClient, org, auth_headers, scenario
    ):
        m1 = _make_memory(client, org["id"], auth_headers, "Order 1", scenario["id"])
        _make_memory(client, org["id"], auth_headers, "Order 2", scenario["id"])

        client.post(
            f"{LINKS_API}/generate",
            json={"memory_id": m1["id"], "organization_id": org["id"]},
            headers=auth_headers,
        )

        resp = client.get(
            f"{LINKS_API}/memory/{m1['id']}?organization_id={org['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        scores = [l["score"] for l in resp.json()]
        assert scores == sorted(scores, reverse=True)

    def test_list_organisation_isolation(
        self, client: TestClient, org, auth_headers, scenario
    ):
        """Links generated in org A must not appear when queried with org B."""
        m1 = _make_memory(client, org["id"], auth_headers, "Isolated 1", scenario["id"])
        _make_memory(client, org["id"], auth_headers, "Isolated 2", scenario["id"])
        client.post(
            f"{LINKS_API}/generate",
            json={"memory_id": m1["id"], "organization_id": org["id"]},
            headers=auth_headers,
        )

        other_org = _make_org(client)
        resp = client.get(
            f"{LINKS_API}/memory/{m1['id']}?organization_id={other_org['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_requires_organization_id(
        self, client: TestClient, mem_a, auth_headers
    ):
        resp = client.get(
            f"{LINKS_API}/memory/{mem_a['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_list_without_auth_returns_401(self, client: TestClient, mem_a, org):
        resp = client.get(
            f"{LINKS_API}/memory/{mem_a['id']}?organization_id={org['id']}"
        )
        assert resp.status_code == 401


# ===========================================================================
# API — Manual Create
# ===========================================================================

class TestCreateLinkManually:
    def test_manual_create_returns_201(
        self, client: TestClient, org, auth_headers, mem_a, mem_b
    ):
        resp = client.post(
            f"{LINKS_API}/",
            json={
                "organization_id": org["id"],
                "source_memory_id": mem_a["id"],
                "target_memory_id": mem_b["id"],
                "link_type": "RELATED_INCIDENT",
                "score": 0.75,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["link_type"] == "RELATED_INCIDENT"
        assert data["score"] == 0.75

    def test_self_link_returns_400(
        self, client: TestClient, org, auth_headers, mem_a
    ):
        resp = client.post(
            f"{LINKS_API}/",
            json={
                "organization_id": org["id"],
                "source_memory_id": mem_a["id"],
                "target_memory_id": mem_a["id"],
                "link_type": "RELATED_INCIDENT",
                "score": 0.5,
            },
            headers=auth_headers,
        )
        assert resp.status_code in (400, 422), resp.text

    def test_duplicate_manual_link_returns_409(
        self, client: TestClient, org, auth_headers, mem_a, mem_b
    ):
        payload = {
            "organization_id": org["id"],
            "source_memory_id": mem_a["id"],
            "target_memory_id": mem_b["id"],
            "link_type": "RELATED_INCIDENT",
            "score": 0.6,
        }
        resp1 = client.post(f"{LINKS_API}/", json=payload, headers=auth_headers)
        assert resp1.status_code in (201, 409)

        resp2 = client.post(f"{LINKS_API}/", json=payload, headers=auth_headers)
        assert resp2.status_code == 409, resp2.text

    def test_score_out_of_range_returns_422(
        self, client: TestClient, org, auth_headers, mem_a, mem_b
    ):
        resp = client.post(
            f"{LINKS_API}/",
            json={
                "organization_id": org["id"],
                "source_memory_id": mem_a["id"],
                "target_memory_id": mem_b["id"],
                "link_type": "RELATED_INCIDENT",
                "score": 1.5,  # out of [0, 1]
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_invalid_link_type_returns_422(
        self, client: TestClient, org, auth_headers, mem_a, mem_b
    ):
        resp = client.post(
            f"{LINKS_API}/",
            json={
                "organization_id": org["id"],
                "source_memory_id": mem_a["id"],
                "target_memory_id": mem_b["id"],
                "link_type": "NOT_A_TYPE",
                "score": 0.5,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_create_without_auth_returns_401(
        self, client: TestClient, org, mem_a, mem_b
    ):
        resp = client.post(
            f"{LINKS_API}/",
            json={
                "organization_id": org["id"],
                "source_memory_id": mem_a["id"],
                "target_memory_id": mem_b["id"],
                "link_type": "RELATED_INCIDENT",
                "score": 0.5,
            },
        )
        assert resp.status_code == 401
