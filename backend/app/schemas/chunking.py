"""Pydantic schemas for chunking API endpoints."""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from app.chunking.chunk_models import ChunkingStrategy


class ChunkPreviewRequest(BaseModel):
    """Request payload to preview text chunking without database persistence."""
    content: str = Field(..., description="The raw document, markdown, or code content to split")
    strategy: ChunkingStrategy = Field(default=ChunkingStrategy.AUTO, description="Chunking strategy (recursive, markdown, code, auto)")
    chunk_size: int = Field(default=1000, ge=50, le=10000, description="Target chunk size in characters")
    chunk_overlap: int = Field(default=200, ge=0, le=2000, description="Overlap between consecutive chunks in characters")
    min_chunk_size: int = Field(default=50, ge=10, description="Minimum characters for a stand-alone chunk")
    language: str | None = Field(default=None, description="Programming or markup language hint")
    file_path: str | None = Field(default=None, description="File path hint (used for language / strategy detection)")
    hierarchical: bool = Field(default=False, description="Enable parent-child two-tier chunking")
    preserve_headers: bool = Field(default=True, description="Preserve markdown header breadcrumb hierarchy in chunks")


class ChunkPreviewItem(BaseModel):
    """Preview of a single generated chunk."""
    chunk_index: int = Field(..., description="Sequential index of the chunk")
    chunk_hash: str = Field(..., description="SHA-256 integrity hash")
    content: str = Field(..., description="Chunk text content")
    token_count: int = Field(..., description="Estimated token count")
    start_char: int = Field(..., description="Starting character offset")
    end_char: int = Field(..., description="Ending character offset")
    start_line: int = Field(..., description="Starting line number (1-indexed)")
    end_line: int = Field(..., description="Ending line number (1-indexed)")
    symbol_name: str | None = Field(default=None, description="Extracted symbol name (function/class) if code chunk")
    section_header: str | None = Field(default=None, description="Governing section header if markdown chunk")
    header_hierarchy: list[str] = Field(default_factory=list, description="Markdown breadcrumbs")
    parent_chunk_hash: str | None = Field(default=None, description="SHA-256 hash of parent chunk if hierarchical")
    is_parent: bool = Field(default=False, description="True if this is a parent context chunk")
    is_duplicate: bool = Field(default=False, description="True if marked as a duplicate")


class ChunkPreviewResponse(BaseModel):
    """Response returned by chunk preview endpoint."""
    strategy_used: str = Field(..., description="The chunking strategy applied")
    document_hash: str = Field(..., description="SHA-256 digest of input document")
    total_chunks: int = Field(..., description="Total valid chunks produced")
    duplicate_chunks_skipped: int = Field(default=0, description="Number of duplicate chunks skipped")
    execution_time_ms: float = Field(default=0.0, description="Execution time in milliseconds")
    chunks: list[ChunkPreviewItem] = Field(default_factory=list, description="List of generated chunk previews")
