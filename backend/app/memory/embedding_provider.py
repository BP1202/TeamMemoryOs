"""
Embedding provider abstraction for TeamMemoryOS.

Integrates with the production embedding provider subsystem in ``app.providers``.
"""
from __future__ import annotations

from app.models.memory_entry import EMBEDDING_DIM
from app.providers.embedding_provider import (
    EmbeddingProvider,
    OllamaEmbeddingProvider,
    StubEmbeddingProvider,
    get_embedding_provider,
)

__all__ = [
    "EMBEDDING_DIM",
    "EmbeddingProvider",
    "StubEmbeddingProvider",
    "OllamaEmbeddingProvider",
    "get_embedding_provider",
]
