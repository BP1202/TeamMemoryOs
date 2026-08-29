import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# Embedding dimensionality — matches IBM Granite and OpenAI small models.
# Changing this requires a new migration.
EMBEDDING_DIM = 1536


class MemoryType(str, enum.Enum):
    decision = "decision"
    context = "context"
    artifact = "artifact"
    insight = "insight"
    discussion = "discussion"


class MemoryEntry(Base):
    """A single unit of organizational memory.

    Stores captured knowledge such as decisions, context snippets,
    artifacts, and insights.  The `embedding` column is a nullable
    ARRAY(Float) placeholder that will be replaced with a proper
    pgvector column once the embedding pipeline is built.
    """

    __tablename__ = "memory_entries"

    __table_args__ = (
        Index("ix_memory_entries_organization_id", "organization_id"),
        Index("ix_memory_entries_scenario_id", "scenario_id"),
        Index("ix_memory_entries_memory_type", "memory_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    scenario_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("scenarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    memory_type: Mapped[MemoryType] = mapped_column(
        Enum(MemoryType, name="memorytype"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(
        # Optional short label so entries can be browsed without reading content.
        nullable=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    # Flexible structured metadata — tags, source, confidence scores, etc.
    meta: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    # pgvector column — nullable until an embedding pipeline populates it.
    embedding: Mapped[Optional[list]] = mapped_column(
        Vector(EMBEDDING_DIM),
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
            f"<MemoryEntry id={self.id} type={self.memory_type!r} "
            f"org={self.organization_id}>"
        )
