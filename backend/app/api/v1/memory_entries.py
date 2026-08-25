from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.memory_entry import MemoryEntryCreate, MemoryEntryRead
from app.services.memory_entry import (
    create_memory_entry,
    get_memory_entries_by_org,
    get_memory_entries_by_scenario,
    get_memory_entry_by_id,
)

router = APIRouter()


@router.post("/", response_model=MemoryEntryRead, status_code=status.HTTP_201_CREATED)
def create_new_memory_entry(
    entry_in: MemoryEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ingest a new memory entry.

    The authenticated user is recorded as the creator when
    ``created_by_user_id`` is not explicitly provided.
    """
    if entry_in.created_by_user_id is None:
        entry_in = entry_in.model_copy(
            update={"created_by_user_id": current_user.id}
        )
    try:
        return create_memory_entry(db, entry_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Referenced organization, scenario, or user not found",
        )


@router.get("/organization/{organization_id}", response_model=List[MemoryEntryRead])
def list_memory_entries_by_org(
    organization_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List memory entries for an organization, newest first."""
    return get_memory_entries_by_org(db, organization_id, skip=skip, limit=limit)


@router.get("/scenario/{scenario_id}", response_model=List[MemoryEntryRead])
def list_memory_entries_by_scenario(
    scenario_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List memory entries for a specific scenario, newest first."""
    return get_memory_entries_by_scenario(db, scenario_id, skip=skip, limit=limit)


@router.get("/{entry_id}", response_model=MemoryEntryRead)
def get_memory_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Retrieve a single memory entry by ID."""
    entry = get_memory_entry_by_id(db, entry_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory entry not found",
        )
    return entry
