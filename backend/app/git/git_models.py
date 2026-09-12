"""Git Domain Models and Data Structures for Repository Intelligence (AI-004)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class FileChangeType(str, Enum):
    """Classification of changes made to a file across Git revisions."""
    ADDED = "A"
    MODIFIED = "M"
    DELETED = "D"
    RENAMED = "R"
    COPIED = "C"
    UNTRACKED = "U"
    UNKNOWN = "?"


class GitDiffEntry(BaseModel):
    """Represents a diff for a single file between commits/trees."""
    file_path: str
    old_path: str | None = None
    change_type: FileChangeType = FileChangeType.MODIFIED
    insertions: int = 0
    deletions: int = 0
    old_blob_sha: str | None = None
    new_blob_sha: str | None = None
    is_binary: bool = False

    model_config = ConfigDict(from_attributes=True)


class GitDiffSummary(BaseModel):
    """Aggregate summary of a diff comparison between refs or working tree."""
    base_ref: str | None = None
    target_ref: str | None = None
    changed_files: list[GitDiffEntry] = Field(default_factory=list)
    total_files: int = 0
    total_insertions: int = 0
    total_deletions: int = 0

    model_config = ConfigDict(from_attributes=True)


class GitCommitInfo(BaseModel):
    """Metadata and statistics for a single Git commit."""
    commit_sha: str
    author_name: str | None = None
    author_email: str | None = None
    committed_at: datetime
    message: str
    summary: str
    parent_shas: list[str] = Field(default_factory=list)
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0
    changed_files: list[str] = Field(default_factory=list)
    conventional_type: str | None = None
    issue_references: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class GitBranchInfo(BaseModel):
    """Information about a Git branch."""
    name: str
    commit_sha: str
    is_active: bool = False
    is_remote: bool = False
    tracking_branch: str | None = None

    model_config = ConfigDict(from_attributes=True)


class GitTagInfo(BaseModel):
    """Information about a Git tag."""
    name: str
    commit_sha: str
    tagger_name: str | None = None
    tagger_email: str | None = None
    tagged_at: datetime | None = None
    message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RepositoryHealth(BaseModel):
    """Status and health metrics of a local Git repository."""
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


class IncrementalIndexResult(BaseModel):
    """Result of full or incremental repository indexing."""
    repository_id: UUID
    is_incremental: bool = True
    base_sha: str | None = None
    target_sha: str | None = None
    total_files_scanned: int = 0
    files_indexed: int = 0
    files_skipped_unchanged: int = 0
    files_deleted: int = 0
    total_chunks: int = 0
    new_chunks: int = 0
    reused_chunks: int = 0
    duration_seconds: float = 0.0

    model_config = ConfigDict(from_attributes=True)
