"""
Comprehensive Test Suite for Sprint AI-005 — LangChain Production RAG Pipeline.

Validates:
1. Chat model initialization & configuration
2. PGVector Retriever with metadata extraction
3. Prompt templates (Engineering, Incident, Repo, PR Review)
4. LCEL Runnable pipeline execution (sync & async)
5. Streaming token events & SSE emission
6. Output parser formatting & confidence heuristics
7. API endpoints: POST /api/v1/chat, POST /api/v1/chat/ask, POST /api/v1/chat/stream
8. Citation preservation & formatting
9. Empty retrieval graceful fallback
10. Organization isolation & security boundaries
"""
from __future__ import annotations

import json
import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.db.dependencies import get_db
from app.langchain.chains import arun_rag_chain, build_rag_chain, run_rag_chain
from app.langchain.chat_model import StubChatModel, get_chat_model
from app.langchain.output_parser import TeamMemoryOutputParser, TeamMemoryRAGOutput
from app.langchain.prompt_templates import (
    ENGINEERING_CHAT_PROMPT,
    INCIDENT_INVESTIGATION_PROMPT,
    PULL_REQUEST_REVIEW_PROMPT,
    REPOSITORY_ANALYSIS_PROMPT,
    format_documents_to_citations,
    format_documents_to_context,
    get_prompt_template,
)
from app.langchain.retriever import TeamMemoryPGVectorRetriever, get_memory_retriever
from app.langchain.streaming import astream_rag_chain, stream_rag_chain
from app.memory.embedding_provider import StubEmbeddingProvider
from app.models.memory_entry import MemoryEntry, MemoryType
from app.schemas.memory_entry import MemoryEntryCreate
from app.services.memory_entry import create_memory_entry, store_embedding

USERS_API = "/api/v1/users"
ORGS_API = "/api/v1/organizations"
AUTH_API = "/api/v1/auth/login"
MEMORY_API = "/api/v1/memory"
CHAT_API = "/api/v1/chat"


def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post(AUTH_API, data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture()
def db():
    gen = get_db()
    session = next(gen)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def auth_headers(client: TestClient):
    password = "ValidPass123!"
    email = f"lc_user_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        f"{USERS_API}/",
        json={"full_name": "LangChain Test User", "email": email, "password": password},
    )
    token = _login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def org_a(client: TestClient, auth_headers):
    slug = f"lc-org-a-{uuid.uuid4().hex[:8]}"
    resp = client.post(f"{ORGS_API}/", json={"name": "Org A", "slug": slug})
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def org_b(client: TestClient, auth_headers):
    slug = f"lc-org-b-{uuid.uuid4().hex[:8]}"
    resp = client.post(f"{ORGS_API}/", json={"name": "Org B", "slug": slug})
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def populated_memory_org_a(db, org_a):
    org_id = uuid.UUID(org_a["id"])
    emb_provider = StubEmbeddingProvider()

    # Create memory 1: Decision
    entry1 = create_memory_entry(
        db=db,
        entry_in=MemoryEntryCreate(
            organization_id=org_id,
            memory_type=MemoryType.decision,
            title="Adopt PostgreSQL 17",
            content="We chose PostgreSQL 17 with pgvector for unified vector and relational storage.",
            meta={
                "source": "backend/app/db",
                "file_path": "backend/app/db/session.py",
                "start_line": 1,
                "end_line": 25,
                "section_header": "Database Layer",
            },
        ),
        auto_embed=False,
    )
    store_embedding(db, entry1.id, emb_provider.embed(entry1.content))

    # Create memory 2: Incident
    entry2 = create_memory_entry(
        db=db,
        entry_in=MemoryEntryCreate(
            organization_id=org_id,
            memory_type=MemoryType.insight,
            title="Connection Pool Saturation",
            content="Incident resolved: increased max_overflow and reduced pool_recycle timeout to 300s.",
            meta={
                "source": "incidents/postmortems",
                "file_path": "docs/incidents/inc-042.md",
                "start_line": 10,
                "end_line": 40,
                "section_header": "Root Cause Analysis",
            },
        ),
        auto_embed=False,
    )
    store_embedding(db, entry2.id, emb_provider.embed(entry2.content))

    return [entry1, entry2]


