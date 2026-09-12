"""
In-memory LRU Embedding Cache for TeamMemoryOS.

Caches text-to-vector embeddings keyed by SHA-256 chunk hash to prevent
redundant generation calls to Ollama for duplicate code or memory chunks.
"""
from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict
from typing import Any

from app.core.settings import settings


class EmbeddingCache:
    """Thread-safe LRU cache for embedding vectors keyed by SHA-256 hash."""

    def __init__(self, max_size: int | None = None) -> None:
        self._max_size = max_size or getattr(settings, "EMBEDDING_CACHE_SIZE", 5000)
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    @staticmethod
    def compute_hash(text: str) -> str:
        """Calculate the SHA-256 digest of input text."""
        normalized = text.strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def get(self, text: str) -> list[float] | None:
        """Lookup embedding by raw text using its SHA-256 hash."""
        chunk_hash = self.compute_hash(text)
        return self.get_by_hash(chunk_hash)

    def get_by_hash(self, chunk_hash: str) -> list[float] | None:
        """Lookup embedding directly by chunk SHA-256 hash."""
        with self._lock:
            if chunk_hash in self._cache:
                self._cache.move_to_end(chunk_hash)
                self._hits += 1
                return list(self._cache[chunk_hash])
            self._misses += 1
            return None

    def set(
        self,
        text: str,
        embedding: list[float],
        chunk_hash: str | None = None,
    ) -> str:
        """Store an embedding vector in the cache.

        Returns the calculated or provided chunk SHA-256 hash.
        """
        h = chunk_hash or self.compute_hash(text)
        with self._lock:
            if h in self._cache:
                self._cache.move_to_end(h)
            else:
                if len(self._cache) >= self._max_size:
                    self._cache.popitem(last=False)
            self._cache[h] = list(embedding)
        return h

    def clear(self) -> None:
        """Clear all cached embeddings and reset stats."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    @property
    def size(self) -> int:
        """Current number of cached embeddings."""
        with self._lock:
            return len(self._cache)

    @property
    def stats(self) -> dict[str, Any]:
        """Cache operational statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 4),
            }


_GLOBAL_CACHE: EmbeddingCache | None = None
_INIT_LOCK = threading.Lock()


def get_embedding_cache() -> EmbeddingCache:
    """Return the global EmbeddingCache singleton."""
    global _GLOBAL_CACHE
    if _GLOBAL_CACHE is None:
        with _INIT_LOCK:
            if _GLOBAL_CACHE is None:
                _GLOBAL_CACHE = EmbeddingCache()
    return _GLOBAL_CACHE
