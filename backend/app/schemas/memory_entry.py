from uuid import UUID
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.memory_entry import MemoryType


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