# ---------------------------------------------------------------------------
# 1. Chat Model Tests
# ---------------------------------------------------------------------------
class TestLangChainChatModel:
    def test_stub_chat_model_sync_invoke(self):
        model = StubChatModel()
        resp = model.invoke("Question: How does pgvector work? Answer:")
        assert resp is not None
        assert "How does pgvector work?" in resp.content
        assert "team memory" in resp.content.lower()

    @pytest.mark.asyncio
    async def test_stub_chat_model_async_invoke(self):
        model = StubChatModel()
        resp = await model.ainvoke("Question: Async check? Answer:")
        assert "Async check?" in resp.content

    def test_stub_chat_model_stream(self):
        model = StubChatModel()
        chunks = list(model.stream("Question: Streaming check? Answer:"))
        assert len(chunks) > 0
        joined = "".join(c.content for c in chunks)
        assert "Streaming check?" in joined

    def test_get_chat_model_factory(self, monkeypatch):
        monkeypatch.setattr(settings, "LLM_PROVIDER", "stub")
        model = get_chat_model()
        assert isinstance(model, StubChatModel)


# ---------------------------------------------------------------------------
# 2. PGVector Retriever Tests
# ---------------------------------------------------------------------------
class TestPGVectorRetriever:
    def test_retriever_returns_top_k_with_metadata(self, db, org_a, populated_memory_org_a):
        org_id = uuid.UUID(org_a["id"])
        retriever = get_memory_retriever(
            db=db,
            organization_id=org_id,
            top_k=2,
            embedding_provider=StubEmbeddingProvider(),
        )

        docs = retriever.invoke("PostgreSQL database decision")
        assert len(docs) == 2
        first = docs[0]
        assert first.metadata["organization_id"] == str(org_id)
        assert first.metadata["memory_type"] in ("decision", "insight")
        assert "file_path" in first.metadata
        assert "line_numbers" in first.metadata
        assert "chunk_hash" in first.metadata
        assert first.metadata["similarity_score"] is not None

    @pytest.mark.asyncio
    async def test_retriever_ainvoke(self, db, org_a, populated_memory_org_a):
        org_id = uuid.UUID(org_a["id"])
        retriever = get_memory_retriever(
            db=db,
            organization_id=org_id,
            top_k=1,
            embedding_provider=StubEmbeddingProvider(),
        )
        docs = await retriever.ainvoke("Incident report")
        assert len(docs) == 1
        assert docs[0].page_content is not None


# ---------------------------------------------------------------------------
# 3. Prompt Template Tests
# ---------------------------------------------------------------------------
class TestPromptTemplates:
    def test_prompt_template_selector(self):
        assert get_prompt_template("engineering") == ENGINEERING_CHAT_PROMPT
        assert get_prompt_template("incident") == INCIDENT_INVESTIGATION_PROMPT
        assert get_prompt_template("repository") == REPOSITORY_ANALYSIS_PROMPT
        assert get_prompt_template("pr") == PULL_REQUEST_REVIEW_PROMPT
        assert get_prompt_template(None) == ENGINEERING_CHAT_PROMPT

    def test_format_documents_helpers(self, db, org_a, populated_memory_org_a):
        org_id = uuid.UUID(org_a["id"])
        retriever = get_memory_retriever(
            db=db,
            organization_id=org_id,
            top_k=2,
            embedding_provider=StubEmbeddingProvider(),
        )
        docs = retriever.invoke("database")

        context = format_documents_to_context(docs)
        assert "--- Organisational Memory Context ---" in context
        assert "TYPE: decision" in context or "TYPE: insight" in context

        citations = format_documents_to_citations(docs)
        assert "Citations:" in citations
        assert "[1]" in citations

    def test_empty_documents_formatting(self):
        assert "No relevant" in format_documents_to_context([])
        assert format_documents_to_citations([]) == ""


# ---------------------------------------------------------------------------
# 4. Runnable Pipeline Tests
# ---------------------------------------------------------------------------
class TestRunnablePipeline:
    def test_run_rag_chain_sync(self, db, org_a, populated_memory_org_a):
        org_id = uuid.UUID(org_a["id"])
        output = run_rag_chain(
            db=db,
            question="What is our database choice?",
            organization_id=org_id,
            embedding_provider=StubEmbeddingProvider(),
            chat_model=StubChatModel(),
        )
        assert isinstance(output, TeamMemoryRAGOutput)
        assert output.answer is not None
        assert len(output.citations) == 2
        assert len(output.retrieved_memories) == 2
        assert output.retrieval_mode == "semantic"

    @pytest.mark.asyncio
    async def test_arun_rag_chain_async(self, db, org_a, populated_memory_org_a):
        org_id = uuid.UUID(org_a["id"])
        output = await arun_rag_chain(
            db=db,
            question="What incidents occurred?",
            organization_id=org_id,
            embedding_provider=StubEmbeddingProvider(),
            chat_model=StubChatModel(),
        )
        assert isinstance(output, TeamMemoryRAGOutput)
        assert len(output.citations) == 2


