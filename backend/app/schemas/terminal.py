"""Pydantic schemas for Terminal Memory Copilot (Milestone 6.3)."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.terminal import ErrorSeverity


# ---------------------------------------------------------------------------
# TerminalSession
# ---------------------------------------------------------------------------

class TerminalSessionCreate(BaseModel):
    organization_id: uuid.UUID
    raw_output: str = Field(..., min_length=1, max_length=50_000)
    command: str | None = Field(default=None, max_length=1000)
    working_directory: str | None = Field(default=None, max_length=500)


class TerminalSessionRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    submitted_by_user_id: uuid.UUID | None
    raw_output: str
    command: str | None
    working_directory: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# TerminalError
# ---------------------------------------------------------------------------

class TerminalErrorRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    session_id: uuid.UUID
    memory_entry_id: uuid.UUID | None
    error_type: str
    error_message: str
    severity: str
    suggested_fixes: list | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Upload / Search
# ---------------------------------------------------------------------------

class TerminalUploadResponse(BaseModel):
    session_id: uuid.UUID
    errors_found: int
    errors_ingested: int
    memory_entries_created: int


class TerminalSearchRequest(BaseModel):
    organization_id: uuid.UUID
    error_message: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class TerminalFixResult(BaseModel):
    error_type: str
    error_message: str
    fix_description: str
    confidence: float
    source_session_id: uuid.UUID | None


class TerminalSearchResponse(BaseModel):
    query: str
    organization_id: uuid.UUID
    fixes: list[TerminalFixResult]
    explanation: str
