"""
Sprint 5.2 — Knowledge Graph Relationship Engine tests.

Covers:
* POST /api/v1/relationships/                           — create relationship (auth required)
* GET  /api/v1/relationships/{id}                       — get relationship
* GET  /api/v1/relationships/entity/{id}/outgoing       — list outgoing
* GET  /api/v1/relationships/entity/{id}/neighbors      — list neighbors (both directions)
* Duplicate relationship returns 409
* Self-loop returns 400
* Organisation isolation (relationships not visible across orgs)
* Invalid entity IDs return 409
* Unknown relationship ID returns 404
* Unauthenticated requests rejected
* Neighbor direction labelling (outgoing / incoming)
* Optional relationship_type filter on list endpoints
"""
import uuid

import pytest
from fastapi.testclient import TestClient

USERS_API = "/api/v1/users"
ORGS_API = "/api/v1/organizations"
AUTH_API = "/api/v1/auth/login"
ENTITIES_API = "/api/v1/entities"
REL_API = "/api/v1/relationships"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post(AUTH_API, data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _make_user_headers(client: TestClient) -> dict:
    password = "ValidPass123!"
    email = f"rel_user_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        f"{USERS_API}/",
        json={"full_name": "Rel Test User", "email": email, "password": password},
    )
    token = _login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


