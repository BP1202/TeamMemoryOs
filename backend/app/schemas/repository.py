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


# ---------------------------------------------------------------------------
# Git Intelligence & Health (AI-004)
# ---------------------------------------------------------------------------

class BranchRead(BaseModel):
    name: str
    commit_sha: str
    is_active: bool = False
    is_remote: bool = False
    tracking_branch: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TagRead(BaseModel):
    name: str
    commit_sha: str
    tagger_name: str | None = None
    tagger_email: str | None = None
    tagged_at: datetime | None = None
    message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DiffEntryRead(BaseModel):
    file_path: str
    old_path: str | None = None
    change_type: str
    insertions: int = 0
    deletions: int = 0
    old_blob_sha: str | None = None
    new_blob_sha: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DiffResponse(BaseModel):
    base_ref: str | None = None
    target_ref: str | None = None
    changed_files: list[DiffEntryRead] = Field(default_factory=list)
    total_files: int = 0
    total_insertions: int = 0
    total_deletions: int = 0

    model_config = ConfigDict(from_attributes=True)


class RepositoryHealthResponse(BaseModel):
    is_valid_git: bool
    path: str
    default_branch: str
    current_branch: str | None = None
    total_commits: int = 0
    total_branches: int = 0
    total_tags: int = 0
    is_clean: bool = True
    uncommitted_changes: int = 0
    last_commit_sha: str | None = None
    last_commit_date: datetime | None = None
    last_commit_message: str | None = None
    storage_size_bytes: int = 0
    error: str | None = None

    model_config = ConfigDict(from_attributes=True)


class IncrementalIndexRequest(BaseModel):
    force_full: bool = False
    file_extensions: list[str] = Field(
        default=[".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".rs", ".sql", ".md"],
        description="File extensions to index.",
    )
    max_files: int = Field(default=500, ge=1, le=2000)


class IncrementalIndexResponse(BaseModel):
    repository_id: uuid.UUID
    is_incremental: bool
    base_sha: str | None
    target_sha: str | None
    total_files_scanned: int
    files_indexed: int
    files_skipped_unchanged: int
    files_deleted: int
    total_chunks: int
    new_chunks: int
    reused_chunks: int
    duration_seconds: float

    model_config = ConfigDict(from_attributes=True)

