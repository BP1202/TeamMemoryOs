"""
Unit and integration tests for Ollama LLM provider, factory, and streaming endpoints.
"""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app
from app.providers.base_provider import BaseLLMProvider, StubLLMProvider
from app.providers.llm_factory import get_llm_provider
from app.providers.ollama_provider import OllamaProvider


# ---------------------------------------------------------------------------
# Base & Stub LLM Provider Tests
# ---------------------------------------------------------------------------

def test_stub_llm_provider_generation():
    provider = StubLLMProvider(model_name="test-stub")
    assert provider.provider_name == "stub"
    assert provider.model_name == "test-stub"
    assert provider.is_available() is True

    prompt = "Question: How do we handle database migrations?"
    resp = provider.generate(prompt)
    assert "[Stub response]" in resp
    assert "database migrations" in resp


@pytest.mark.asyncio
async def test_stub_llm_provider_async():
    provider = StubLLMProvider()
    resp = await provider.agenerate("Question: What is TeamMemoryOS?")
    assert "[Stub response]" in resp
    assert "TeamMemoryOS" in resp

    health = await provider.acheck_health()
    assert health["status"] == "healthy"
    assert health["provider"] == "stub"


def test_stub_llm_provider_streaming():
    provider = StubLLMProvider()
    tokens = list(provider.stream_generate("Question: Test streaming"))
    assert len(tokens) > 0
    full_text = "".join(tokens)
    assert "[Stub response]" in full_text


@pytest.mark.asyncio
async def test_stub_llm_provider_async_streaming():
    provider = StubLLMProvider()
    tokens = []
    async for token in provider.astream_generate("Question: Async stream test"):
        tokens.append(token)
    assert len(tokens) > 0
    full_text = "".join(tokens)
    assert "[Stub response]" in full_text


# ---------------------------------------------------------------------------
# LLM Factory Tests
# ---------------------------------------------------------------------------

def test_llm_factory_resolves_ollama():
    provider = get_llm_provider("ollama", model="llama3.1:8b")
    assert isinstance(provider, OllamaProvider)
    assert provider.provider_name == "ollama"
    assert provider.model_name == "llama3.1:8b"


def test_llm_factory_resolves_stub():
    provider = get_llm_provider("stub", model="custom-stub")
    assert isinstance(provider, StubLLMProvider)
    assert provider.provider_name == "stub"
    assert provider.model_name == "custom-stub"


def test_llm_factory_defaults_to_settings():
    with patch.object(settings, "LLM_PROVIDER", "stub"):
        provider = get_llm_provider()
        assert isinstance(provider, StubLLMProvider)


# ---------------------------------------------------------------------------
# Ollama Provider Unit Tests (Mocked HTTP)
# ---------------------------------------------------------------------------

def test_ollama_provider_generate_success():
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.1:8b")
    assert provider.provider_name == "ollama"
    assert provider.model_name == "llama3.1:8b"
    assert provider.base_url == "http://localhost:11434"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": "Use Alembic with postgres migrations."}

    with patch("httpx.Client.post", return_value=mock_resp):
        result = provider.generate("How to run migrations?")
        assert result == "Use Alembic with postgres migrations."


@pytest.mark.asyncio
async def test_ollama_provider_agenerate_success():
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.1:8b")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": "Async response text"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        result = await provider.agenerate("Test prompt")
        assert result == "Async response text"


def test_ollama_provider_stream_generate():
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.1:8b")

    stream_lines = [
        json.dumps({"response": "Hello", "done": False}),
        json.dumps({"response": " world", "done": False}),
        json.dumps({"response": "!", "done": True}),
    ]

    mock_stream_ctx = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_lines.return_value = stream_lines
    mock_stream_ctx.__enter__.return_value = mock_response

    with patch("httpx.Client.stream", return_value=mock_stream_ctx):
        tokens = list(provider.stream_generate("Hi"))
        assert tokens == ["Hello", " world", "!"]


def test_ollama_provider_connection_error_raises_when_no_fallback():
    provider = OllamaProvider(base_url="http://localhost:9999", model="llama3.1:8b", fallback_to_stub=False)

    with patch("httpx.Client.post", side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(RuntimeError) as exc_info:
            provider.generate("Test prompt")
        assert "Could not connect to Ollama" in str(exc_info.value)


def test_ollama_provider_fallback_to_stub():
    provider = OllamaProvider(base_url="http://localhost:9999", model="llama3.1:8b", fallback_to_stub=True)

    with patch("httpx.Client.post", side_effect=httpx.ConnectError("Connection refused")):
        result = provider.generate("Question: How to optimize postgres?")
        assert "[Stub response]" in result
        assert "optimize postgres" in result


@pytest.mark.asyncio
async def test_ollama_provider_health_check():
    provider = OllamaProvider(base_url="http://localhost:11434", model="llama3.1:8b")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "models": [{"name": "llama3.1:8b"}, {"name": "nomic-embed-text:latest"}]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        health = await provider.acheck_health()
        assert health["status"] == "healthy"
        assert health["provider"] == "ollama"
        assert health["model"] == "llama3.1:8b"
        assert health["model_available"] is True
        assert "llama3.1:8b" in health["available_models"]


# ---------------------------------------------------------------------------
# API Health Endpoint Test
# ---------------------------------------------------------------------------

def test_ollama_health_endpoint():
    client = TestClient(app)
    response = client.get("/api/v1/health/ollama")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["provider"] == "ollama"


# ---------------------------------------------------------------------------
# API Chat Streaming Endpoint Test
# ---------------------------------------------------------------------------

def test_chat_stream_endpoint():
    from uuid import uuid4
    from app.api.deps import get_current_user
    from app.db.dependencies import get_db
    from app.models.user import User

    # Mock authenticated user and db
    mock_user = User(id=uuid4(), email="test@teammemory.local", full_name="Test User")
    mock_db = MagicMock()
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    org_id = str(uuid4())

    mock_events = [
        'data: {"type": "metadata", "citations": [], "retrieved_memory_count": 0, "provider_used": "ollama", "retrieval_mode": "semantic"}\n\n',
        'data: {"type": "token", "token": "Streaming"}\n\n',
        'data: {"type": "token", "token": " answer"}\n\n',
        'data: {"type": "done", "answer": "Streaming answer", "citations": [], "retrieved_memory_count": 0, "provider_used": "ollama", "retrieval_mode": "semantic"}\n\n',
    ]

    with patch("app.memory.rag_generation.stream_rag", return_value=iter(mock_events)):
        try:
            response = client.post(
                "/api/v1/chat/stream",
                json={
                    "organization_id": org_id,
                    "question": "Question: How do we configure streaming?",
                },
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
            
            # Verify SSE structure
            lines = [line for line in response.text.split("\n") if line.startswith("data: ")]
            assert len(lines) >= 2  # metadata, tokens, done

            first_event = json.loads(lines[0][len("data: "):])
            assert first_event["type"] == "metadata"

            last_event = json.loads(lines[-1][len("data: "):])
            assert last_event["type"] == "done"
            assert "answer" in last_event
        finally:
            app.dependency_overrides.pop(get_current_user, None)
            app.dependency_overrides.pop(get_db, None)
