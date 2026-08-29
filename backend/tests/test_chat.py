"""
Task 4.4 — Granite-Powered RAG Generation tests.

Covers:
* StubGenerationProvider — determinism, protocol conformance, provider name
* GenerationProvider factory — stub returned by default
* PromptBuilder — structure, citations, trimming, empty context
* RAG generation service (run_rag) — with/without memories, provider failure
* POST /api/v1/chat/ask — success, empty memory, unauthenticated, invalid input
"""
from __future__ import annotations

import math
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.memory.embedding_provider import StubEmbeddingProvider
from app.memory.generation_provider import (
    GenerationProvider,
    StubGenerationProvider,
    get_generation_provider,
)
from app.memory.prompt_builder import SYSTEM_PROMPT, build_prompt, _build_citations
from app.memory.rag_generation import ChatResponse, run_rag
from app.models.memory_entry import EMBEDDING_DIM

USERS_API = "/api/v1/users"
ORGS_API = "/api/v1/organizations"
AUTH_API = "/api/v1/auth/login"
MEMORY_API = "/api/v1/memory"
CHAT_API = "/api/v1/chat"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post(AUTH_API, data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _unit_vec(seed: float = 1.0) -> list[float]:
    raw = [seed] * EMBEDDING_DIM
    mag = math.sqrt(sum(v * v for v in raw))
    return [v / mag for v in raw]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def org(client: TestClient):
    slug = f"chat-org-{uuid.uuid4().hex[:8]}"
    resp = client.post(f"{ORGS_API}/", json={"name": "Chat Org", "slug": slug})
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def auth_headers(client: TestClient):
    password = "ValidPass123!"
    email = f"chat_auth_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        f"{USERS_API}/",
        json={"full_name": "Chat Auth User", "email": email, "password": password},
    )
    token = _login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def memory_entry_with_embedding(client: TestClient, org, auth_headers):
    """Create a memory entry and store a deterministic embedding on it."""
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
    entry = resp.json()

    vec = StubEmbeddingProvider().embed("Use PostgreSQL")
    emb_resp = client.put(
        f"{MEMORY_API}/{entry['id']}/embedding",
        json={"embedding": vec},
        headers=auth_headers,
    )
    assert emb_resp.status_code == 200, emb_resp.text
    return entry


# ---------------------------------------------------------------------------
# StubGenerationProvider unit tests
# ---------------------------------------------------------------------------

class TestStubGenerationProvider:
    def setup_method(self):
        self.provider = StubGenerationProvider()

    def test_provider_name(self):
        assert self.provider.provider_name == "stub"

    def test_protocol_conformance(self):
        assert isinstance(self.provider, GenerationProvider)

    def test_generate_returns_string(self):
        result = self.provider.generate("Some prompt\nQuestion: What is pgvector?")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_echoes_question(self):
        result = self.provider.generate(
            "Context...\nQuestion: How do we deploy this?"
        )
        assert "How do we deploy this?" in result

    def test_generate_no_question_line(self):
        result = self.provider.generate("Just a prompt with no question marker.")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_is_deterministic(self):
        prompt = "Question: Is this repeatable?"
        assert self.provider.generate(prompt) == self.provider.generate(prompt)


# ---------------------------------------------------------------------------
# Generation provider factory
# ---------------------------------------------------------------------------

class TestGetGenerationProvider:
    def test_default_returns_stub(self, monkeypatch):
        monkeypatch.setattr(settings, "GRANITE_PROVIDER", "stub")
        provider = get_generation_provider()
        assert isinstance(provider, StubGenerationProvider)

    def test_factory_returns_stub_instance(self):
        # Default setting is "stub" — no credentials needed.
        provider = get_generation_provider()
        assert provider.provider_name == "stub"


# ---------------------------------------------------------------------------
# Prompt builder unit tests
# ---------------------------------------------------------------------------

class TestPromptBuilder:
    def _make_mock_entry(self, title: str | None, content: str, mtype: str = "decision"):
        entry = MagicMock()
        entry.id = uuid.uuid4()
        entry.title = title
        entry.content = content
        entry.memory_type.value = mtype
        return entry

    def test_prompt_contains_system_prompt(self):
        prompt = build_prompt("What is our DB?", "context block", [])
        assert SYSTEM_PROMPT[:40] in prompt

    def test_prompt_contains_question(self):
        prompt = build_prompt("Why PostgreSQL?", "some context", [])
        assert "Why PostgreSQL?" in prompt

    def test_prompt_contains_context(self):
        prompt = build_prompt("Q?", "SPECIAL_CONTEXT_MARKER", [])
        assert "SPECIAL_CONTEXT_MARKER" in prompt

    def test_prompt_contains_citations(self):
        entry = self._make_mock_entry("Use Postgres", "Decision text")
        prompt = build_prompt("Q?", "context", [entry])
        assert "[1]" in prompt
        assert "decision" in prompt
        assert "Use Postgres" in prompt

    def test_empty_entries_no_citations_block(self):
        prompt = build_prompt("Q?", "context", [])
        assert "Citations:" not in prompt

    def test_prompt_trimmed_when_too_long(self):
        long_context = "X" * 20_000
        prompt = build_prompt("Short Q?", long_context, [], max_chars=500)
        assert len(prompt) <= 600  # allows a small margin for trim marker

    def test_trim_includes_marker(self):
        # Use a large enough budget so the context is trimmed (not fully omitted)
        # but small enough that 20_000 Xs cannot fit.
        prompt = build_prompt("Q?", "X" * 20_000, [], max_chars=2000)
        assert "trimmed" in prompt

    def test_citations_block_structure(self):
        entry = self._make_mock_entry("My Title", "content")
        citations = _build_citations([entry])
        assert "[1]" in citations
        assert "My Title" in citations
        assert str(entry.id) in citations

    def test_citations_no_title(self):
        entry = self._make_mock_entry(None, "content")
        citations = _build_citations([entry])
        assert "[1]" in citations