def _make_org(client: TestClient) -> dict:
    slug = f"rel-org-{uuid.uuid4().hex[:8]}"
    resp = client.post(f"{ORGS_API}/", json={"name": "Relationship Org", "slug": slug})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _make_entity(client: TestClient, org_id: str, headers: dict, name: str, etype: str = "SERVICE") -> dict:
    resp = client.post(
        f"{ENTITIES_API}/",
        json={"organization_id": org_id, "entity_type": etype, "name": name},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _make_relationship(
    client: TestClient,
    org_id: str,
    source_id: str,
    target_id: str,
    rel_type: str,
    headers: dict,
) -> dict:
    resp = client.post(
        f"{REL_API}/",
        json={
            "organization_id": org_id,
            "source_entity_id": source_id,
            "target_entity_id": target_id,
            "relationship_type": rel_type,
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def auth_headers(client: TestClient):
    return _make_user_headers(client)


@pytest.fixture()
def org(client: TestClient):
    return _make_org(client)


@pytest.fixture()
def entity_a(client: TestClient, org, auth_headers):
    return _make_entity(client, org["id"], auth_headers, "AuthService")


@pytest.fixture()
def entity_b(client: TestClient, org, auth_headers):
    return _make_entity(client, org["id"], auth_headers, "UserRepository")


@pytest.fixture()
def relationship(client: TestClient, org, entity_a, entity_b, auth_headers):
    return _make_relationship(
        client, org["id"], entity_a["id"], entity_b["id"], "DEPENDS_ON", auth_headers
    )


# ===========================================================================
# Create Relationship
# ===========================================================================

class TestCreateRelationship:
    def test_create_returns_201(self, relationship, entity_a, entity_b, org):
        assert "id" in relationship
        assert relationship["relationship_type"] == "DEPENDS_ON"
        assert relationship["source_entity_id"] == entity_a["id"]
        assert relationship["target_entity_id"] == entity_b["id"]
        assert relationship["organization_id"] == org["id"]
        assert relationship["created_at"] is not None

    def test_all_relationship_types_accepted(
        self, client: TestClient, org, auth_headers
    ):
        for rtype in ("REFERENCES", "IMPLEMENTS", "FIXES", "DEPENDS_ON",
                      "REVIEWED_BY", "RELATED_TO", "CAUSED_BY"):
            src = _make_entity(client, org["id"], auth_headers, f"src-{rtype.lower()}")
            tgt = _make_entity(client, org["id"], auth_headers, f"tgt-{rtype.lower()}")
            resp = client.post(
                f"{REL_API}/",
                json={
                    "organization_id": org["id"],
                    "source_entity_id": src["id"],
                    "target_entity_id": tgt["id"],
                    "relationship_type": rtype,
                },
                headers=auth_headers,
            )
            assert resp.status_code == 201, f"Failed for type {rtype}: {resp.text}"
            assert resp.json()["relationship_type"] == rtype

    def test_duplicate_relationship_returns_409(
        self, client: TestClient, relationship, org, entity_a, entity_b, auth_headers
    ):
        """Exact same (org, src, tgt, type) edge must be rejected with 409."""
        resp = client.post(
            f"{REL_API}/",
            json={
                "organization_id": org["id"],
                "source_entity_id": entity_a["id"],
                "target_entity_id": entity_b["id"],
                "relationship_type": "DEPENDS_ON",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 409, resp.text

    def test_same_pair_different_type_is_allowed(
        self, client: TestClient, org, entity_a, entity_b, auth_headers
    ):
        """Same source+target with a different relationship type is a distinct edge."""
        resp = client.post(
            f"{REL_API}/",
            json={
                "organization_id": org["id"],
                "source_entity_id": entity_a["id"],
                "target_entity_id": entity_b["id"],
                "relationship_type": "REFERENCES",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text

    def test_self_loop_returns_400(
        self, client: TestClient, org, entity_a, auth_headers
    ):
        """A relationship where source == target must be rejected with 400."""
        resp = client.post(
            f"{REL_API}/",
            json={
                "organization_id": org["id"],
                "source_entity_id": entity_a["id"],
                "target_entity_id": entity_a["id"],
                "relationship_type": "RELATED_TO",
            },
            headers=auth_headers,
        )
        assert resp.status_code in (400, 422), resp.text

    def test_invalid_entity_id_returns_409(
        self, client: TestClient, org, entity_a, auth_headers
    ):
        """Non-existent entity FK must produce 409."""
        resp = client.post(
            f"{REL_API}/",
            json={
                "organization_id": org["id"],
                "source_entity_id": entity_a["id"],
                "target_entity_id": str(uuid.uuid4()),
                "relationship_type": "FIXES",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 409, resp.text

    def test_invalid_relationship_type_returns_422(
        self, client: TestClient, org, entity_a, entity_b, auth_headers
    ):
        resp = client.post(
            f"{REL_API}/",
            json={
                "organization_id": org["id"],
                "source_entity_id": entity_a["id"],
                "target_entity_id": entity_b["id"],
                "relationship_type": "KNOWS",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422, resp.text

    def test_create_without_auth_returns_401(
        self, client: TestClient, org, entity_a, entity_b
    ):
        resp = client.post(
            f"{REL_API}/",
            json={
                "organization_id": org["id"],
                "source_entity_id": entity_a["id"],
                "target_entity_id": entity_b["id"],
                "relationship_type": "RELATED_TO",
            },
        )
        assert resp.status_code == 401


# ===========================================================================
# Get Relationship
# ===========================================================================

class TestGetRelationship:
    def test_get_by_id_returns_200(
        self, client: TestClient, relationship, auth_headers
    ):
        resp = client.get(
            f"{REL_API}/{relationship['id']}", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == relationship["id"]

    def test_unknown_id_returns_404(self, client: TestClient, auth_headers):
        resp = client.get(f"{REL_API}/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_without_auth_returns_401(self, client: TestClient, relationship):
        resp = client.get(f"{REL_API}/{relationship['id']}")
        assert resp.status_code == 401


# ===========================================================================
# List Outgoing Relationships
# ===========================================================================

class TestListOutgoing:
    def test_list_outgoing_contains_created(
        self, client: TestClient, relationship, entity_a, auth_headers
    ):
        resp = client.get(
            f"{REL_API}/entity/{entity_a['id']}/outgoing",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        ids = [r["id"] for r in resp.json()]
        assert relationship["id"] in ids

    def test_list_outgoing_target_is_empty(
        self, client: TestClient, relationship, entity_b, auth_headers
    ):
        """entity_b is only a target, so its outgoing list should be empty."""
        resp = client.get(
            f"{REL_API}/entity/{entity_b['id']}/outgoing",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_outgoing_filter_by_type(
        self, client: TestClient, org, entity_a, entity_b, auth_headers
    ):
        # Create a second relationship with a different type
        entity_c = _make_entity(client, org["id"], auth_headers, "PaymentService")
        _make_relationship(
            client, org["id"], entity_a["id"], entity_c["id"], "REFERENCES", auth_headers
        )
        resp = client.get(
            f"{REL_API}/entity/{entity_a['id']}/outgoing?relationship_type=REFERENCES",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        types = {r["relationship_type"] for r in resp.json()}
        assert types == {"REFERENCES"}

    def test_list_unknown_entity_returns_empty(
        self, client: TestClient, auth_headers
    ):
        resp = client.get(
            f"{REL_API}/entity/{uuid.uuid4()}/outgoing",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_without_auth_returns_401(
        self, client: TestClient, entity_a
    ):
        resp = client.get(f"{REL_API}/entity/{entity_a['id']}/outgoing")
        assert resp.status_code == 401


# ===========================================================================
# List Neighbors
# ===========================================================================

class TestListNeighbors:
    def test_source_sees_outgoing_neighbor(
        self, client: TestClient, relationship, entity_a, entity_b, org, auth_headers
    ):
        """entity_a → entity_b: entity_a's neighbor list must include entity_b as outgoing."""
        resp = client.get(
            f"{REL_API}/entity/{entity_a['id']}/neighbors"
            f"?organization_id={org['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        neighbors = resp.json()
        outgoing = [n for n in neighbors if n["direction"] == "outgoing"]
        assert any(n["entity"]["id"] == entity_b["id"] for n in outgoing)

    def test_target_sees_incoming_neighbor(
        self, client: TestClient, relationship, entity_a, entity_b, org, auth_headers
    ):
        """entity_b is the target: its neighbor list must show entity_a as incoming."""
        resp = client.get(
            f"{REL_API}/entity/{entity_b['id']}/neighbors"
            f"?organization_id={org['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        neighbors = resp.json()
        incoming = [n for n in neighbors if n["direction"] == "incoming"]
        assert any(n["entity"]["id"] == entity_a["id"] for n in incoming)

    def test_neighbors_include_relationship_metadata(
        self, client: TestClient, relationship, entity_a, org, auth_headers
    ):
        resp = client.get(
            f"{REL_API}/entity/{entity_a['id']}/neighbors"
            f"?organization_id={org['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        n = resp.json()[0]
        assert "entity" in n
        assert "relationship_type" in n
        assert "relationship_id" in n
        assert "direction" in n
        assert n["relationship_id"] == relationship["id"]

    def test_neighbor_filter_by_relationship_type(
        self, client: TestClient, org, entity_a, entity_b, auth_headers
    ):
        """Filter reduces neighbors to the requested relationship type only."""
        entity_c = _make_entity(client, org["id"], auth_headers, "NotificationService")
        _make_relationship(
            client, org["id"], entity_a["id"], entity_c["id"], "IMPLEMENTS", auth_headers
        )
        # Only DEPENDS_ON neighbors
        resp = client.get(
            f"{REL_API}/entity/{entity_a['id']}/neighbors"
            f"?organization_id={org['id']}&relationship_type=IMPLEMENTS",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        types = {n["relationship_type"] for n in resp.json()}
        assert types == {"IMPLEMENTS"}

    def test_isolated_entity_has_no_neighbors(
        self, client: TestClient, org, auth_headers
    ):
        isolated = _make_entity(client, org["id"], auth_headers, "IsolatedService")
        resp = client.get(
            f"{REL_API}/entity/{isolated['id']}/neighbors"
            f"?organization_id={org['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_organisation_isolation_in_neighbors(
        self, client: TestClient, relationship, entity_a, auth_headers
    ):
        """Querying with a different org_id must return no neighbors."""
        other_org = _make_org(client)
        resp = client.get(
            f"{REL_API}/entity/{entity_a['id']}/neighbors"
            f"?organization_id={other_org['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_neighbors_requires_organization_id(
        self, client: TestClient, entity_a, auth_headers
    ):
        """Missing organization_id query param must return 422."""
        resp = client.get(
            f"{REL_API}/entity/{entity_a['id']}/neighbors",
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_neighbors_without_auth_returns_401(
        self, client: TestClient, entity_a, org
    ):
        resp = client.get(
            f"{REL_API}/entity/{entity_a['id']}/neighbors"
            f"?organization_id={org['id']}"
        )
        assert resp.status_code == 401

    def test_bidirectional_visibility(
        self, client: TestClient, org, auth_headers
    ):
        """An entity that is both source and target of different edges sees both."""
        hub = _make_entity(client, org["id"], auth_headers, "HubService")
        spoke1 = _make_entity(client, org["id"], auth_headers, "Spoke1Service")
        spoke2 = _make_entity(client, org["id"], auth_headers, "Spoke2Service")
        # hub → spoke1 (outgoing)
        _make_relationship(
            client, org["id"], hub["id"], spoke1["id"], "DEPENDS_ON", auth_headers
        )
        # spoke2 → hub (incoming to hub)
        _make_relationship(
            client, org["id"], spoke2["id"], hub["id"], "REFERENCES", auth_headers
        )
        resp = client.get(
            f"{REL_API}/entity/{hub['id']}/neighbors?organization_id={org['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        neighbors = resp.json()
        directions = {n["direction"] for n in neighbors}
        assert "outgoing" in directions
        assert "incoming" in directions
        entity_ids = {n["entity"]["id"] for n in neighbors}
        assert spoke1["id"] in entity_ids
        assert spoke2["id"] in entity_ids
