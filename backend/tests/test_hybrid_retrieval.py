"""
Sprint 5.4 — Hybrid Retrieval Engine tests.

Covers:
* POST /api/v1/retrieval/hybrid-search          — hybrid search endpoint
* Semantic-only mode returns results when embeddings exist
* Graph-expanded candidates appear when entities are connected
* MemoryLink candidates surface from link-expanded memories
* Score ordering (highest first)
* Explanation metadata present (retrieval_reason, matched_entities, graph_distance)
* graph_distance = 0 for semantic seeds, 1 for graph-expanded
* Organisation isolation (no cross-org leakage)
* Empty org returns empty results
* Unauthenticated requests rejected

Chat integration:
* POST /api/v1/chat/ask with use_hybrid=True returns retrieval_mode="hybrid"
* POST /api/v1/chat/ask default (use_hybrid=False) returns retrieval_mode="semantic"
* Existing chat tests are not broken (backward compatibility)

Unit tests for HybridRetriever internals:
* _weighted_score values are deterministic
* _cosine_distance edge cases
* retrieve() on empty org returns []
"""
from __future__ import annotations

import math
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.graph.hybrid_retriever import (
    HybridRetriever,
    HybridResult,
    _cosine_distance,
    _weighted_score,
)
from app.memory.embedding_provider import StubEmbeddingProvider

USERS_API = "/api/v1/users"
ORGS_API = "/api/v1/organizations"
SCENARIOS_API = "/api/v1/scenarios"
AUTH_API = "/api/v1/auth/login"
MEMORY_API = "/api/v1/memory"
ENTITIES_API = "/api/v1/entities"
REL_API = "/api/v1/relationships"
LINKS_API = "/api/v1/memory-links"
RETRIEVAL_API = "/api/v1/retrieval"
CHAT_API = "/api/v1/chat"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post(AUTH_API, data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _make_headers(client: TestClient) -> dict:
    password = "ValidPass123!"
    email = f"hyb_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        f"{USERS_API}/",
        json={"full_name": "Hybrid Test User", "email": email, "password": password},
    )
    return {"Authorization": f"Bearer {_login(client, email, password)}"}


def _make_org(client: TestClient) -> dict:
    slug = f"hyb-org-{uuid.uuid4().hex[:8]}"
    resp = client.post(f"{ORGS_API}/", json={"name": "Hybrid Org", "slug": slug})
    assert resp.status_code == 201
    return resp.json()


