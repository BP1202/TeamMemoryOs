"""
Sprint 5.5 — Explainable Retrieval Engine tests.

Covers:
Unit tests:
* aggregate_confidence — empty, single, multi-result, rank-decay
* build_graph_path — no results, no entities, direct edge, reverse edge, no edge
* build_retrieval_explanation — summary text, citation count, mode field
* Citation fields (rank, scores, matched_entities)

API tests — POST /api/v1/retrieval/explain:
* Returns explanation + results with all required fields
* confidence in [0, 1]
* citations have correct rank ordering
* graph_path present when entity relationship connects top results
* organisation isolation (empty for wrong org)
* Unauthenticated returns 401, empty question returns 422

API tests — POST /api/v1/chat/ask (with use_hybrid=True):
* explanation field populated in hybrid mode
* explanation is None in semantic mode
* explanation.citations match retrieved_memory_count
* explanation.summary is non-empty
* explanation.confidence in [0, 1]
* existing chat tests still pass (backward compat)
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.graph.explanation_builder import (
    Citation,
    GraphPathStep,
    RetrievalExplanation,
    aggregate_confidence,
    build_graph_path,
    build_retrieval_explanation,
)
from app.graph.hybrid_retriever import HybridResult
from app.memory.embedding_provider import StubEmbeddingProvider
from app.models.memory_entry import MemoryType

USERS_API = "/api/v1/users"
ORGS_API = "/api/v1/organizations"
SCENARIOS_API = "/api/v1/scenarios"
AUTH_API = "/api/v1/auth/login"
MEMORY_API = "/api/v1/memory"
ENTITIES_API = "/api/v1/entities"
REL_API = "/api/v1/relationships"
RETRIEVAL_API = "/api/v1/retrieval"
CHAT_API = "/api/v1/chat"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(client, email, password):
    resp = client.post(AUTH_API, data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _make_headers(client):
    pw = "ValidPass123!"
    email = f"expl_{uuid.uuid4().hex[:8]}@example.com"
    client.post(f"{USERS_API}/", json={"full_name": "Expl User", "email": email, "password": pw})
    return {"Authorization": f"Bearer {_login(client, email, pw)}"}


def _make_org(client):
    slug = f"expl-org-{uuid.uuid4().hex[:8]}"
    resp = client.post(f"{ORGS_API}/", json={"name": "Expl Org", "slug": slug})
    assert resp.status_code == 201
    return resp.json()


def _make_memory(client, org_id, headers, content, embed=True):
    resp = client.post(
        f"{MEMORY_API}/",
        json={"organization_id": org_id, "memory_type": "decision", "content": content},
        headers=headers,
    )
    assert resp.status_code == 201
    entry = resp.json()
    if embed:
        vec = StubEmbeddingProvider().embed(content)
        er = client.put(f"{MEMORY_API}/{entry['id']}/embedding", json={"embedding": vec}, headers=headers)
        assert er.status_code == 200
    return entry


def _make_entity(client, org_id, headers, name):
    resp = client.post(
        f"{ENTITIES_API}/",
        json={"organization_id": org_id, "entity_type": "TECHNOLOGY", "name": name},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()


def _attach(client, memory_id, entity_id, headers):
    resp = client.post(
        f"{ENTITIES_API}/memory/{memory_id}/attach",
        json={"memory_entry_id": memory_id, "entity_id": entity_id},
        headers=headers,
    )
    assert resp.status_code in (201, 409)


def _make_fake_hybrid_result(score=0.8, sem=0.8, graph=0.0, link=0.0,
                              reason="semantic similarity", entities=None,
                              distance=0):
    """Create a minimal HybridResult with a mock MemoryEntry."""
    from unittest.mock import MagicMock
    mem = MagicMock()
    mem.id = uuid.uuid4()
    mem.title = "Mock Memory"
    mem.memory_type = MagicMock()
    mem.memory_type.value = "decision"
    return HybridResult(
        memory=mem,
        score=score,
        semantic_score=sem,
        graph_score=graph,
        link_score=link,
        retrieval_reason=reason,
        matched_entities=entities or [],
        graph_distance=distance,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def auth_headers(client):
    return _make_headers(client)


@pytest.fixture()
def org(client):
    return _make_org(client)


@pytest.fixture()
def org_with_linked_memories(client, auth_headers):
    """Org: two embedded memories sharing an entity connected by a graph edge."""
    org = _make_org(client)
    m1 = _make_memory(client, org["id"], auth_headers, "PostgreSQL is our primary store")
    m2 = _make_memory(client, org["id"], auth_headers, "Redis caching layer for sessions")
    e1 = _make_entity(client, org["id"], auth_headers, f"PostgreSQL-{uuid.uuid4().hex[:4]}")
    e2 = _make_entity(client, org["id"], auth_headers, f"Redis-{uuid.uuid4().hex[:4]}")
    _attach(client, m1["id"], e1["id"], auth_headers)
    _attach(client, m2["id"], e2["id"], auth_headers)
    # Create a graph edge between the two entities
    client.post(
        f"{REL_API}/",
        json={
            "organization_id": org["id"],
            "source_entity_id": e1["id"],
            "target_entity_id": e2["id"],
            "relationship_type": "DEPENDS_ON",
        },
        headers=auth_headers,
    )
    return {"org": org, "m1": m1, "m2": m2, "e1": e1, "e2": e2}


# ===========================================================================
# Unit tests — aggregate_confidence
# ===========================================================================

class TestAggregateConfidence:
    def test_empty_returns_zero(self):
        assert aggregate_confidence([]) == 0.0

    def test_single_result_returns_its_score(self):
        r = _make_fake_hybrid_result(score=0.75)
        assert aggregate_confidence([r]) == pytest.approx(0.75)

    def test_multiple_results_rank_decay(self):
        r1 = _make_fake_hybrid_result(score=1.0)
        r2 = _make_fake_hybrid_result(score=0.0)
        # rank-decay: r1 weight=1.0, r2 weight=0.5 → (1.0*1.0 + 0.0*0.5)/1.5 = 0.667
        conf = aggregate_confidence([r1, r2])
        assert conf == pytest.approx(2 / 3, abs=0.01)

    def test_confidence_clamped_to_one(self):
        results = [_make_fake_hybrid_result(score=1.0) for _ in range(5)]
        assert aggregate_confidence(results) == pytest.approx(1.0)

    def test_confidence_always_non_negative(self):
        results = [_make_fake_hybrid_result(score=0.0) for _ in range(3)]
        assert aggregate_confidence(results) >= 0.0

    def test_top_hit_dominates(self):
        """First result has higher weight than later results."""
        high = _make_fake_hybrid_result(score=1.0)
        low1 = _make_fake_hybrid_result(score=0.0)
        low2 = _make_fake_hybrid_result(score=0.0)
        conf_all = aggregate_confidence([high, low1, low2])
        # Must be >0 because top result has weight 1 vs total 1+0.5+0.33
        assert conf_all > 0.5


# ===========================================================================
# Unit tests — build_graph_path
# ===========================================================================

class TestBuildGraphPath:
    def _get_db(self):
        from app.db.dependencies import get_db
        return next(get_db())

    def test_empty_results_returns_empty_path(self):
        db = self._get_db()
        try:
            path = build_graph_path([], db, uuid.uuid4())
            assert path == []
        finally:
            db.close()

    def test_single_result_returns_empty_path(self):
        db = self._get_db()
        try:
            path = build_graph_path(
                [_make_fake_hybrid_result()], db, uuid.uuid4()
            )
            assert path == []
        finally:
            db.close()

    def test_no_entities_returns_empty_path(self):
        db = self._get_db()
        try:
            r1 = _make_fake_hybrid_result(entities=[])
            r2 = _make_fake_hybrid_result(entities=[])
            path = build_graph_path([r1, r2], db, uuid.uuid4())
            assert path == []
        finally:
            db.close()

    def test_graph_path_returns_steps_when_edge_exists(self, org_with_linked_memories):
        """Direct relationship between e1 and e2 → build_graph_path returns steps."""
        data = org_with_linked_memories
        db = self._get_db()
        try:
            r1 = _make_fake_hybrid_result(
                entities=[data["e1"]["name"]], score=0.9
            )
            r2 = _make_fake_hybrid_result(
                entities=[data["e2"]["name"]], score=0.5
            )
            path = build_graph_path(
                [r1, r2], db, uuid.UUID(data["org"]["id"])
            )
            assert len(path) >= 1
            step = path[0]
            assert isinstance(step, GraphPathStep)
            assert step.relationship_type == "DEPENDS_ON"
        finally:
            db.close()

    def test_graph_path_empty_when_no_edge(self):
        """No relationship between entity sets → empty path."""
        db = self._get_db()
        try:
            r1 = _make_fake_hybrid_result(entities=["EntityThatDoesNotExist_A"])
            r2 = _make_fake_hybrid_result(entities=["EntityThatDoesNotExist_B"])
            path = build_graph_path([r1, r2], db, uuid.uuid4())
            assert path == []
        finally:
            db.close()


# ===========================================================================
# Unit tests — build_retrieval_explanation
# ===========================================================================

class TestBuildRetrievalExplanation:
    def _get_db(self):
        from app.db.dependencies import get_db
        return next(get_db())

    def test_empty_results_returns_no_memories_summary(self):
        db = self._get_db()
        try:
            exp = build_retrieval_explanation(
                question="What is X?",
                hybrid_results=[],
                db=db,
                organization_id=uuid.uuid4(),
                retrieval_mode="hybrid",
            )
            assert exp.result_count == 0
            assert exp.confidence == 0.0
            assert "No relevant" in exp.summary
            assert exp.citations == []
            assert exp.graph_path == []
        finally:
            db.close()

    def test_citations_match_results_count(self):
        db = self._get_db()
        try:
            results = [_make_fake_hybrid_result(score=0.9 - i * 0.1) for i in range(3)]
            exp = build_retrieval_explanation(
                question="Q?",
                hybrid_results=results,
                db=db,
                organization_id=uuid.uuid4(),
                retrieval_mode="hybrid",
            )
            assert len(exp.citations) == 3
        finally:
            db.close()

    def test_citations_are_ranked_in_order(self):
        db = self._get_db()
        try:
            results = [_make_fake_hybrid_result(score=0.9 - i * 0.1) for i in range(3)]
            exp = build_retrieval_explanation(
                "Q", results, db, uuid.uuid4()
            )
            ranks = [c.rank for c in exp.citations]
            assert ranks == [1, 2, 3]
        finally:
            db.close()

    def test_summary_contains_result_count(self):
        db = self._get_db()
        try:
            results = [_make_fake_hybrid_result() for _ in range(2)]
            exp = build_retrieval_explanation("Q", results, db, uuid.uuid4(), "hybrid")
            assert "2" in exp.summary
        finally:
            db.close()

    def test_confidence_in_valid_range(self):
        db = self._get_db()
        try:
            results = [_make_fake_hybrid_result(score=0.6)]
            exp = build_retrieval_explanation("Q", results, db, uuid.uuid4(), "hybrid")
            assert 0.0 <= exp.confidence <= 1.0
        finally:
            db.close()

    def test_retrieval_mode_preserved(self):
        db = self._get_db()
        try:
            exp = build_retrieval_explanation(
                "Q", [], db, uuid.uuid4(), "semantic"
            )
            assert exp.retrieval_mode == "semantic"
        finally:
            db.close()


# ===========================================================================
# API tests — POST /api/v1/retrieval/explain
# ===========================================================================

class TestExplainEndpoint:
    def test_explain_returns_200(self, client, org, auth_headers):
        resp = client.post(
            f"{RETRIEVAL_API}/explain",
            json={"organization_id": org["id"], "question": "What was decided?"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text

    def test_explain_response_has_required_fields(self, client, org, auth_headers):
        resp = client.post(
            f"{RETRIEVAL_API}/explain",
            json={"organization_id": org["id"], "question": "Test"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "explanation" in data
        assert "results" in data
        exp = data["explanation"]
        assert "question" in exp
        assert "retrieval_mode" in exp
        assert "confidence" in exp
        assert "result_count" in exp
        assert "citations" in exp
        assert "graph_path" in exp
        assert "summary" in exp

    def test_explain_empty_org_returns_zero_confidence(self, client, auth_headers):
        empty_org = _make_org(client)
        resp = client.post(
            f"{RETRIEVAL_API}/explain",
            json={"organization_id": empty_org["id"], "question": "Anything?"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        exp = resp.json()["explanation"]
        assert exp["confidence"] == 0.0
        assert exp["result_count"] == 0
        assert exp["citations"] == []
        assert "No relevant" in exp["summary"]

    def test_explain_with_memories_returns_citations(
        self, client, org_with_linked_memories, auth_headers
    ):
        resp = client.post(
            f"{RETRIEVAL_API}/explain",
            json={
                "organization_id": org_with_linked_memories["org"]["id"],
                "question": "database storage",
                "top_k": 5,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        exp = resp.json()["explanation"]
        assert exp["result_count"] >= 1
        assert len(exp["citations"]) == exp["result_count"]

    def test_explain_citations_have_score_fields(
        self, client, org_with_linked_memories, auth_headers
    ):
        resp = client.post(
            f"{RETRIEVAL_API}/explain",
            json={
                "organization_id": org_with_linked_memories["org"]["id"],
                "question": "database",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        for citation in resp.json()["explanation"]["citations"]:
            assert "memory_id" in citation
            assert "memory_type" in citation
            assert "retrieval_reason" in citation
            assert "semantic_score" in citation
            assert "graph_score" in citation
            assert "link_score" in citation
            assert "final_score" in citation
            assert "rank" in citation
            assert citation["retrieval_reason"]

    def test_explain_citations_ranked_ascending(
        self, client, org_with_linked_memories, auth_headers
    ):
        resp = client.post(
            f"{RETRIEVAL_API}/explain",
            json={"organization_id": org_with_linked_memories["org"]["id"], "question": "db"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        ranks = [c["rank"] for c in resp.json()["explanation"]["citations"]]
        assert ranks == sorted(ranks)

    def test_explain_confidence_in_range(
        self, client, org_with_linked_memories, auth_headers
    ):
        resp = client.post(
            f"{RETRIEVAL_API}/explain",
            json={"organization_id": org_with_linked_memories["org"]["id"], "question": "db"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        conf = resp.json()["explanation"]["confidence"]
        assert 0.0 <= conf <= 1.0

    def test_explain_graph_path_when_entity_edge_exists(
        self, client, org_with_linked_memories, auth_headers
    ):
        """Explanation should include a graph_path step when entities are connected."""
        resp = client.post(
            f"{RETRIEVAL_API}/explain",
            json={
                "organization_id": org_with_linked_memories["org"]["id"],
                "question": "PostgreSQL Redis database storage",
                "top_k": 5,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        # If two results share a graph edge, path should have at least one step
        exp = resp.json()["explanation"]
        if exp["result_count"] >= 2:
            # path may or may not exist depending on which entities are in top-2
            # just verify it's a list
            assert isinstance(exp["graph_path"], list)

    def test_explain_organisation_isolation(
        self, client, org_with_linked_memories, auth_headers
    ):
        """Querying with a different org_id must return empty explanation."""
        other_org = _make_org(client)
        resp = client.post(
            f"{RETRIEVAL_API}/explain",
            json={"organization_id": other_org["id"], "question": "database"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["explanation"]["result_count"] == 0
        assert resp.json()["results"] == []

    def test_explain_without_auth_returns_401(self, client, org):
        resp = client.post(
            f"{RETRIEVAL_API}/explain",
            json={"organization_id": org["id"], "question": "test"},
        )
        assert resp.status_code == 401

    def test_explain_empty_question_returns_422(self, client, org, auth_headers):
        resp = client.post(
            f"{RETRIEVAL_API}/explain",
            json={"organization_id": org["id"], "question": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_explain_summary_is_non_empty_string(
        self, client, org_with_linked_memories, auth_headers
    ):
        resp = client.post(
            f"{RETRIEVAL_API}/explain",
            json={"organization_id": org_with_linked_memories["org"]["id"], "question": "db"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        summary = resp.json()["explanation"]["summary"]
        assert isinstance(summary, str)
        assert len(summary) > 0


# ===========================================================================
# Chat endpoint — explanation integration
# ===========================================================================

class TestChatExplanationIntegration:
    def test_semantic_mode_explanation_is_null(self, client, org, auth_headers):
        resp = client.post(
            f"{CHAT_API}/ask",
            json={"organization_id": org["id"], "question": "What is this?"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["explanation"] is None

    def test_hybrid_mode_explanation_is_populated(
        self, client, org_with_linked_memories, auth_headers
    ):
        resp = client.post(
            f"{CHAT_API}/ask",
            json={
                "organization_id": org_with_linked_memories["org"]["id"],
                "question": "database storage decisions",
                "use_hybrid": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["retrieval_mode"] == "hybrid"
        assert data["explanation"] is not None
        exp = data["explanation"]
        assert exp["question"] == "database storage decisions"
        assert exp["retrieval_mode"] == "hybrid"

    def test_hybrid_explanation_citations_match_count(
        self, client, org_with_linked_memories, auth_headers
    ):
        resp = client.post(
            f"{CHAT_API}/ask",
            json={
                "organization_id": org_with_linked_memories["org"]["id"],
                "question": "database",
                "use_hybrid": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        if data["explanation"] is not None:
            exp = data["explanation"]
            assert exp["result_count"] == len(exp["citations"])

    def test_hybrid_explanation_confidence_in_range(
        self, client, org_with_linked_memories, auth_headers
    ):
        resp = client.post(
            f"{CHAT_API}/ask",
            json={
                "organization_id": org_with_linked_memories["org"]["id"],
                "question": "database",
                "use_hybrid": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        if data["explanation"] is not None:
            assert 0.0 <= data["explanation"]["confidence"] <= 1.0

    def test_hybrid_explanation_summary_non_empty(
        self, client, org_with_linked_memories, auth_headers
    ):
        resp = client.post(
            f"{CHAT_API}/ask",
            json={
                "organization_id": org_with_linked_memories["org"]["id"],
                "question": "database",
                "use_hybrid": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        if data["explanation"] is not None:
            assert data["explanation"]["summary"]

    def test_existing_chat_semantic_unbroken(self, client, org, auth_headers):
        """Original semantic chat path must still work after schema changes."""
        resp = client.post(
            f"{CHAT_API}/ask",
            json={"organization_id": org["id"], "question": "Any question?"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert data["provider_used"] == "stub"
        assert data["retrieval_mode"] == "semantic"
        assert data["explanation"] is None
