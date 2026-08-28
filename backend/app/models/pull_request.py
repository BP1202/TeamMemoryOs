"""PullRequest and PullRequestReview models for PR Guardian (Milestone 6.2)."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PRStatus(str, enum.Enum):
    open = "open"
    closed = "closed"
    merged = "merged"


class PullRequest(Base):
    """A pull request ingested into organizational memory."""

    __tablename__ = "pull_requests"

    __table_args__ = (
        UniqueConstraint(
            "repository_id",
            "pr_number",
            name="uq_pull_requests_repo_number",
        ),
        Index("ix_pull_requests_organization_id", "organization_id"),
        Index("ix_pull_requests_repository_id", "repository_id"),
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
    pr_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    author: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    source_branch: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    target_branch: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    status: Mapped[PRStatus] = mapped_column(
        Enum(PRStatus, name="prstatus"),
        nullable=False,
        default=PRStatus.open,
    )
    # Raw diff text (may be large — stored for analysis)
    diff_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    # JSON list of changed file paths
    changed_files: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    files_changed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
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
            f"<PullRequest id={self.id} pr=#{self.pr_number} "
            f"repo={self.repository_id}>"
        )


class PullRequestReview(Base):
    """AI-generated review for a PullRequest."""

    __tablename__ = "pull_request_reviews"

    __table_args__ = (
        Index("ix_pr_reviews_pull_request_id", "pull_request_id"),
        Index("ix_pr_reviews_organization_id", "organization_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    pull_request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pull_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    risk_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )
    # JSON list of risk factors
    risk_factors: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    # JSON list of review suggestions
    suggestions: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    # JSON list of retrieved context citations
    citations: Mapped[list | None] = mapped_column(
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
            f"<PullRequestReview id={self.id} "
            f"pr={self.pull_request_id} risk={self.risk_score:.2f}>"
        )
