import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MemoryLinkType(str, enum.Enum):
    SHARED_ENTITY = "SHARED_ENTITY"
    SAME_SCENARIO = "SAME_SCENARIO"
    SEMANTIC_SIMILARITY = "SEMANTIC_SIMILARITY"
    RELATED_INCIDENT = "RELATED_INCIDENT"


class MemoryLink(Base):
    """A scored typed relationship between two MemoryEntry records.

    Links are automatically inferred by the memory linking engine based
    on shared entities, shared scenarios, and semantic similarity.

    The unique constraint on (organization_id, source_memory_id,
    target_memory_id, link_type) prevents duplicate inference results.
    Links are directional: source → target.
    """

    __tablename__ = "memory_links"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "source_memory_id",
            "target_memory_id",
            "link_type",
            name="uq_memory_links_org_src_tgt_type",
        ),
        Index("ix_memory_links_organization_id", "organization_id"),
        Index("ix_memory_links_source_memory_id", "source_memory_id"),
        Index("ix_memory_links_target_memory_id", "target_memory_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_memory_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("memory_entries.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_memory_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("memory_entries.id", ondelete="CASCADE"),
        nullable=False,
    )
    link_type: Mapped[MemoryLinkType] = mapped_column(
        Enum(MemoryLinkType, name="memorylinktype"),
        nullable=False,
    )
    # Relevance score in [0.0, 1.0] — higher means more strongly linked.
    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    def __repr__(self) -> str:
        return (
            f"<MemoryLink id={self.id} type={self.link_type!r} "
            f"score={self.score:.3f} "
            f"{self.source_memory_id} → {self.target_memory_id}>"
        )
