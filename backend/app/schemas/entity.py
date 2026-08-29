from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.entity import EntityType


class EntityCreate(BaseModel):
    organization_id: UUID
    entity_type: EntityType
    name: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(None, max_length=1000)


class EntityRead(BaseModel):
    id: UUID
    organization_id: UUID
    entity_type: EntityType
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemoryEntityCreate(BaseModel):
    memory_entry_id: UUID
    entity_id: UUID


class MemoryEntityRead(BaseModel):
    id: UUID
    memory_entry_id: UUID
    entity_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EntityExtractRequest(BaseModel):
    """Request body for extracting entities from free-form text."""

    text: str = Field(..., min_length=1)
    organization_id: UUID


class ExtractedEntity(BaseModel):
    """A single entity extracted from text (not yet persisted)."""

    entity_type: EntityType
    name: str
