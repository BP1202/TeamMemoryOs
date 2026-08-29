"""Pydantic schemas for Engineering Conversation Engine (Milestone 6.5)."""
from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.retrieval import CitationRead, GraphPathStepRead


# ---------------------------------------------------------------------------
# Shared engineering response
# ---------------------------------------------------------------------------

class EngineeringResponse(BaseModel):
    """Structured response from the engineering conversation engine."""
    answer: str
    citations: list[CitationRead]
    graph_path: list[GraphPathStepRead]
    confidence: float = Field(..., ge=0.0, le=1.0)
    retrieval_mode: str = "hybrid"
    suggested_actions: list[str]
    provider_used: str


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class EngineeringChatRequest(BaseModel):
    organization_id: uuid.UUID
    question: str = Field(..., min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)
    # Optional routing hints — auto-detected when absent
    mode: Literal["auto", "debug", "architecture", "review", "search", "incident"] = "auto"


# ---------------------------------------------------------------------------
# Debug
# ---------------------------------------------------------------------------

class DebugRequest(BaseModel):
    organization_id: uuid.UUID
    error_message: str = Field(..., min_length=1, max_length=4000)
    stack_trace: str | None = None
    command: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


# ---------------------------------------------------------------------------
# Review (PR Review via conversation)
# ---------------------------------------------------------------------------

class ReviewRequest(BaseModel):
    organization_id: uuid.UUID
    pull_request_id: uuid.UUID | None = None
    diff_text: str | None = None
    title: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)
