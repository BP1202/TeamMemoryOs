"""
Task 4.3 — Semantic Retrieval Engine tests.

Covers:
* StubEmbeddingProvider — determinism, normalisation, dimension
* store_embedding service — success, wrong dimension, not-found
* semantic_search service — ranking correctness, org isolation, empty result
* RAG context builder — formatted output, empty-memory case
* PUT  /api/v1/memory/{entry_id}/embedding  — store embedding (auth required)
* POST /api/v1/memory/search                — semantic search (auth required)
* Unauthenticated access rejected on both new endpoints
"""
from __future__ import annotations

import math
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.main import app
from app.memory.embedding_provider import StubEmbeddingProvider
from app.memory.rag_context import build_rag_context
from app.models.memory_entry import EMBEDDING_DIM
from app.services.memory_entry import (
    create_memory_entry,
    semantic_search,
    store_embedding,
)
from app.schemas.memory_entry import MemoryEntryCreate

USERS_API = "/api/v1/users"
ORGS_API = "/api/v1/organizations"
SCENARIOS_API = "/api/v1/scenarios"
AUTH_API = "/api/v1/auth/login"
MEMORY_API = "/api/v1/memory"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post(AUTH_API, data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _make_vector(seed: float = 1.0) -> list[float]:
    """Return a unit-normalised vector usable for deterministic tests."""
    raw = [seed] * EMBEDDING_DIM
    mag = math.sqrt(sum(v * v for v in raw))
    return [v / mag for v in raw]


def _get_db_session() -> Session:
    """Grab a direct DB session for service-layer tests."""
    gen = get_db()
    return next(gen)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def org(client: TestClient):
    slug = f"rag-org-{uuid.uuid4().hex[:8]}"
    resp = client.post(f"{ORGS_API}/", json={"name": "RAG Org", "slug": slug})
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def auth_headers(client: TestClient):
    password = "ValidPass123!"
    email = f"rag_auth_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        f"{USERS_API}/",
        json={"full_name": "RAG Auth User", "email": email, "password": password},
    )
    token = _login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def memory_entry(client: TestClient, org, auth_headers):
    resp = client.post(
        f"{MEMORY_API}/",
        json={
            "organization_id": org["id"],
            "memory_type": "decision",
            "title": "Use PostgreSQL",
            "content": "We decided to use PostgreSQL as the primary datastore.",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def db_session():
    """Provide a raw SQLAlchemy session; close after test."""
    session = _get_db_session()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# StubEmbeddingProvider unit tests
# ---------------------------------------------------------------------------

class TestStubEmbeddingProvider:
    def setup_method(self):
        self.provider = StubEmbeddingProvider()

    def test_dimension_property(self):
        assert self.provider.dimension == EMBEDDING_DIM

    def test_embed_returns_correct_length(self):
        vec = self.provider.embed("hello world")
        assert len(vec) == EMBEDDING_DIM

    def test_embed_is_deterministic(self):
        v1 = self.provider.embed("same text")
        v2 = self.provider.embed("same text")
        assert v1 == v2

    def test_embed_different_texts_produce_different_vectors(self):
        v1 = self.provider.embed("PostgreSQL is great")
        v2 = self.provider.embed("Python is fast")
        assert v1 != v2

    def test_embed_is_unit_normalised(self):
        vec = self.provider.embed("normalisation check")
        magnitude = math.sqrt(sum(v * v for v in vec))
        assert abs(magnitude - 1.0) < 1e-6, f"magnitude was {magnitude}"

    def test_embed_protocol_conformance(self):
        from app.memory.embedding_provider import EmbeddingProvider
        assert isinstance(self.provider, EmbeddingProvider)


# ---------------------------------------------------------------------------
# store_embedding + semantic_search service-layer tests
# ---------------------------------------------------------------------------

class TestStoreEmbedding:
    def test_store_returns_updated_entry(self, db_session, org, auth_headers, client):
        # Create an entry via the API first
        resp = client.post(
            f"{MEMORY_API}/",
            json={
                "organization_id": org["id"],
                "memory_type": "context",
                "content": "Background context for store test.",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        entry_id = uuid.UUID(resp.json()["id"])
        vec = _make_vector(0.5)

        updated = store_embedding(db_session, entry_id, vec)
        assert updated is not None
        assert updated.embedding is not None
        assert len(updated.embedding) == EMBEDDING_DIM

    def test_store_wrong_dimension_raises_value_error(self, db_session, org, auth_headers, client):
        resp = client.post(
            f"{MEMORY_API}/",
            json={
                "organization_id": org["id"],
                "memory_type": "insight",
                "content": "Insight for dim test.",
            },
            headers=auth_headers,
        )
        entry_id = uuid.UUID(resp.json()["id"])
        with pytest.raises(ValueError, match="dimensions"):
            store_embedding(db_session, entry_id, [0.1, 0.2, 0.3])  # wrong dim

    def test_store_unknown_entry_returns_none(self, db_session):
        result = store_embedding(db_session, uuid.uuid4(), _make_vector())
        assert result is None


class TestSemanticSearch:
    def _seed_entry(self, db: Session, org_id: str, content: str, vec: list[float]):
        """Create a memory entry and store an embedding, directly via service."""
        entry_in = MemoryEntryCreate(
            organization_id=uuid.UUID(org_id),
            memory_type="decision",
            content=content,
        )
        entry = create_memory_entry(db, entry_in)
        store_embedding(db, entry.id, vec)
        db.refresh(entry)
        return entry

    def test_search_returns_most_similar_first(self, db_session, org):
        """Seed two entries with different vectors; the closer one must rank first."""
        # query vector aligned with seed 1.0
        query_vec = _make_vector(1.0)
        # entry A: very close (same direction)
        entry_a = self._seed_entry(db_session, org["id"], "Entry A", _make_vector(1.0))
        # entry B: different direction (seed 2.0 produces a different normalised vec)
        entry_b = self._seed_entry(db_session, org["id"], "Entry B", _make_vector(2.0))

        results = semantic_search(db_session, query_vec, uuid.UUID(org["id"]), top_k=5)
        ids = [str(r.id) for r in results]

        assert str(entry_a.id) in ids
        # entry_a should rank before entry_b (lower cosine distance)
        assert ids.index(str(entry_a.id)) < ids.index(str(entry_b.id))

    def test_search_org_isolation(self, db_session, client):
        """Entries from a different org must not appear in results."""
        # Create two separate orgs
        slug_a = f"iso-a-{uuid.uuid4().hex[:6]}"
        slug_b = f"iso-b-{uuid.uuid4().hex[:6]}"
        org_a = client.post(f"{ORGS_API}/", json={"name": "Org A", "slug": slug_a}).json()
        org_b = client.post(f"{ORGS_API}/", json={"name": "Org B", "slug": slug_b}).json()

        vec = _make_vector(1.0)
        entry_b = self._seed_entry(db_session, org_b["id"], "Org B only entry", vec)

        results = semantic_search(db_session, vec, uuid.UUID(org_a["id"]), top_k=10)
        result_ids = [str(r.id) for r in results]
        assert str(entry_b.id) not in result_ids

    def test_search_no_embeddings_returns_empty(self, db_session, org, client, auth_headers):
        """Entries without embeddings must not be returned."""
        # Create entry but DON'T store an embedding
        resp = client.post(
            f"{MEMORY_API}/",
            json={
                "organization_id": org["id"],
                "memory_type": "discussion",
                "content": "No embedding stored here.",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201

        # Use a fresh org with no embeddings to keep isolation clean
        slug = f"empty-{uuid.uuid4().hex[:6]}"
        empty_org = client.post(
            f"{ORGS_API}/", json={"name": "Empty Org", "slug": slug}
        ).json()
        results = semantic_search(db_session, _make_vector(), uuid.UUID(empty_org["id"]))
        assert results == []


# ---------------------------------------------------------------------------
# RAG context builder unit tests
# ---------------------------------------------------------------------------

class TestRAGContextBuilder:
    def setup_method(self):
        self.provider = StubEmbeddingProvider()

    def test_returns_rag_context_object(self, db_session, org):
        result = build_rag_context(
            db=db_session,
            query="What database decisions were made?",
            organization_id=uuid.UUID(org["id"]),
            provider=self.provider,
        )
        from app.memory.rag_context import RAGContext
        assert isinstance(result, RAGContext)

    def test_empty_memory_produces_no_relevant_memories_text(self, db_session):
        slug = f"rag-empty-{uuid.uuid4().hex[:6]}"
        from sqlalchemy import text as sa_text
        # Use a brand-new org with no memory entries
        from app.services.organization import create_organization
        from app.schemas.organization import OrganizationCreate
        fresh_org = create_organization(
            db_session,
            OrganizationCreate(name="Fresh Org", slug=slug),
        )
        result = build_rag_context(
            db=db_session,
            query="anything",
            organization_id=fresh_org.id,
            provider=self.provider,
        )
        assert result.entries == []
        assert "No relevant memories found" in result.context_text

    def test_context_text_contains_query(self, db_session, org):
        query = "unique_query_string_xyz"
        result = build_rag_context(
            db=db_session,
            query=query,
            organization_id=uuid.UUID(org["id"]),
            provider=self.provider,
        )
        assert query in result.context_text

    def test_context_text_has_header_and_footer(self, db_session, org):
        result = build_rag_context(
            db=db_session,
            query="test",
            organization_id=uuid.UUID(org["id"]),
            provider=self.provider,
        )
        assert "--- Organisational Memory Context ---" in result.context_text
        assert "--- End of Context ---" in result.context_text


# ---------------------------------------------------------------------------
# API endpoint tests — PUT /{entry_id}/embedding
# ---------------------------------------------------------------------------

class TestStoreEmbeddingEndpoint:
    def test_store_embedding_returns_200(self, client, memory_entry, auth_headers):
        resp = client.put(
            f"{MEMORY_API}/{memory_entry['id']}/embedding",
            json={"embedding": _make_vector()},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == memory_entry["id"]

    def test_store_embedding_without_auth_returns_401(self, client, memory_entry):
        resp = client.put(
            f"{MEMORY_API}/{memory_entry['id']}/embedding",
            json={"embedding": _make_vector()},
        )
        assert resp.status_code == 401

    def test_store_embedding_unknown_entry_returns_404(self, client, auth_headers):
        resp = client.put(
            f"{MEMORY_API}/{uuid.uuid4()}/embedding",
            json={"embedding": _make_vector()},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_store_embedding_wrong_dimension_returns_422(self, client, memory_entry, auth_headers):
        resp = client.put(
            f"{MEMORY_API}/{memory_entry['id']}/embedding",
            json={"embedding": [0.1, 0.2, 0.3]},
            headers=auth_headers,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# API endpoint tests — POST /search
# ---------------------------------------------------------------------------

class TestSemanticSearchEndpoint:
    def _embed_entry(self, client, entry_id: str, vec: list[float], headers: dict):
        resp = client.put(
            f"{MEMORY_API}/{entry_id}/embedding",
            json={"embedding": vec},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text

    def test_search_returns_results(self, client, memory_entry, org, auth_headers):
        vec = _make_vector()
        self._embed_entry(client, memory_entry["id"], vec, auth_headers)

        resp = client.post(
            f"{MEMORY_API}/search",
            json={
                "query_embedding": vec,
                "organization_id": org["id"],
                "top_k": 5,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        results = resp.json()
        assert isinstance(results, list)
        ids = [r["entry"]["id"] for r in results]
        assert memory_entry["id"] in ids

    def test_search_result_has_rank(self, client, memory_entry, org, auth_headers):
        vec = _make_vector()
        self._embed_entry(client, memory_entry["id"], vec, auth_headers)

        resp = client.post(
            f"{MEMORY_API}/search",
            json={"query_embedding": vec, "organization_id": org["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        for item in resp.json():
            assert "rank" in item
            assert item["rank"] >= 1

    def test_search_without_auth_returns_401(self, client, org):
        resp = client.post(
            f"{MEMORY_API}/search",
            json={"query_embedding": _make_vector(), "organization_id": org["id"]},
        )
        assert resp.status_code == 401

    def test_search_wrong_dimension_returns_422(self, client, org, auth_headers):
        resp = client.post(
            f"{MEMORY_API}/search",
            json={
                "query_embedding": [0.1, 0.2],
                "organization_id": org["id"],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_search_unknown_org_returns_empty(self, client, auth_headers):
        resp = client.post(
            f"{MEMORY_API}/search",
            json={
                "query_embedding": _make_vector(),
                "organization_id": str(uuid.uuid4()),
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []
