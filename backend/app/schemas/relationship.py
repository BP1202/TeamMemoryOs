from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.entity import RelationshipType
from app.schemas.entity import EntityRead


class RelationshipCreate(BaseModel):
    organization_id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    relationship_type: RelationshipType

    @model_validator(mode="after")
    def source_and_target_must_differ(self) -> "RelationshipCreate":
        if self.source_entity_id == self.target_entity_id:
            raise ValueError("source_entity_id and target_entity_id must be different")
        return self


class RelationshipRead(BaseModel):
    id: UUID
    organization_id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    relationship_type: RelationshipType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NeighborRead(BaseModel):
    """An entity that is directly connected to the queried entity, with
    the relationship metadata that links them."""

    entity: EntityRead
    relationship_type: RelationshipType
    relationship_id: UUID
    direction: str = Field(
        ...,
        description="'outgoing' when this entity is the target; 'incoming' when it is the source",
    )
