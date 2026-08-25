"""
Embedding provider abstraction for TeamMemoryOS.

Defines the ``EmbeddingProvider`` protocol so any concrete implementation
(IBM Granite, OpenAI, sentence-transformers, …) can be swapped behind the
same interface without touching retrieval or RAG logic.

Also provides a ``StubEmbeddingProvider`` that returns a deterministic,
normalised vector from a hash of the input text.  This lets the full
retrieval pipeline be exercised in tests and development without any AI
service or network dependency.
"""
from __future__ import annotations

import hashlib
import math
from typing import Protocol, runtime_checkable

from app.models.memory_entry import EMBEDDING_DIM


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Provider-agnostic contract for text-to-vector embedding."""

    def embed(self, text: str) -> list[float]:
        """Return a normalised float vector of length ``EMBEDDING_DIM``."""
        ...

    @property
    def dimension(self) -> int:
        """Embedding dimension produced by this provider."""
        ...


class StubEmbeddingProvider:
    """Deterministic stub — no network, no model, no cost.

    Produces a unit-normalised vector whose components are derived from a
    SHA-256 hash of the input text, seeded with each byte of the digest
    cycling through ``EMBEDDING_DIM`` positions.  Two identical strings
    always return the same vector; similar strings return similar-but-not-
    identical vectors (no semantic meaning — only for testing the pipeline).
    """

    @property
    def dimension(self) -> int:
        return EMBEDDING_DIM

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()  # 32 bytes
        # Build EMBEDDING_DIM raw floats by cycling through the digest bytes.
        raw: list[float] = [
            float(digest[i % len(digest)]) for i in range(EMBEDDING_DIM)
        ]
        # L2-normalise so the vector lies on the unit sphere (required for
        # cosine similarity to equal the dot product).
        magnitude = math.sqrt(sum(v * v for v in raw))
        if magnitude == 0:
            return raw  # shouldn't happen with SHA-256, but guard anyway
        return [v / magnitude for v in raw]
