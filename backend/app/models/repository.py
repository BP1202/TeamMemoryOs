"""Repository and CommitMemory models for Git Repository Intelligence (Milestone 6.1)."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Repository(Base):
    """A Git repository registered for memory ingestion.

    Scoped to an organisation.  The combination of
    (organization_id, remote_url) is unique to prevent duplicate registrations.
    """

    __tablename__ = "repositories"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "remote_url",
            name="uq_repositories_org_url",
        ),
        Index("ix_repositories_organization_id", "organization_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    remote_url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )
    default_branch: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="main",
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # Latest commit SHA synced (for incremental sync)
    last_synced_sha: Mapped[str | None] = mapped_column(
        String(40),
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
            f"<Repository id={self.id} name={self.name!r} "
            f"org={self.organization_id}>"
        )


class CommitMemory(Base):
    """A single Git commit ingested as organizational memory.

    Each commit is linked to a Repository and produces a MemoryEntry.
    """

    __tablename__ = "commit_memories"

    __table_args__ = (
        UniqueConstraint(
            "repository_id",
            "commit_sha",
            name="uq_commit_memories_repo_sha",
        ),
        Index("ix_commit_memories_repository_id", "repository_id"),
        Index("ix_commit_memories_organization_id", "organization_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
    )
    memory_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("memory_entries.id", ondelete="SET NULL"),
        nullable=True,
    )
    commit_sha: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )
    author_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    author_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    commit_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    committed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    files_changed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    insertions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    deletions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    # JSON list of changed file paths (capped for performance)
    changed_files: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    def __repr__(self) -> str:
        return (
            f"<CommitMemory id={self.id} sha={self.commit_sha[:7]} "
            f"repo={self.repository_id}>"
        )
