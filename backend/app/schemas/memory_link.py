from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.memory_link import MemoryLinkType


class MemoryLinkCreate(BaseModel):
    organization_id: UUID
    source_memory_id: UUID
    target_memory_id: UUID
    link_type: MemoryLinkType
    score: float = Field(..., ge=0.0, le=1.0)

    @model_validator(mode="after")
    def source_and_target_must_differ(self) -> "MemoryLinkCreate":
        if self.source_memory_id == self.target_memory_id:
            raise ValueError("source_memory_id and target_memory_id must be different")
        return self


class MemoryLinkRead(BaseModel):
    id: UUID
    organization_id: UUID
    source_memory_id: UUID
    target_memory_id: UUID
    link_type: MemoryLinkType
    score: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GenerateLinksRequest(BaseModel):
    """Request body for auto-generating memory links for a given memory entry."""

    memory_id: UUID
    organization_id: UUID


class GenerateLinksResponse(BaseModel):
    """Summary returned after a generate-links run."""

    memory_id: UUID
    links_created: int
    links_skipped: int
    links: list[MemoryLinkRead]
