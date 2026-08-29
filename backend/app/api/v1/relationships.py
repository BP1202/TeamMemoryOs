from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.models.entity import RelationshipType
from app.models.user import User
from app.schemas.relationship import NeighborRead, RelationshipCreate, RelationshipRead
from app.services.relationship import (
    create_relationship,
    get_relationship_by_id,
    list_neighbors,
    list_relationships_for_entity,
)

router = APIRouter()


@router.post(
    "/",
    response_model=RelationshipRead,
    status_code=status.HTTP_201_CREATED,
)
def create_new_relationship(
    rel_in: RelationshipCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Create a directed typed relationship between two entities.

    Returns 400 if source and target are the same entity.
    Returns 409 if an identical relationship already exists or a referenced
    entity ID is not found.
    """
    try:
        return create_relationship(db, rel_in)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Relationship already exists, or a referenced entity / "
                "organisation ID was not found"
            ),
        )


@router.get("/{relationship_id}", response_model=RelationshipRead)
def get_relationship(
    relationship_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retrieve a single relationship by ID."""
    rel = get_relationship_by_id(db, relationship_id)
    if rel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relationship not found",
        )
    return rel


@router.get(
    "/entity/{entity_id}/outgoing",
    response_model=List[RelationshipRead],
)
def list_outgoing_relationships(
    entity_id: UUID,
    relationship_type: Optional[RelationshipType] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all outgoing relationships for an entity, newest first.

    Optionally filter by ``relationship_type``.
    """
    return list_relationships_for_entity(
        db,
        entity_id,
        relationship_type=relationship_type,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/entity/{entity_id}/neighbors",
    response_model=List[NeighborRead],
)
def list_entity_neighbors(
    entity_id: UUID,
    organization_id: UUID = Query(...),
    relationship_type: Optional[RelationshipType] = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all directly connected entities (both directions).

    Returns each neighbor with the relationship type, direction
    ('incoming' or 'outgoing'), and the relationship ID for traceability.
    Results are scoped to ``organization_id`` for tenant isolation.
    """
    return list_neighbors(
        db,
        entity_id=entity_id,
        organization_id=organization_id,
        relationship_type=relationship_type,
    )
