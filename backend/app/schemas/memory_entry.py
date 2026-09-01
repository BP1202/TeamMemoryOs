from uuid import UUID
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.memory_entry import EMBEDDING_DIM, MemoryType


class MemoryEntryBase(BaseModel):
    memory_type: MemoryType
    title: str | None = Field(None, max_length=255)
    content: str = Field(..., min_length=1)
    meta: dict[str, Any] | None = None


class MemoryEntryCreate(MemoryEntryBase):
    organization_id: UUID
    scenario_id: UUID | None = None
    created_by_user_id: UUID | None = None


class MemoryEntryRead(MemoryEntryBase):
    id: UUID
    organization_id: UUID
    scenario_id: UUID | None
    created_by_user_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmbeddingStore(BaseModel):
    """Request body for storing a pre-computed embedding on a memory entry."""

    embedding: list[float] = Field(
        ...,
        min_length=EMBEDDING_DIM,
        max_length=EMBEDDING_DIM,
        description=f"Normalised float vector of exactly {EMBEDDING_DIM} dimensions.",
    )


class SemanticSearchRequest(BaseModel):
    """Request body for semantic similarity search."""

    query_embedding: list[float] = Field(
        ...,
        min_length=EMBEDDING_DIM,
        max_length=EMBEDDING_DIM,
        description=f"Pre-computed query vector of exactly {EMBEDDING_DIM} dimensions.",
    )
    organization_id: UUID
    scenario_id: UUID | None = None
    top_k: int = Field(default=5, ge=1, le=50)


class SemanticSearchResult(BaseModel):
    """A single hit returned by semantic search."""

    entry: MemoryEntryRead
    # Cosine distance is not returned here to keep the interface clean;
    # ordering by the DB already encodes relevance rank.
    rank: int
