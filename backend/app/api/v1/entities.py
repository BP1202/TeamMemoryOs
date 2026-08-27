from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.models.entity import EntityType
from app.models.user import User
from app.schemas.entity import (
    EntityCreate,
    EntityExtractRequest,
    EntityRead,
    ExtractedEntity,
    MemoryEntityCreate,
    MemoryEntityRead,
)
from app.services.entity import (
    attach_entity_to_memory,
    create_entity,
    get_entities_by_org,
    get_entities_for_memory,
    get_entity_by_id,
    get_or_create_entity,
)
from app.services.entity_extraction import extract_entities

router = APIRouter()


@router.post("/", response_model=EntityRead, status_code=status.HTTP_201_CREATED)
def create_new_entity(
    entity_in: EntityCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Create a new entity within an organisation.

    Returns 409 if an entity with the same type and name already exists
    in the organisation.
    """
    try:
        return create_entity(db, entity_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Entity with this type and name already exists in the organisation",
        )


@router.get("/organization/{organization_id}", response_model=List[EntityRead])
def list_entities_by_org(
    organization_id: UUID,
    entity_type: Optional[EntityType] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List entities belonging to an organisation, optionally filtered by type."""
    return get_entities_by_org(db, organization_id, entity_type=entity_type, skip=skip, limit=limit)


@router.get("/{entity_id}", response_model=EntityRead)
def get_entity(
    entity_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retrieve a single entity by ID."""
    entity = get_entity_by_id(db, entity_id)
    if entity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entity not found",
        )
    return entity


@router.post(
    "/memory/{memory_entry_id}/attach",
    response_model=MemoryEntityRead,
    status_code=status.HTTP_201_CREATED,
)
def attach_entity(
    memory_entry_id: UUID,
    body: MemoryEntityCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Attach an existing entity to a memory entry.

    Returns 409 if the entity is already attached to the memory entry.
    """
    if body.memory_entry_id != memory_entry_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="memory_entry_id in body must match the URL parameter",
        )
    try:
        return attach_entity_to_memory(db, body)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Entity is already attached to this memory entry, or referenced ID not found",
        )


@router.get("/memory/{memory_entry_id}", response_model=List[EntityRead])
def list_entities_for_memory(
    memory_entry_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all entities attached to a memory entry."""
    return get_entities_for_memory(db, memory_entry_id)


@router.post("/extract", response_model=List[ExtractedEntity])
def extract_entities_from_text(
    body: EntityExtractRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Deterministically extract entities from free-form text.

    Returns a list of extracted entities (not persisted).
    Use POST /entities/ to persist individual entities if needed.
    """
    raw = extract_entities(body.text)
    return [ExtractedEntity(entity_type=r.entity_type, name=r.name) for r in raw]
