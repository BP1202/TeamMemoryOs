"""TerminalSession and TerminalError models for Terminal Memory Copilot (Milestone 6.3)."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ErrorSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class TerminalSession(Base):
    """A terminal session submitted for learning and memory capture."""

    __tablename__ = "terminal_sessions"

    __table_args__ = (
        Index("ix_terminal_sessions_organization_id", "organization_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    submitted_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Raw terminal output text
    raw_output: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    # Parsed command that triggered the session (best effort)
    command: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )
    # Working directory when command was run
    working_directory: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    def __repr__(self) -> str:
        return (
            f"<TerminalSession id={self.id} "
            f"org={self.organization_id}>"
        )


class TerminalError(Base):
    """A classified terminal error extracted from a TerminalSession."""

    __tablename__ = "terminal_errors"

    __table_args__ = (
        Index("ix_terminal_errors_organization_id", "organization_id"),
        Index("ix_terminal_errors_session_id", "session_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("terminal_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    memory_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("memory_entries.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Classifier-assigned error type (e.g. "ImportError", "ConnectionRefused")
    error_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    # Extracted error message (one-liner)
    error_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    severity: Mapped[ErrorSeverity] = mapped_column(
        Enum(ErrorSeverity, name="errorseverity"),
        nullable=False,
        default=ErrorSeverity.medium,
    )
    # JSON list of suggested fixes retrieved from history
    suggested_fixes: Mapped[list | None] = mapped_column(
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
            f"<TerminalError id={self.id} type={self.error_type!r} "
            f"severity={self.severity}>"
        )
