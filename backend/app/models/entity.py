import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EntityType(str, enum.Enum):
    PERSON = "PERSON"
    REPOSITORY = "REPOSITORY"
    FILE = "FILE"
    SERVICE = "SERVICE"
    TECHNOLOGY = "TECHNOLOGY"
    INCIDENT = "INCIDENT"
    PULL_REQUEST = "PULL_REQUEST"
    BRANCH = "BRANCH"
    API_ENDPOINT = "API_ENDPOINT"


class Entity(Base):
    """A reusable engineering entity that acts as a knowledge graph node.

    Entities are scoped to an organisation.  The combination of
    (organization_id, entity_type, name) is unique to prevent duplicates.
    """

    __tablename__ = "entities"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "entity_type",
            "name",
            name="uq_entities_org_type_name",
        ),
        Index("ix_entities_organization_id", "organization_id"),
        Index("ix_entities_entity_type", "entity_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType, name="entitytype"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<Entity id={self.id} type={self.entity_type!r} "
            f"name={self.name!r} org={self.organization_id}>"
        )


class MemoryEntity(Base):
    """Association between a MemoryEntry and an Entity (many-to-many)."""

    __tablename__ = "memory_entities"

    __table_args__ = (
        UniqueConstraint(
            "memory_entry_id",
            "entity_id",
            name="uq_memory_entities_entry_entity",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    memory_entry_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("memory_entries.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    def __repr__(self) -> str:
        return (
            f"<MemoryEntity memory={self.memory_entry_id} "
            f"entity={self.entity_id}>"
        )
