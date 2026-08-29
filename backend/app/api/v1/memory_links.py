from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.models.memory_link import MemoryLinkType
from app.models.user import User
from app.schemas.memory_link import (
    GenerateLinksRequest,
    GenerateLinksResponse,
    MemoryLinkCreate,
    MemoryLinkRead,
)
from app.services.memory_link import (
    create_memory_link,
    generate_memory_links,
    get_memory_links,
)

router = APIRouter()


@router.post(
    "/generate",
    response_model=GenerateLinksResponse,
    status_code=status.HTTP_200_OK,
)
def generate_links_for_memory(
    body: GenerateLinksRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Automatically infer and persist memory links for a given memory entry.

    Evaluates three deterministic signals (shared entities, same scenario,
    semantic similarity) against every other memory in the organisation and
    writes links with score > 0.  Duplicate links are silently skipped.

    Returns a summary of what was created.
    """
    return generate_memory_links(db, body.memory_id, body.organization_id)


@router.get(
    "/memory/{memory_id}",
    response_model=List[MemoryLinkRead],
)
def list_links_for_memory(
    memory_id: UUID,
    organization_id: UUID = Query(...),
    link_type: Optional[MemoryLinkType] = Query(default=None),
    min_score: float = Query(default=0.0, ge=0.0, le=1.0),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List outgoing memory links for a memory entry.

    Requires ``organization_id`` for tenant isolation.
    Optionally filter by ``link_type`` and ``min_score``.
    Results are ordered by descending score.
    """
    return get_memory_links(
        db,
        memory_id=memory_id,
        organization_id=organization_id,
        link_type=link_type,
        min_score=min_score,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/",
    response_model=MemoryLinkRead,
    status_code=status.HTTP_201_CREATED,
)
def create_link_manually(
    link_in: MemoryLinkCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Manually create a memory link between two entries.

    Returns 400 for self-links, 409 for duplicates or bad foreign keys.
    """
    try:
        return create_memory_link(db, link_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Memory link already exists, or a referenced memory entry / "
                "organisation ID was not found"
            ),
        )