# ---------------------------------------------------------------------------
# run_rag service tests (service layer — no HTTP)
# ---------------------------------------------------------------------------

class TestRunRAG:
    def setup_method(self):
        self.emb_provider = StubEmbeddingProvider()
        self.gen_provider = StubGenerationProvider()

    def _get_db(self):
        from app.db.dependencies import get_db
        gen = get_db()
        return next(gen)

    def test_run_rag_returns_chat_response(self, org):
        db = self._get_db()
        try:
            result = run_rag(
                db=db,
                question="What database do we use?",
                organization_id=uuid.UUID(org["id"]),
                embedding_provider=self.emb_provider,
                generation_provider=self.gen_provider,
            )
        finally:
            db.close()

        assert isinstance(result, ChatResponse)
        assert isinstance(result.answer, str)
        assert len(result.answer) > 0
        assert isinstance(result.citations, list)
        assert result.provider_used == "stub"

    def test_run_rag_empty_memory_no_retrieved(self, org):
        """Fresh org with no embedded memories — retrieved_memory_count must be 0."""
        slug = f"empty-chat-{uuid.uuid4().hex[:6]}"
        from app.services.organization import create_organization
        from app.schemas.organization import OrganizationCreate
        db = self._get_db()
        try:
            fresh_org = create_organization(
                db, OrganizationCreate(name="Empty Chat Org", slug=slug)
            )
            result = run_rag(
                db=db,
                question="Anything?",
                organization_id=fresh_org.id,
                embedding_provider=self.emb_provider,
                generation_provider=self.gen_provider,
            )
        finally:
            db.close()

        assert result.retrieved_memory_count == 0
        assert result.answer  # stub still returns something

    def test_run_rag_provider_failure_returns_safe_message(self, org):
        """If generation raises, run_rag must return a safe error message."""
        failing_provider = MagicMock(spec=GenerationProvider)
        failing_provider.provider_name = "failing_stub"
        failing_provider.generate.side_effect = RuntimeError("model exploded")

        db = self._get_db()
        try:
            result = run_rag(
                db=db,
                question="What is the architecture?",
                organization_id=uuid.UUID(org["id"]),
                embedding_provider=self.emb_provider,
                generation_provider=failing_provider,
            )
        finally:
            db.close()

        assert "unable to generate" in result.answer.lower()
        assert "RuntimeError" in result.answer

    def test_run_rag_with_memory_retrieves_entries(self, org, memory_entry_with_embedding):
        """When embeddings exist the retrieved_memory_count must be > 0."""
        db = self._get_db()
        try:
            result = run_rag(
                db=db,
                question="What database decisions were made?",
                organization_id=uuid.UUID(org["id"]),
                embedding_provider=self.emb_provider,
                generation_provider=self.gen_provider,
            )
        finally:
            db.close()

        assert result.retrieved_memory_count > 0
        assert len(result.citations) == result.retrieved_memory_count


# ---------------------------------------------------------------------------
# POST /api/v1/chat/ask endpoint tests
# ---------------------------------------------------------------------------

class TestChatAskEndpoint:
    def test_ask_returns_200_with_answer(self, client, org, auth_headers):
        resp = client.post(
            f"{CHAT_API}/ask",
            json={
                "organization_id": org["id"],
                "question": "What is our primary database?",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "citations" in data
        assert "retrieved_memory_count" in data
        assert "provider_used" in data
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0

    def test_ask_returns_provider_name(self, client, org, auth_headers):
        resp = client.post(
            f"{CHAT_API}/ask",
            json={"organization_id": org["id"], "question": "Any question."},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        # Default GRANITE_PROVIDER=stub — must reflect that in response
        assert resp.json()["provider_used"] == "stub"

    def test_ask_with_memory_returns_citations(
        self, client, org, auth_headers, memory_entry_with_embedding
    ):
        resp = client.post(
            f"{CHAT_API}/ask",
            json={
                "organization_id": org["id"],
                "question": "What database decisions were made?",
                "top_k": 5,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["retrieved_memory_count"] > 0
        assert len(data["citations"]) == data["retrieved_memory_count"]

    def test_ask_empty_org_returns_zero_retrieved(self, client, auth_headers):
        slug = f"chat-empty-{uuid.uuid4().hex[:6]}"
        empty_org = client.post(
            f"{ORGS_API}/", json={"name": "Empty Chat Org", "slug": slug}
        ).json()
        resp = client.post(
            f"{CHAT_API}/ask",
            json={
                "organization_id": empty_org["id"],
                "question": "Is there any memory?",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["retrieved_memory_count"] == 0
        # Answer must still be non-empty (graceful fallback)
        assert len(resp.json()["answer"]) > 0

    def test_ask_without_auth_returns_401(self, client, org):
        resp = client.post(
            f"{CHAT_API}/ask",
            json={"organization_id": org["id"], "question": "Anything?"},
        )
        assert resp.status_code == 401

    def test_ask_empty_question_returns_422(self, client, org, auth_headers):
        resp = client.post(
            f"{CHAT_API}/ask",
            json={"organization_id": org["id"], "question": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_ask_missing_org_id_returns_422(self, client, auth_headers):
        resp = client.post(
            f"{CHAT_API}/ask",
            json={"question": "What is happening?"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_ask_top_k_out_of_range_returns_422(self, client, org, auth_headers):
        resp = client.post(
            f"{CHAT_API}/ask",
            json={
                "organization_id": org["id"],
                "question": "Anything?",
                "top_k": 0,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422
