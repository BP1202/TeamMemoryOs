from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScenarioBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    is_active: bool = True


class ScenarioCreate(ScenarioBase):
    organization_id: UUID
    # Caller supplies their own user id; validated in the route via get_current_user.
    created_by_user_id: UUID | None = None


class ScenarioRead(ScenarioBase):
    id: UUID
    organization_id: UUID
    created_by_user_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