# ---------------------------------------------------------------------------
# 5. Streaming Engine Tests
# ---------------------------------------------------------------------------
class TestStreamingEngine:
    def test_stream_rag_chain_events(self, db, org_a, populated_memory_org_a):
        org_id = uuid.UUID(org_a["id"])
        events = list(stream_rag_chain(
            db=db,
            question="Summarize database choices",
            organization_id=org_id,
            embedding_provider=StubEmbeddingProvider(),
            chat_model=StubChatModel(),
        ))

        assert len(events) > 0
        # Parse SSE data
        parsed_events = []
        for line in events:
            if line.startswith("data: "):
                payload = json.loads(line[6:].strip())
                parsed_events.append(payload)

        types = [e["type"] for e in parsed_events]
        assert "metadata" in types
        assert "citation" in types
        assert "token" in types
        assert "done" in types

        # Check metadata payload
        metadata = next(e for e in parsed_events if e["type"] == "metadata")
        assert metadata["retrieved_memory_count"] == 2
        assert len(metadata["citations"]) == 2

        # Check done payload
        done = next(e for e in parsed_events if e["type"] == "done")
        assert len(done["answer"]) > 0

    @pytest.mark.asyncio
    async def test_astream_rag_chain_events(self, db, org_a, populated_memory_org_a):
        org_id = uuid.UUID(org_a["id"])
        events = []
        async for chunk in astream_rag_chain(
            db=db,
            question="Async streaming question",
            organization_id=org_id,
            embedding_provider=StubEmbeddingProvider(),
            chat_model=StubChatModel(),
        ):
            events.append(chunk)

        assert len(events) > 0
        parsed = [json.loads(line[6:].strip()) for line in events if line.startswith("data: ")]
        types = [p["type"] for p in parsed]
        assert "metadata" in types
        assert "done" in types


# ---------------------------------------------------------------------------
# 6. Output Parser Tests
# ---------------------------------------------------------------------------
class TestOutputParser:
    def test_output_parser_structure(self):
        parser = TeamMemoryOutputParser()
        raw_text = "The system uses PostgreSQL [1] and Redis [2]."
        res = parser.parse(raw_text)
        assert res.answer == raw_text
        assert res.citations == ["[1]", "[2]"]
        assert res.confidence >= 0.8
        assert "LangChain-RAG-Agent" in res.participating_agents


# ---------------------------------------------------------------------------
# 7. Organization Isolation & Empty Fallback Tests
# ---------------------------------------------------------------------------
class TestOrganizationIsolationAndFallback:
    def test_organization_isolation(self, db, org_a, org_b, populated_memory_org_a):
        """Org B must not retrieve memories stored in Org A."""
        org_b_id = uuid.UUID(org_b["id"])
        output = run_rag_chain(
            db=db,
            question="What is our database choice?",
            organization_id=org_b_id,
            embedding_provider=StubEmbeddingProvider(),
            chat_model=StubChatModel(),
        )
        assert len(output.retrieved_memories) == 0
        assert len(output.citations) == 0

    def test_empty_retrieval_fallback(self, db, org_b):
        """Empty retrieval returns a graceful answer without throwing."""
        org_b_id = uuid.UUID(org_b["id"])
        output = run_rag_chain(
            db=db,
            question="Non-existent memory topic",
            organization_id=org_b_id,
            embedding_provider=StubEmbeddingProvider(),
            chat_model=StubChatModel(),
        )
        assert output.answer is not None
        assert output.confidence <= 0.5


# ---------------------------------------------------------------------------
# 8. API Endpoint Tests
# ---------------------------------------------------------------------------
class TestChatEndpoints:
    def test_post_chat_root(self, client: TestClient, org_a, auth_headers, populated_memory_org_a):
        resp = client.post(
            CHAT_API,
            json={
                "organization_id": org_a["id"],
                "question": "What database do we use?",
                "scenario_type": "engineering",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "answer" in data
        assert data["retrieved_memory_count"] == 2
        assert len(data["citations"]) == 2

    def test_post_chat_ask_alias(self, client: TestClient, org_a, auth_headers, populated_memory_org_a):
        resp = client.post(
            f"{CHAT_API}/ask",
            json={
                "organization_id": org_a["id"],
                "question": "What database do we use?",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["retrieved_memory_count"] == 2

    def test_post_chat_stream(self, client: TestClient, org_a, auth_headers, populated_memory_org_a):
        resp = client.post(
            f"{CHAT_API}/stream",
            json={
                "organization_id": org_a["id"],
                "question": "Explain database configuration",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        text_body = resp.text
        assert "data: " in text_body
        assert '"type": "metadata"' in text_body
        assert '"type": "done"' in text_body
