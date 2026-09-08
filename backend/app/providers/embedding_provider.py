"""
Production Embedding Provider abstraction and Ollama integration for TeamMemoryOS.

Supports local vector embedding generation using Ollama (`nomic-embed-text`),
integrated with an in-memory SHA-256 LRU cache and automatic fallback for offline use.
"""
from __future__ import annotations

import hashlib
import logging
import math
from typing import Any, Protocol, runtime_checkable

import httpx

from app.cache.embedding_cache import get_embedding_cache
from app.core.settings import settings
from app.models.memory_entry import EMBEDDING_DIM

logger = logging.getLogger(__name__)


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Provider-agnostic protocol for text-to-vector embedding."""

    def embed(self, text: str) -> list[float]:
        """Return a normalised float vector of length ``dimension``."""
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return a list of normalised float vectors."""
        ...

    @property
    def dimension(self) -> int:
        """Embedding dimensionality produced by this provider."""
        ...

    @property
    def provider_name(self) -> str:
        """Human-readable provider identifier."""
        ...

    @property
    def model_name(self) -> str:
        """Name of the embedding model."""
        ...


class StubEmbeddingProvider:
    """Deterministic stub provider — produces normalized vectors from SHA-256 hash.

    Used in unit tests and offline fallback environments without network dependency.
    """

    def __init__(self, dimension: int = EMBEDDING_DIM, model_name: str = "stub-embed") -> None:
        self._dimension = dimension
        self._model_name = model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def provider_name(self) -> str:
        return "stub"

    @property
    def model_name(self) -> str:
        return self._model_name

    def is_available(self) -> bool:
        return True

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        raw = [float(digest[i % len(digest)]) for i in range(self._dimension)]
        magnitude = math.sqrt(sum(v * v for v in raw))
        if magnitude == 0:
            return raw
        return [v / magnitude for v in raw]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


class OllamaEmbeddingProvider:
    """Production local embedding provider powered by Ollama nomic-embed-text."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        dimension: int = EMBEDDING_DIM,
        timeout: float | None = None,
        fallback_to_stub: bool = True,
    ) -> None:
        self._base_url = (base_url or getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self._model = model or getattr(settings, "EMBEDDING_MODEL", "nomic-embed-text")
        self._dimension = dimension
        self._timeout = timeout or getattr(settings, "OLLAMA_TIMEOUT_SECONDS", 60.0)
        self._fallback_to_stub = fallback_to_stub
        self._cache = get_embedding_cache()
        self._stub = StubEmbeddingProvider(dimension=dimension, model_name=f"{self._model}-stub")

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def base_url(self) -> str:
        return self._base_url

    def _normalize_and_pad(self, vector: list[float]) -> list[float]:
        """Align vector dimension to target dimension and apply L2 normalization."""
        if not vector:
            return [0.0] * self._dimension

        # If vector length is smaller than target dimension, pad with zeros
        if len(vector) < self._dimension:
            padded = list(vector) + [0.0] * (self._dimension - len(vector))
        elif len(vector) > self._dimension:
            padded = vector[: self._dimension]
        else:
            padded = list(vector)

        # L2-normalize
        magnitude = math.sqrt(sum(v * v for v in padded))
        if magnitude == 0:
            return padded
        return [v / magnitude for v in padded]

    def embed(self, text: str) -> list[float]:
        """Embed a single text string using cache when possible."""
        normalized_text = text.strip()
        if not normalized_text:
            return [0.0] * self._dimension

        # Check cache
        cached = self._cache.get(normalized_text)
        if cached is not None and len(cached) == self._dimension:
            return cached

        # Call Ollama /api/embeddings
        url = f"{self._base_url}/api/embeddings"
        payload = {
            "model": self._model,
            "prompt": normalized_text,
        }

        logger.info("[OllamaEmbeddingProvider] Embedding text len=%d with model '%s'", len(normalized_text), self._model)

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                raw_embedding = data.get("embedding", [])
                aligned = self._normalize_and_pad(raw_embedding)
                self._cache.set(normalized_text, aligned)
                return aligned
        except httpx.ConnectError as exc:
            logger.warning("[OllamaEmbeddingProvider] Failed to connect to Ollama at %s: %s", self._base_url, exc)
            if self._fallback_to_stub:
                logger.info("[OllamaEmbeddingProvider] Falling back to deterministic stub vector.")
                stub_vec = self._stub.embed(normalized_text)
                self._cache.set(normalized_text, stub_vec)
                return stub_vec
            raise RuntimeError(
                f"Could not connect to Ollama embedding service at {self._base_url}. Is 'ollama serve' running?"
            ) from exc
        except Exception as exc:
            logger.error("[OllamaEmbeddingProvider] Embedding generation error: %s", exc)
            if self._fallback_to_stub:
                stub_vec = self._stub.embed(normalized_text)
                self._cache.set(normalized_text, stub_vec)
                return stub_vec
            raise

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple text strings."""
        return [self.embed(t) for t in texts]

    def is_available(self) -> bool:
        """Check if Ollama embedding model is ready."""
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(f"{self._base_url}/api/tags")
                if resp.status_code == 200:
                    models = [m.get("name") for m in resp.json().get("models", [])]
                    return any(self._model in m or m.startswith(self._model) for m in models)
                return False
        except Exception:
            return False


def get_embedding_provider(
    provider_name: str | None = None,
    dimension: int = EMBEDDING_DIM,
    **kwargs: Any,
) -> EmbeddingProvider:
    """Resolve and return configured EmbeddingProvider instance."""
    target = (provider_name or getattr(settings, "EMBEDDING_PROVIDER", "ollama") or "ollama").lower().strip()

    if target == "ollama":
        return OllamaEmbeddingProvider(dimension=dimension, **kwargs)
    elif target == "stub":
        model_name = kwargs.get("model", "stub-embed")
        return StubEmbeddingProvider(dimension=dimension, model_name=model_name)
    else:
        logger.warning("[EmbeddingFactory] Unknown provider '%s', defaulting to Ollama.", target)
        return OllamaEmbeddingProvider(dimension=dimension, **kwargs)