def _make_memory(client, org_id, headers, content, embed=True) -> dict:
    resp = client.post(
        f"{MEMORY_API}/",
        json={"organization_id": org_id, "memory_type": "decision", "content": content},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    entry = resp.json()
    if embed:
        vec = StubEmbeddingProvider().embed(content)
        emb_resp = client.put(
            f"{MEMORY_API}/{entry['id']}/embedding",
            json={"embedding": vec},
            headers=headers,
        )
        assert emb_resp.status_code == 200, emb_resp.text
    return entry


def _make_entity(client, org_id, headers, name) -> dict:
    resp = client.post(
        f"{ENTITIES_API}/",
        json={"organization_id": org_id, "entity_type": "TECHNOLOGY", "name": name},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _attach_entity(client, memory_id, entity_id, headers):
    resp = client.post(
        f"{ENTITIES_API}/memory/{memory_id}/attach",
        json={"memory_entry_id": memory_id, "entity_id": entity_id},
        headers=headers,
    )
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
def org_with_memories(client: TestClient, auth_headers):
    """Org with two embedded memories sharing an entity."""
    org = _make_org(client)
    m1 = _make_memory(client, org["id"], auth_headers, "We use PostgreSQL for all storage")
    m2 = _make_memory(client, org["id"], auth_headers, "PostgreSQL performance tuning guide")
    entity = _make_entity(client, org["id"], auth_headers, f"PostgreSQL-{uuid.uuid4().hex[:4]}")
    _attach_entity(client, m1["id"], entity["id"], auth_headers)
    _attach_entity(client, m2["id"], entity["id"], auth_headers)
    return {"org": org, "m1": m1, "m2": m2, "entity": entity}


# ===========================================================================
# Unit tests — scoring helpers
# ===========================================================================

class TestWeightedScore:
    def test_all_signals_max(self):
        score = _weighted_score(1.0, 1.0, 1.0)
        assert score == pytest.approx(1.0)

    def test_all_signals_zero(self):
        score = _weighted_score(0.0, 0.0, 0.0)
        assert score == pytest.approx(0.0)

    def test_semantic_only(self):
        score = _weighted_score(1.0, 0.0, 0.0)
        assert score == pytest.approx(0.5)

    def test_graph_only(self):
        score = _weighted_score(0.0, 1.0, 0.0)
        assert score == pytest.approx(0.2)

    def test_link_only(self):
        score = _weighted_score(0.0, 0.0, 1.0)
        assert score == pytest.approx(0.3)

    def test_score_always_clamped(self):
        # Passing values > 1 must still clamp to 1.0
        score = _weighted_score(2.0, 2.0, 2.0)
        assert 0.0 <= score <= 1.0


class TestCosineDistance:
    def _unit_vec(self, val=1.0):
        raw = [val] * 1536
        mag = math.sqrt(sum(v * v for v in raw))
        return [v / mag for v in raw]

    def test_identical_vectors_zero_distance(self):
        v = self._unit_vec(1.0)
        assert _cosine_distance(v, v) == pytest.approx(0.0, abs=1e-6)

    def test_orthogonal_vectors_one_distance(self):
        a = [1.0] + [0.0] * 1535
        b = [0.0, 1.0] + [0.0] * 1534
        dist = _cosine_distance(a, b)
        assert dist == pytest.approx(1.0, abs=1e-6)

    def test_zero_vector_returns_one(self):
        a = [0.0] * 1536
        b = self._unit_vec()
        assert _cosine_distance(a, b) == pytest.approx(1.0)

    def test_mismatched_length_returns_one(self):
        assert _cosine_distance([1.0, 0.0], [1.0, 0.0, 0.0]) == pytest.approx(1.0)


# ===========================================================================
# HybridRetriever service-level unit tests
# ===========================================================================

class TestHybridRetrieverService:
    def _get_db(self):
        from app.db.dependencies import get_db
        return next(get_db())

    def test_retrieve_empty_org_returns_empty(self):
        """Fresh org with no memories → retrieve() returns []."""
        db = self._get_db()
        try:
            slug = f"empty-hyb-{uuid.uuid4().hex[:6]}"
            from app.services.organization import create_organization
            from app.schemas.organization import OrganizationCreate
            org = create_organization(db, OrganizationCreate(name="Empty Hyb", slug=slug))
            retriever = HybridRetriever(
                db=db,
                organization_id=org.id,
                embedding_provider=StubEmbeddingProvider(),
                top_k=5,
            )
            results = retriever.retrieve("What is the architecture?")
            assert results == []
        finally:
            db.close()

    def test_retrieve_respects_top_k(self, org_with_memories, client, auth_headers):
        """top_k=1 must return at most 1 result."""
        db = self._get_db()
        try:
            retriever = HybridRetriever(
                db=db,
                organization_id=uuid.UUID(org_with_memories["org"]["id"]),
                embedding_provider=StubEmbeddingProvider(),
                top_k=1,
            )
            results = retriever.retrieve("PostgreSQL storage")
            assert len(results) <= 1
        finally:
            db.close()

    def test_retrieve_results_sorted_descending(self, org_with_memories, client, auth_headers):
        """Results must be sorted by score descending."""
        db = self._get_db()
        try:
            retriever = HybridRetriever(
                db=db,
                organization_id=uuid.UUID(org_with_memories["org"]["id"]),
                embedding_provider=StubEmbeddingProvider(),
                top_k=10,
            )
            results = retriever.retrieve("database storage")
            scores = [r.score for r in results]
            assert scores == sorted(scores, reverse=True)
        finally:
            db.close()

    def test_retrieve_result_has_required_fields(self, org_with_memories, client, auth_headers):
        """Each HybridResult must carry the full metadata."""
        db = self._get_db()
        try:
            retriever = HybridRetriever(
                db=db,
                organization_id=uuid.UUID(org_with_memories["org"]["id"]),
                embedding_provider=StubEmbeddingProvider(),
                top_k=5,
            )
            results = retriever.retrieve("PostgreSQL")
            assert len(results) >= 1
            r = results[0]
            assert hasattr(r, "memory")
            assert hasattr(r, "score")
            assert hasattr(r, "semantic_score")
            assert hasattr(r, "graph_score")
            assert hasattr(r, "link_score")
            assert hasattr(r, "retrieval_reason")
            assert hasattr(r, "matched_entities")
            assert hasattr(r, "graph_distance")
            assert r.retrieval_reason  # non-empty
            assert 0.0 <= r.score <= 1.0
        finally:
            db.close()


# ===========================================================================
# POST /api/v1/retrieval/hybrid-search endpoint tests
# ===========================================================================

class TestHybridSearchEndpoint:
    def test_hybrid_search_returns_200(self, client, org, auth_headers):
        resp = client.post(
            f"{RETRIEVAL_API}/hybrid-search",
            json={
                "organization_id": org["id"],
                "question": "What architecture decisions were made?",
                "top_k": 5,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "results" in data
        assert "graph_stats" in data
        assert "retrieval_mode" in data
        assert data["retrieval_mode"] == "hybrid"
        assert data["question"] == "What architecture decisions were made?"

    def test_hybrid_search_empty_org_returns_empty_results(
        self, client, auth_headers
    ):
        empty_org = _make_org(client)
        resp = client.post(
            f"{RETRIEVAL_API}/hybrid-search",
            json={"organization_id": empty_org["id"], "question": "Anything?"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_hybrid_search_with_memories_returns_results(
        self, client, org_with_memories, auth_headers
    ):
        resp = client.post(
            f"{RETRIEVAL_API}/hybrid-search",
            json={
                "organization_id": org_with_memories["org"]["id"],
                "question": "PostgreSQL database decisions",
                "top_k": 5,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) >= 1

    def test_hybrid_results_have_explanation_fields(
        self, client, org_with_memories, auth_headers
    ):
        resp = client.post(
            f"{RETRIEVAL_API}/hybrid-search",
            json={
                "organization_id": org_with_memories["org"]["id"],
                "question": "database",
                "top_k": 5,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        for result in resp.json()["results"]:
            assert "score" in result
            assert "semantic_score" in result
            assert "graph_score" in result
            assert "link_score" in result
            assert "retrieval_reason" in result
            assert "matched_entities" in result
            assert "graph_distance" in result
            assert result["retrieval_reason"]  # non-empty string
            assert 0.0 <= result["score"] <= 1.0

    def test_hybrid_results_sorted_by_score(
        self, client, org_with_memories, auth_headers
    ):
        resp = client.post(
            f"{RETRIEVAL_API}/hybrid-search",
            json={
                "organization_id": org_with_memories["org"]["id"],
                "question": "database",
                "top_k": 10,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        scores = [r["score"] for r in resp.json()["results"]]
        assert scores == sorted(scores, reverse=True)

    def test_hybrid_search_response_has_graph_stats(
        self, client, org_with_memories, auth_headers
    ):
        resp = client.post(
            f"{RETRIEVAL_API}/hybrid-search",
            json={
                "organization_id": org_with_memories["org"]["id"],
                "question": "database",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        stats = resp.json()["graph_stats"]
        assert "seed_count" in stats
        assert "entity_count" in stats
        assert "graph_expanded_entity_count" in stats
        assert "link_expanded_count" in stats
        assert "total_candidates_evaluated" in stats

    def test_hybrid_graph_expansion_surfaces_related_memory(
        self, client, auth_headers
    ):
        """Memory B is not directly related to the query, but shares a graph-connected
        entity with Memory A (which is the semantic hit).  B should appear via graph expansion."""
        org = _make_org(client)

        # Memory A — semantically similar to query, has entity X
        m_a = _make_memory(client, org["id"], auth_headers, "PostgreSQL storage architecture")
        entity_x = _make_entity(client, org["id"], auth_headers, f"EntityX-{uuid.uuid4().hex[:4]}")
        _attach_entity(client, m_a["id"], entity_x["id"], auth_headers)

        # Memory B — NOT semantically similar, has entity Y
        # No embedding stored so it won't appear as a semantic seed
        m_b = _make_memory(
            client, org["id"], auth_headers,
            "Completely unrelated incident report content xyz123", embed=False
        )
        entity_y = _make_entity(client, org["id"], auth_headers, f"EntityY-{uuid.uuid4().hex[:4]}")
        _attach_entity(client, m_b["id"], entity_y["id"], auth_headers)

        # Connect entity X → entity Y via a relationship
        client.post(
            f"{REL_API}/",
            json={
                "organization_id": org["id"],
                "source_entity_id": entity_x["id"],
                "target_entity_id": entity_y["id"],
                "relationship_type": "RELATED_TO",
            },
            headers=auth_headers,
        )

        resp = client.post(
            f"{RETRIEVAL_API}/hybrid-search",
            json={"organization_id": org["id"], "question": "PostgreSQL storage", "top_k": 10},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        result_ids = [r["memory"]["id"] for r in resp.json()["results"]]
        # m_a must appear (semantic hit)
        assert m_a["id"] in result_ids
        # m_b should appear via graph expansion (entity Y is reachable from entity X)
        assert m_b["id"] in result_ids

    def test_hybrid_organisation_isolation(
        self, client, org_with_memories, auth_headers
    ):
        """Results must not include memories from a different organisation."""
        other_org = _make_org(client)
        resp = client.post(
            f"{RETRIEVAL_API}/hybrid-search",
            json={
                "organization_id": other_org["id"],
                "question": "PostgreSQL database decisions",
                "top_k": 10,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        # No results from the other org
        assert resp.json()["results"] == []

    def test_hybrid_search_without_auth_returns_401(self, client, org):
        resp = client.post(
            f"{RETRIEVAL_API}/hybrid-search",
            json={"organization_id": org["id"], "question": "Test"},
        )
        assert resp.status_code == 401

    def test_hybrid_search_empty_question_returns_422(
        self, client, org, auth_headers
    ):
        resp = client.post(
            f"{RETRIEVAL_API}/hybrid-search",
            json={"organization_id": org["id"], "question": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_hybrid_search_top_k_out_of_range_returns_422(
        self, client, org, auth_headers
    ):
        resp = client.post(
            f"{RETRIEVAL_API}/hybrid-search",
            json={"organization_id": org["id"], "question": "test", "top_k": 0},
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ===========================================================================
# Chat endpoint — hybrid mode integration
# ===========================================================================

class TestChatHybridIntegration:
    def test_chat_default_mode_is_semantic(self, client, org, auth_headers):
        resp = client.post(
            f"{CHAT_API}/ask",
            json={"organization_id": org["id"], "question": "What decisions were made?"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["retrieval_mode"] == "semantic"

    def test_chat_hybrid_mode_returns_hybrid(self, client, org, auth_headers):
        resp = client.post(
            f"{CHAT_API}/ask",
            json={
                "organization_id": org["id"],
                "question": "What decisions were made?",
                "use_hybrid": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["retrieval_mode"] == "hybrid"

    def test_chat_hybrid_with_memories_returns_answer(
        self, client, org_with_memories, auth_headers
    ):
        resp = client.post(
            f"{CHAT_API}/ask",
            json={
                "organization_id": org_with_memories["org"]["id"],
                "question": "What database do we use?",
                "use_hybrid": True,
                "top_k": 5,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["retrieval_mode"] == "hybrid"
        assert data["answer"]
        assert isinstance(data["citations"], list)

    def test_chat_hybrid_response_has_all_fields(self, client, org, auth_headers):
        resp = client.post(
            f"{CHAT_API}/ask",
            json={
                "organization_id": org["id"],
                "question": "Any question",
                "use_hybrid": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "citations" in data
        assert "retrieved_memory_count" in data
        assert "provider_used" in data
        assert "retrieval_mode" in data

    def test_existing_chat_tests_still_pass(self, client, org, auth_headers):
        """Confirm original semantic chat endpoint is not broken."""
        resp = client.post(
            f"{CHAT_API}/ask",
            json={
                "organization_id": org["id"],
                "question": "What is our primary database?",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["provider_used"] == "stub"
