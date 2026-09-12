"""Abstract base class and core utilities for Chunking Engine."""
from __future__ import annotations

import hashlib
import re
import time
from abc import ABC, abstractmethod
from typing import Any

from app.chunking.chunk_models import Chunk, ChunkingConfig, ChunkingStrategy, ChunkMetadata, ChunkResult


class BaseChunker(ABC):
    """Abstract Base Class for all specialized Chunkers."""

    @staticmethod
    def compute_hash(text: str) -> str:
        """Compute SHA-256 digest of normalized text."""
        normalized = text.strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count for text.
        
        Uses standard approximation: ~4 characters per token or word count + punctuation heuristic.
        """
        if not text:
            return 0
        # Words + punctuation tokens
        words = len(re.findall(r"\w+|[^\w\s]", text, re.UNICODE))
        char_estimate = max(1, len(text) // 4)
        return max(words, char_estimate)

    @staticmethod
    def locate_span(full_text: str, substring: str, start_search: int = 0) -> tuple[int, int, int, int]:
        """Locate start_char, end_char, start_line, end_line of substring in full_text."""
        if not substring or not full_text:
            return 0, 0, 1, 1

        idx = full_text.find(substring, start_search)
        if idx == -1:
            idx = full_text.find(substring.strip())
            if idx == -1:
                idx = start_search

        start_char = idx
        end_char = idx + len(substring)

        start_line = full_text.count("\n", 0, start_char) + 1
        end_line = full_text.count("\n", 0, end_char) + 1

        return start_char, end_char, start_line, end_line

    @staticmethod
    def deduplicate_chunks(chunks: list[Chunk]) -> tuple[list[Chunk], int]:
        """Filter out duplicate chunks based on their SHA-256 hash while maintaining order."""
        seen_hashes: set[str] = set()
        unique_chunks: list[Chunk] = []
        duplicates_skipped = 0

        for idx, ch in enumerate(chunks):
            if ch.chunk_hash in seen_hashes:
                duplicates_skipped += 1
                ch.is_duplicate = True
            else:
                seen_hashes.add(ch.chunk_hash)
                # Re-index unique chunks sequentially
                ch.chunk_index = len(unique_chunks)
                unique_chunks.append(ch)

        return unique_chunks, duplicates_skipped

    @abstractmethod
    def chunk(
        self,
        text: str,
        metadata: ChunkMetadata | dict[str, Any] | None = None,
        config: ChunkingConfig | None = None,
    ) -> ChunkResult:
        """Split input text into semantic chunks according to config."""
        pass
