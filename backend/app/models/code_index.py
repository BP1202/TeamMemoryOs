"""CodeFile and CodeChunk models for AI Codebase Search (Milestone 6.4)."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.memory_entry import EMBEDDING_DIM


class CodeFile(Base):
    """A source file indexed from a repository."""

    __tablename__ = "code_files"

    __table_args__ = (
        UniqueConstraint(
            "repository_id",
            "file_path",
            name="uq_code_files_repo_path",
        ),
        Index("ix_code_files_organization_id", "organization_id"),
        Index("ix_code_files_repository_id", "repository_id"),
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
    file_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )
    language: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    size_bytes: Mapped[int] = mapped_column(
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
            f"<CodeFile id={self.id} path={self.file_path!r} "
            f"repo={self.repository_id}>"
        )


class CodeChunk(Base):
    """A semantically meaningful chunk of source code with an embedding.

    Chunks are produced by splitting CodeFile content into logical units
    (function, class, or fixed-size windows when AST is unavailable).
    """

    __tablename__ = "code_chunks"

    __table_args__ = (
        Index("ix_code_chunks_organization_id", "organization_id"),
        Index("ix_code_chunks_code_file_id", "code_file_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    code_file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("code_files.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Optional link to a MemoryEntry so code chunks integrate with RAG
    memory_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("memory_entries.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Chunk type: "function", "class", "block", "import", "other"
    chunk_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="block",
    )
    # Symbol name when chunk_type is "function" or "class"
    symbol_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    start_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    end_line: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    embedding: Mapped[Optional[list]] = mapped_column(
        Vector(EMBEDDING_DIM),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    def __repr__(self) -> str:
        return (
            f"<CodeChunk id={self.id} type={self.chunk_type!r} "
            f"file={self.code_file_id}>"
        )
