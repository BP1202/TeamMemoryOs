from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.memory_entry import (
    EmbeddingStore,
    MemoryEntryCreate,
    MemoryEntryRead,
    SemanticSearchRequest,
    SemanticSearchResult,
)
from app.services.memory_entry import (
    create_memory_entry,
    get_memory_entries_by_org,
    get_memory_entries_by_scenario,
    get_memory_entry_by_id,
    semantic_search,
    store_embedding,
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


@router.put("/{entry_id}/embedding", response_model=MemoryEntryRead)
def store_memory_embedding(
    entry_id: UUID,
    body: EmbeddingStore,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Store a pre-computed embedding vector on a memory entry.

    The caller supplies a normalised float vector of exactly
    ``EMBEDDING_DIM`` dimensions.  Dimension validation is enforced by
    the Pydantic schema and by the service layer.
    """
    try:
        entry = store_embedding(db, entry_id, body.embedding)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory entry not found",
        )
    return entry


@router.post("/search", response_model=List[SemanticSearchResult])
def search_memory(
    body: SemanticSearchRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Perform semantic similarity search over an organisation's memory.

    Accepts a pre-computed query vector and returns the top-k most similar
    entries ordered by cosine similarity (most relevant first).
    """
    try:
        entries = semantic_search(
            db=db,
            query_embedding=body.query_embedding,
            organization_id=body.organization_id,
            top_k=body.top_k,
            scenario_id=body.scenario_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return [
        SemanticSearchResult(entry=MemoryEntryRead.model_validate(e), rank=i + 1)
        for i, e in enumerate(entries)
    ]


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
