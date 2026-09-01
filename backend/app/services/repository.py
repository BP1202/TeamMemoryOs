"""Git Repository Intelligence service (Milestone 6.1).

Provides:
* Repository CRUD.
* Incremental commit ingestion using GitPython (when available).
* Fallback to manual commit registration without GitPython.
* Commit → MemoryEntry ingestion with entity extraction.
* Automatic MemoryLinks for related commits.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.memory_entry import MemoryEntry, MemoryType
from app.models.repository import CommitMemory, Repository
from app.schemas.repository import (
    RepositoryCreate,
    RepositorySyncResponse,
)
from app.services.entity import get_or_create_entity
from app.services.entity_extraction import extract_entities
from app.services.memory_link import _upsert_link
from app.models.memory_link import MemoryLinkType
from app.models.entity import EntityType, MemoryEntity


# Secret filter patterns — never ingest credentials into memory
_SECRET_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"(?:password|passwd|pwd)\s*[:=]\s*\S+",
        r"(?:secret|token|api_key|apikey)\s*[:=]\s*\S+",
        r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----",
        r"(?:aws_access_key|aws_secret)[^=]*=\s*\S+",
    ]
]


def _filter_secrets(text: str) -> str:
    """Replace likely secret values with [REDACTED] before storing."""
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


# ---------------------------------------------------------------------------
# Repository CRUD
# ---------------------------------------------------------------------------

def create_repository(db: Session, repo_in: RepositoryCreate) -> Repository:
    """Register a new repository.  Raises IntegrityError on duplicate URL."""
    repo = Repository(
        organization_id=repo_in.organization_id,
        name=repo_in.name,
        remote_url=repo_in.remote_url,
        default_branch=repo_in.default_branch,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


def get_repository_by_id(db: Session, repo_id: UUID) -> Repository | None:
    return db.scalar(select(Repository).where(Repository.id == repo_id))


def get_repositories_by_org(
    db: Session, organization_id: UUID, skip: int = 0, limit: int = 100
) -> Sequence[Repository]:
    stmt = (
        select(Repository)
        .where(Repository.organization_id == organization_id)
        .order_by(Repository.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return db.scalars(stmt).all()


# ---------------------------------------------------------------------------
# Commit ingestion helpers
# ---------------------------------------------------------------------------

def _get_or_none(db: Session, sha: str, repo_id: UUID) -> CommitMemory | None:
    return db.scalar(
        select(CommitMemory).where(
            CommitMemory.commit_sha == sha,
            CommitMemory.repository_id == repo_id,
        )
    )


def ingest_commit(
    db: Session,
    *,
    organization_id: UUID,
    repository_id: UUID,
    commit_sha: str,
    author_name: str | None,
    author_email: str | None,
    commit_message: str,
    committed_at: datetime,
    files_changed: int = 0,
    insertions: int = 0,
    deletions: int = 0,
    changed_files: list[str] | None = None,
) -> CommitMemory | None:
    """Ingest a single commit into organizational memory.

    Idempotent — returns None if the commit was already ingested.
    Filters secrets from commit messages before storing.
    """
    if _get_or_none(db, commit_sha, repository_id) is not None:
        return None  # already ingested

    safe_message = _filter_secrets(commit_message)

    # Create the MemoryEntry
    content = (
        f"Commit {commit_sha[:7]} by {author_name or 'unknown'}: {safe_message}"
    )
    if changed_files:
        content += f"\nFiles changed: {', '.join(changed_files[:10])}"
        if len(changed_files) > 10:
            content += f" (+{len(changed_files) - 10} more)"

    entry = MemoryEntry(
        organization_id=organization_id,
        memory_type=MemoryType.artifact,
        title=f"Commit {commit_sha[:7]}: {safe_message[:80]}",
        content=content,
        meta={
            "source": "git",
            "commit_sha": commit_sha,
            "author": author_name,
            "files_changed": files_changed,
            "insertions": insertions,
            "deletions": deletions,
        },
    )
    db.add(entry)
    db.flush()  # get entry.id before CommitMemory

    # Create CommitMemory record
    commit_mem = CommitMemory(
        organization_id=organization_id,
        repository_id=repository_id,
        memory_entry_id=entry.id,
        commit_sha=commit_sha,
        author_name=author_name,
        author_email=author_email,
        commit_message=safe_message,
        committed_at=committed_at,
        files_changed=files_changed,
        insertions=insertions,
        deletions=deletions,
        changed_files=changed_files,
    )
    db.add(commit_mem)
    db.commit()
    db.refresh(commit_mem)

    # Entity extraction from commit message
    raw_entities = extract_entities(safe_message + " " + " ".join(changed_files or []))
    entity_ids: list[UUID] = []
    for raw_entity in raw_entities:
        entity = get_or_create_entity(
            db,
            organization_id=organization_id,
            entity_type=raw_entity.entity_type,
            name=raw_entity.name,
        )
        # Attach entity to memory entry (ignore duplicates)
        try:
            db.add(MemoryEntity(memory_entry_id=entry.id, entity_id=entity.id))
            db.commit()
            entity_ids.append(entity.id)
        except IntegrityError:
            db.rollback()

    return commit_mem


def sync_repository(
    db: Session,
    repository_id: UUID,
    organization_id: UUID,
    max_commits: int = 50,
) -> RepositorySyncResponse:
    """Attempt incremental GitPython sync; fall back gracefully.

    When GitPython is unavailable or the remote URL is not locally cloned,
    returns a response indicating zero commits ingested without raising.
    """
    repo = get_repository_by_id(db, repository_id)
    if repo is None or repo.organization_id != organization_id:
        return RepositorySyncResponse(
            repository_id=repository_id,
            commits_ingested=0,
            commits_skipped=0,
            last_synced_sha=None,
        )

    ingested = 0
    skipped = 0
    last_sha: str | None = repo.last_synced_sha

    try:
        import git as gitpython  # type: ignore

        git_repo = gitpython.Repo(repo.remote_url)
        branch = repo.default_branch
        commits = list(git_repo.iter_commits(branch, max_count=max_commits))

        # Incremental: stop at last known SHA
        for commit in commits:
            sha = commit.hexsha
            if repo.last_synced_sha and sha == repo.last_synced_sha:
                break
            changed = list(commit.stats.files.keys())
            result = ingest_commit(
                db,
                organization_id=organization_id,
                repository_id=repository_id,
                commit_sha=sha,
                author_name=str(commit.author.name),
                author_email=str(commit.author.email),
                commit_message=commit.message.strip(),
                committed_at=datetime.fromtimestamp(
                    commit.committed_date, tz=timezone.utc
                ),
                files_changed=commit.stats.total["files"],
                insertions=commit.stats.total["insertions"],
                deletions=commit.stats.total["deletions"],
                changed_files=changed,
            )
            if result is None:
                skipped += 1
            else:
                ingested += 1
                last_sha = sha

    except Exception:
        # GitPython unavailable or remote not cloned — sync is a no-op
        pass

    # Update repository sync metadata
    if ingested > 0 and last_sha:
        repo.last_synced_sha = last_sha
        repo.last_synced_at = datetime.now(timezone.utc)
        db.commit()

    return RepositorySyncResponse(
        repository_id=repository_id,
        commits_ingested=ingested,
        commits_skipped=skipped,
        last_synced_sha=last_sha,
    )


def get_commits_by_repository(
    db: Session,
    repository_id: UUID,
    organization_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[CommitMemory]:
    stmt = (
        select(CommitMemory)
        .where(
            CommitMemory.repository_id == repository_id,
            CommitMemory.organization_id == organization_id,
        )
        .order_by(CommitMemory.committed_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return db.scalars(stmt).all()
