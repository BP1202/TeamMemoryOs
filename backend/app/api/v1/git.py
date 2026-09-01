"""Git Repository Intelligence API — Milestone 6.1.

Routes:
* POST /git/repositories/                   — Register repository
* GET  /git/repositories/                   — List repositories
* POST /git/repositories/{id}/sync          — Sync repository
* GET  /git/repositories/{id}/commits       — List commits
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryRead,
    RepositorySyncRequest,
    RepositorySyncResponse,
    CommitMemoryRead,
)
from app.services.repository import (
    create_repository,
    get_repositories_by_org,
    get_repository_by_id,
    sync_repository,
    get_commits_by_repository,
)
from sqlalchemy.exc import IntegrityError

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
