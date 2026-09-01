"""Pydantic schemas for Git Repository Intelligence (Milestone 6.1)."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

class RepositoryCreate(BaseModel):
    organization_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=255)
    remote_url: str = Field(..., min_length=1, max_length=1000)
    default_branch: str = Field(default="main", max_length=255)


class RepositoryRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    remote_url: str
    default_branch: str
    last_synced_at: datetime | None
    last_synced_sha: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# CommitMemory
# ---------------------------------------------------------------------------

class CommitMemoryRead(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    repository_id: uuid.UUID
    memory_entry_id: uuid.UUID | None
    commit_sha: str
    author_name: str | None
    author_email: str | None
    commit_message: str
    committed_at: datetime
    files_changed: int
    insertions: int
    deletions: int
    changed_files: list | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

class RepositorySyncRequest(BaseModel):
    """Request body for POST /git/repositories/{id}/sync."""
    max_commits: int = Field(default=50, ge=1, le=500)


class RepositorySyncResponse(BaseModel):
    repository_id: uuid.UUID
    commits_ingested: int
    commits_skipped: int
    last_synced_sha: str | None
