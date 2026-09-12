"""Data models and schemas for Intelligent Chunking Engine.

Defines:
- ChunkingStrategy: enum of supported chunking strategies
- ChunkMetadata: structured metadata associated with a chunk (header hierarchy, code symbols, parent-child links)
- Chunk: individual text chunk with spans, SHA-256 hash, token count, and metadata
- ChunkingConfig: operational parameters (chunk size, overlap, hierarchical mode, separators)
- ChunkResult: collection of generated chunks with summary stats and deduplication counters
"""
from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class ChunkingStrategy(str, Enum):
    """Supported chunking strategies."""
    RECURSIVE = "recursive"
    MARKDOWN = "markdown"
    CODE = "code"
    FIXED = "fixed"
    AUTO = "auto"


class ChunkMetadata(BaseModel):
    """Metadata attached to an individual chunk for enriched retrieval."""
    model_config = ConfigDict(extra="allow")

    source: str | None = Field(default=None, description="Source format or origin (e.g., markdown, code, document, adr, pr, incident)")
    file_path: str | None = Field(default=None, description="File path if chunk was extracted from a repository file")
    language: str | None = Field(default=None, description="Programming or markup language (e.g. python, typescript, markdown)")
    section_header: str | None = Field(default=None, description="Immediate parent markdown header or section title")
    header_hierarchy: list[str] = Field(default_factory=list, description="List of markdown header breadcrumbs (e.g., ['# Architecture', '## Database'])")
    symbol_name: str | None = Field(default=None, description="AST symbol name (e.g. function, class, method name)")
    chunk_type: str | None = Field(default=None, description="Classification (e.g. function, class, markdown_section, paragraph, code_block, list, block)")
    parent_id: str | None = Field(default=None, description="Parent chunk identifier if generated via hierarchical chunking")
    parent_hash: str | None = Field(default=None, description="Parent chunk SHA-256 hash for parent-child retrieval")
    is_parent: bool = Field(default=False, description="True if this chunk serves as a parent chunk")
    extra: dict[str, Any] = Field(default_factory=dict, description="Additional custom metadata key-values")


class Chunk(BaseModel):
    """An individual semantic chunk with location tracking and SHA-256 integrity hash."""
    model_config = ConfigDict(extra="allow")

    content: str = Field(..., description="The chunk text content")
    chunk_index: int = Field(..., description="0-indexed position of the chunk in the document sequence")
    chunk_hash: str = Field(..., description="SHA-256 digest of normalized chunk content")
    start_char: int = Field(default=0, description="Start character offset in original document")
    end_char: int = Field(default=0, description="End character offset in original document")
    start_line: int = Field(default=1, description="1-indexed starting line number in original document")
    end_line: int = Field(default=1, description="1-indexed ending line number in original document")
    token_count: int = Field(default=0, description="Estimated token count for prompt budgeting")
    metadata: ChunkMetadata = Field(default_factory=ChunkMetadata, description="Associated rich metadata")
    parent_chunk_hash: str | None = Field(default=None, description="SHA-256 hash of parent chunk if hierarchical")
    is_duplicate: bool = Field(default=False, description="True if this chunk hash has already been seen/processed")


class ChunkingConfig(BaseModel):
    """Configuration options for chunking operations."""
    chunk_size: int = Field(default=1000, ge=1, description="Target maximum character size per chunk")
    chunk_overlap: int = Field(default=200, ge=0, description="Sliding window character overlap between consecutive chunks")
    min_chunk_size: int = Field(default=50, ge=1, description="Minimum character size to keep as an independent chunk")
    strategy: ChunkingStrategy = Field(default=ChunkingStrategy.AUTO, description="Chunking strategy to apply")
    separators: list[str] | None = Field(default=None, description="Custom separators for recursive chunking in priority order")
    language: str | None = Field(default=None, description="Code language for code chunker (python, typescript, go, rust, sql, etc.)")
    preserve_headers: bool = Field(default=True, description="Whether markdown chunker should embed header hierarchy in chunk content/meta")
    hierarchical: bool = Field(default=False, description="Whether to produce parent (context) chunks alongside child (search) chunks")
    parent_chunk_size: int = Field(default=2500, ge=1, description="Target character size for parent context chunks")
    parent_chunk_overlap: int = Field(default=400, ge=0, description="Overlap for parent context chunks")


class ChunkResult(BaseModel):
    """Result of a chunking run across a document or file."""
    chunks: list[Chunk] = Field(default_factory=list, description="List of generated chunks")
    total_chunks: int = Field(default=0, description="Total number of valid chunks created")
    strategy_used: str = Field(..., description="The chunking strategy that was executed")
    document_hash: str = Field(..., description="SHA-256 digest of the full input document")
    duplicate_chunks_skipped: int = Field(default=0, description="Number of duplicate chunk hashes omitted or flagged")
    execution_time_ms: float = Field(default=0.0, description="Execution time in milliseconds")
