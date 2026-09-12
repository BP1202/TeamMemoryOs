"""Intelligent Chunking Engine for TeamMemoryOS.

Provides semantic, metadata-rich chunking for Markdown documents, source code,
and general engineering text with SHA-256 incremental hashing and duplicate elimination.
"""
from __future__ import annotations

import re
from typing import Any

from app.chunking.base_chunker import BaseChunker
from app.chunking.chunk_metadata import chunk_to_memory_meta, enrich_metadata
from app.chunking.chunk_models import (
    Chunk,
    ChunkingConfig,
    ChunkingStrategy,
    ChunkMetadata,
    ChunkResult,
)
from app.chunking.code_chunker import CodeChunker
from app.chunking.markdown_chunker import MarkdownChunker
from app.chunking.recursive_chunker import RecursiveChunker

__all__ = [
    "BaseChunker",
    "RecursiveChunker",
    "MarkdownChunker",
    "CodeChunker",
    "Chunk",
    "ChunkMetadata",
    "ChunkingConfig",
    "ChunkingStrategy",
    "ChunkResult",
    "enrich_metadata",
    "chunk_to_memory_meta",
    "get_chunker",
    "chunk_text",
]

_RECURSIVE_CHUNKER = RecursiveChunker()
_MARKDOWN_CHUNKER = MarkdownChunker()
_CODE_CHUNKER = CodeChunker()


def get_chunker(strategy: ChunkingStrategy | str) -> BaseChunker:
    """Return the chunker instance for the requested strategy."""
    strat = ChunkingStrategy(strategy) if isinstance(strategy, str) else strategy
    if strat == ChunkingStrategy.MARKDOWN:
        return _MARKDOWN_CHUNKER
    elif strat == ChunkingStrategy.CODE:
        return _CODE_CHUNKER
    else:
        return _RECURSIVE_CHUNKER


def detect_strategy(
    text: str,
    metadata: ChunkMetadata | dict[str, Any] | None = None,
    language: str | None = None,
) -> ChunkingStrategy:
    """Infer optimal chunking strategy from file extension or content patterns."""
    file_path = ""
    if isinstance(metadata, ChunkMetadata) and metadata.file_path:
        file_path = metadata.file_path
    elif isinstance(metadata, dict) and metadata.get("file_path"):
        file_path = str(metadata["file_path"])

    if file_path:
        lower_path = file_path.lower()
        if lower_path.endswith((".md", ".markdown", ".mdx")):
            return ChunkingStrategy.MARKDOWN
        if lower_path.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".c", ".cpp", ".sql", ".sh")):
            return ChunkingStrategy.CODE

    if language:
        lang = language.lower()
        if lang in ("markdown", "md"):
            return ChunkingStrategy.MARKDOWN
        if lang in ("python", "typescript", "javascript", "go", "rust", "java", "c", "cpp", "sql", "bash", "code"):
            return ChunkingStrategy.CODE

    # Content-based heuristics
    stripped = text.strip()
    if re.search(r"^#{1,6}\s+", stripped, re.MULTILINE):
        return ChunkingStrategy.MARKDOWN

    if re.search(r"^(?:import\s+|def\s+|class\s+|export\s+|func\s+|fn\s+|CREATE\s+TABLE)", stripped, re.MULTILINE):
        return ChunkingStrategy.CODE

    return ChunkingStrategy.RECURSIVE


def chunk_text(
    text: str,
    strategy: ChunkingStrategy | str = ChunkingStrategy.AUTO,
    metadata: ChunkMetadata | dict[str, Any] | None = None,
    config: ChunkingConfig | None = None,
) -> ChunkResult:
    """Main entrypoint: split text into semantic chunks with metadata and hashing."""
    strat = ChunkingStrategy(strategy) if isinstance(strategy, str) else strategy

    if strat == ChunkingStrategy.AUTO:
        strat = detect_strategy(
            text,
            metadata=metadata,
            language=config.language if config else None,
        )

    chunker = get_chunker(strat)
    cfg = config or ChunkingConfig(strategy=strat)
    if cfg.strategy != strat:
        cfg = cfg.model_copy(update={"strategy": strat})

    return chunker.chunk(text=text, metadata=metadata, config=cfg)
