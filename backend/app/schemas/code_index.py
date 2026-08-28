"""Pydantic schemas for AI Codebase Search (Milestone 6.4)."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# CodeFile
# ---------------------------------------------------------------------------

class CodeFileRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    repository_id: uuid.UUID
    file_path: str
    language: str | None
    size_bytes: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# CodeChunk
# ---------------------------------------------------------------------------

class CodeChunkRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    code_file_id: uuid.UUID
    memory_entry_id: uuid.UUID | None
    chunk_type: str
    symbol_name: str | None
    content: str
    start_line: int
    end_line: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Index / Search
# ---------------------------------------------------------------------------

class CodeIndexRequest(BaseModel):
    """Request body for POST /code/repositories/{id}/index."""
    file_extensions: list[str] = Field(
        default=[".py", ".ts", ".js", ".go", ".java", ".rs"],
        description="File extensions to index.",
    )
    max_files: int = Field(default=200, ge=1, le=2000)


class CodeIndexResponse(BaseModel):
    repository_id: uuid.UUID
    files_indexed: int
    chunks_created: int
    files_skipped: int


class CodeSearchRequest(BaseModel):
    organization_id: uuid.UUID
    query: str = Field(..., min_length=1, max_length=2000)
    repository_id: uuid.UUID | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class CodeSearchResult(BaseModel):
    chunk_id: uuid.UUID
    file_path: str
    language: str | None
    symbol_name: str | None
    chunk_type: str
    content: str
    start_line: int
    end_line: int
    score: float
    explanation: str


class CodeSearchResponse(BaseModel):
    query: str
    organization_id: uuid.UUID
    results: list[CodeSearchResult]
    result_count: int
