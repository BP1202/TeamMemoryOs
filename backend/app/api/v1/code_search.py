"""AI Codebase Search API — Milestone 6.4.

Routes:
* POST /code/repositories/{id}/index  — Index repository
* POST /code/search                   — Search code
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.code_index import (
    CodeIndexRequest,
    CodeIndexResponse,
    CodeSearchRequest,
    CodeSearchResponse,
)
from app.services.code_index import index_repository, search_code
from app.services.repository import get_repository_by_id

router = APIRouter()


@router.post("/repositories/{repository_id}/index", response_model=CodeIndexResponse)
def index_repo(
    repository_id: UUID,
    body: CodeIndexRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Index source files from a repository for code search."""
    repo = get_repository_by_id(db, repository_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return index_repository(
        db,
        repository_id=repository_id,
        organization_id=repo.organization_id,
        request=body,
    )


@router.post("/search", response_model=CodeSearchResponse)
def search_codebase(
    body: CodeSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search the indexed codebase for relevant code chunks."""
    return search_code(db, body)
