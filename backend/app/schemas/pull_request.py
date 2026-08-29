"""Pydantic schemas for PR Guardian (Milestone 6.2)."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.pull_request import PRStatus


# ---------------------------------------------------------------------------
# PullRequest
# ---------------------------------------------------------------------------

class PullRequestCreate(BaseModel):
    organization_id: uuid.UUID
    repository_id: uuid.UUID
    pr_number: int = Field(..., ge=1)
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    author: str | None = None
    source_branch: str | None = None
    target_branch: str | None = None
    status: PRStatus = PRStatus.open
    diff_text: str | None = None
    changed_files: list[str] | None = None
    files_changed: int = Field(default=0, ge=0)


class PullRequestRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    repository_id: uuid.UUID
    memory_entry_id: uuid.UUID | None
    pr_number: int
    title: str
    description: str | None
    author: str | None
    source_branch: str | None
    target_branch: str | None
    status: str
    changed_files: list | None
    files_changed: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# PullRequestReview
# ---------------------------------------------------------------------------

class PullRequestReviewRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    pull_request_id: uuid.UUID
    summary: str | None
    risk_score: float
    risk_factors: list | None
    suggestions: list | None
    citations: list | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PRReviewRequest(BaseModel):
    """Request body for POST /git/pull-requests/{id}/review."""
    top_k: int = Field(default=5, ge=1, le=20)


class PRRiskResponse(BaseModel):
    pull_request_id: uuid.UUID
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_factors: list[str]
    explanation: str
