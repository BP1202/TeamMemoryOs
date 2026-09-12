"""Git Repository Intelligence API — Milestone 6.1 & AI-004.

Routes:
* POST /git/repositories/                             — Register repository
* GET  /git/repositories/                             — List repositories
* POST /git/repositories/{id}/sync                    — Sync repository commits
* GET  /git/repositories/{id}/commits                 — List commits
* GET  /git/repositories/{id}/health                  — Repository health & git stats
* GET  /git/repositories/{id}/branches                — List repository branches
* GET  /git/repositories/{id}/tags                    — List repository tags
* GET  /git/repositories/{id}/diff                    — Diff revisions / working tree
* POST /git/repositories/{id}/index-incremental       — Incremental indexing with hash reuse
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.repository import (
    BranchRead,
    CommitMemoryRead,
    DiffResponse,
    IncrementalIndexRequest,
    IncrementalIndexResponse,
    RepositoryCreate,
    RepositoryHealthResponse,
    RepositoryRead,
    RepositorySyncRequest,
    RepositorySyncResponse,
    TagRead,
)
from app.services.repository import (
    create_repository,
    get_commits_by_repository,
    get_repositories_by_org,
    get_repository_branches,
    get_repository_by_id,
    get_repository_diff,
    get_repository_health,
    get_repository_tags,
    incremental_index_repository,
    sync_repository,
)

router = APIRouter()


@router.post("/repositories/", response_model=RepositoryRead, status_code=status.HTTP_201_CREATED)
def register_repository(
    body: RepositoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a new Git repository for memory ingestion."""
    try:
        return create_repository(db, body)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A repository with this URL is already registered for this organisation.",
        )


@router.get("/repositories/", response_model=list[RepositoryRead])
def list_repositories(
    organization_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all registered repositories for an organisation."""
    return get_repositories_by_org(db, organization_id, skip=skip, limit=limit)


@router.post("/repositories/{repository_id}/sync", response_model=RepositorySyncResponse)
def sync_repo(
    repository_id: UUID,
    body: RepositorySyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger an incremental sync of commits from a repository."""
    repo = get_repository_by_id(db, repository_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return sync_repository(
        db,
        repository_id=repository_id,
        organization_id=repo.organization_id,
        max_commits=body.max_commits,
    )


@router.get("/repositories/{repository_id}/commits", response_model=list[CommitMemoryRead])
def list_commits(
    repository_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List ingested commits for a repository."""
    repo = get_repository_by_id(db, repository_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return get_commits_by_repository(
        db,
        repository_id=repository_id,
        organization_id=repo.organization_id,
        skip=skip,
        limit=limit,
    )


@router.get("/repositories/{repository_id}/health", response_model=RepositoryHealthResponse)
def get_repo_health(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get repository health, git status, branch counts, and clean/dirty state."""
    repo = get_repository_by_id(db, repository_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return get_repository_health(db, repository_id, repo.organization_id)


@router.get("/repositories/{repository_id}/branches", response_model=list[BranchRead])
def list_branches(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all local and remote branches in the repository."""
    repo = get_repository_by_id(db, repository_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return get_repository_branches(db, repository_id, repo.organization_id)


@router.get("/repositories/{repository_id}/tags", response_model=list[TagRead])
def list_tags(
    repository_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all tags in the repository."""
    repo = get_repository_by_id(db, repository_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return get_repository_tags(db, repository_id, repo.organization_id)


@router.get("/repositories/{repository_id}/diff", response_model=DiffResponse)
def get_diff(
    repository_id: UUID,
    base_ref: str | None = Query(default=None, description="Base commit/branch SHA or name"),
    target_ref: str | None = Query(default=None, description="Target commit/branch SHA or name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get diff summary of changed files between revisions or working directory."""
    repo = get_repository_by_id(db, repository_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return get_repository_diff(db, repository_id, repo.organization_id, base_ref, target_ref)


@router.post("/repositories/{repository_id}/index-incremental", response_model=IncrementalIndexResponse)
def index_repo_incremental(
    repository_id: UUID,
    body: IncrementalIndexRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run incremental indexing with SHA-256 chunk hash reuse on modified files."""
    repo = get_repository_by_id(db, repository_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return incremental_index_repository(db, repository_id, repo.organization_id, body)
