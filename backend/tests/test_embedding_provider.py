"""
Unit and integration tests for Embedding Provider, LRU cache, and Ollama embeddings.
"""
import math
from unittest.mock import MagicMock, patch
from uuid import uuid4

import httpx
import pytest

from app.cache.embedding_cache import EmbeddingCache, get_embedding_cache
from app.core.settings import settings
from app.models.memory_entry import EMBEDDING_DIM
from app.providers.embedding_provider import (
    EmbeddingProvider,
    OllamaEmbeddingProvider,
    StubEmbeddingProvider,
    get_embedding_provider,
)
from app.schemas.memory_entry import MemoryEntryCreate, MemoryType
from app.services.memory_entry import create_memory_entry, store_embedding


# ---------------------------------------------------------------------------
# Embedding Cache Tests
# ---------------------------------------------------------------------------

class TestEmbeddingCache:
    def test_compute_hash_deterministic(self):
        text = "PostgreSQL connection pool optimization"
        h1 = EmbeddingCache.compute_hash(text)
        h2 = EmbeddingCache.compute_hash(text)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex string

    def test_cache_set_and_get(self):
        cache = EmbeddingCache(max_size=10)
        text = "def connect(): pass"
        vec = [0.1] * EMBEDDING_DIM

        chunk_hash = cache.set(text, vec)
        assert chunk_hash == EmbeddingCache.compute_hash(text)

        retrieved = cache.get(text)
        assert retrieved == vec

        retrieved_by_hash = cache.get_by_hash(chunk_hash)
        assert retrieved_by_hash == vec

        assert cache.stats["hits"] == 2
        assert cache.stats["misses"] == 0

    def test_cache_lru_eviction(self):
        cache = EmbeddingCache(max_size=2)
        v = [0.0] * EMBEDDING_DIM

        cache.set("chunk 1", v)
        cache.set("chunk 2", v)
        assert cache.size == 2

        cache.set("chunk 3", v)
        assert cache.size == 2
        assert cache.get("chunk 1") is None
        assert cache.get("chunk 2") is not None
        assert cache.get("chunk 3") is not None


# ---------------------------------------------------------------------------
# Stub Embedding Provider Tests
# ---------------------------------------------------------------------------

class TestStubEmbeddingProvider:
    def test_stub_embedding_dimension_and_normalisation(self):
        provider = StubEmbeddingProvider()
        assert provider.dimension == EMBEDDING_DIM
        assert provider.provider_name == "stub"
        assert provider.is_available() is True

        vec = provider.embed("Architecture Decision Record: pgvector")
        assert len(vec) == EMBEDDING_DIM

        # Magnitude must equal 1.0 (unit vector)
        magnitude = math.sqrt(sum(x * x for x in vec))
        assert abs(magnitude - 1.0) < 1e-5

    def test_stub_embed_batch(self):
        provider = StubEmbeddingProvider()
        texts = ["first chunk", "second chunk"]
        vectors = provider.embed_batch(texts)
        assert len(vectors) == 2
        assert len(vectors[0]) == EMBEDDING_DIM
        assert len(vectors[1]) == EMBEDDING_DIM


# ---------------------------------------------------------------------------
# Ollama Embedding Provider Tests (Mocked HTTP)
# ---------------------------------------------------------------------------

class TestOllamaEmbeddingProvider:
    def test_ollama_embed_success_with_padding_and_normalisation(self):
        provider = OllamaEmbeddingProvider(
            base_url="http://localhost:11434",
            model="nomic-embed-text",
            dimension=EMBEDDING_DIM,
        )
        assert provider.provider_name == "ollama"
        assert provider.model_name == "nomic-embed-text"

        # Simulate Ollama returning 768-dim nomic-embed-text vector
        raw_768 = [0.1] * 768
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"embedding": raw_768}

        with patch("httpx.Client.post", return_value=mock_resp):
            vec = provider.embed("Indexing database schema")
            assert len(vec) == EMBEDDING_DIM
            # Vector should be padded and normalized to magnitude 1.0
            magnitude = math.sqrt(sum(x * x for x in vec))
            assert abs(magnitude - 1.0) < 1e-5

    def test_ollama_embedding_cache_hit_skips_network(self):
        provider = OllamaEmbeddingProvider()
        text = "Cached embedding test query"
        cache = get_embedding_cache()
        cache.clear()

        raw_768 = [0.2] * 768
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"embedding": raw_768}

        with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
            # First call — triggers network and caches
            v1 = provider.embed(text)
            assert mock_post.call_count == 1

            # Second call — hits cache, network not called again
            v2 = provider.embed(text)
            assert mock_post.call_count == 1
            assert v1 == v2

    def test_ollama_embed_fallback_to_stub_on_connection_error(self):
        provider = OllamaEmbeddingProvider(
            base_url="http://localhost:9999",
            fallback_to_stub=True,
        )
        cache = get_embedding_cache()
        cache.clear()

        with patch("httpx.Client.post", side_effect=httpx.ConnectError("Ollama offline")):
            vec = provider.embed("Offline query")
            assert len(vec) == EMBEDDING_DIM
            magnitude = math.sqrt(sum(x * x for x in vec))
            assert abs(magnitude - 1.0) < 1e-5

    def test_ollama_embed_raises_when_no_fallback(self):
        provider = OllamaEmbeddingProvider(
            base_url="http://localhost:9999",
            fallback_to_stub=False,
        )
        cache = get_embedding_cache()
        cache.clear()

        with patch("httpx.Client.post", side_effect=httpx.ConnectError("Ollama offline")):
            with pytest.raises(RuntimeError) as exc_info:
                provider.embed("Offline query without fallback")
            assert "Could not connect to Ollama embedding service" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Factory & Integration Tests
# ---------------------------------------------------------------------------

class TestEmbeddingFactory:
    def test_factory_resolves_ollama(self):
        provider = get_embedding_provider("ollama")
        assert isinstance(provider, OllamaEmbeddingProvider)
        assert provider.provider_name == "ollama"

    def test_factory_resolves_stub(self):
        provider = get_embedding_provider("stub")
        assert isinstance(provider, StubEmbeddingProvider)
        assert provider.provider_name == "stub"

    def test_factory_defaults_to_settings(self):
        with patch.object(settings, "EMBEDDING_PROVIDER", "stub"):
            provider = get_embedding_provider()
            assert isinstance(provider, StubEmbeddingProvider)


class TestMemoryEntryAutoEmbedding:
    def test_create_memory_entry_populates_chunk_hash_and_embedding(self):
        mock_db = MagicMock()
        entry_in = MemoryEntryCreate(
            organization_id=uuid4(),
            memory_type=MemoryType.decision,
            title="ADR: Use nomic-embed-text",
            content="We use nomic-embed-text for 768-dim embeddings padded to pgvector.",
        )

        entry = create_memory_entry(mock_db, entry_in, auto_embed=True)
        assert entry.meta is not None
        assert "chunk_hash" in entry.meta
        assert len(entry.meta["chunk_hash"]) == 64
        assert entry.embedding is not None
        assert len(entry.embedding) == EMBEDDING_DIM
