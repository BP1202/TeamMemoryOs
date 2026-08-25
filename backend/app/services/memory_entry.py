from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory_entry import EMBEDDING_DIM, MemoryEntry
from app.schemas.memory_entry import MemoryEntryCreate


def create_memory_entry(db: Session, entry_in: MemoryEntryCreate) -> MemoryEntry:
    entry = MemoryEntry(
        organization_id=entry_in.organization_id,
        scenario_id=entry_in.scenario_id,
        created_by_user_id=entry_in.created_by_user_id,
        memory_type=entry_in.memory_type,
        title=entry_in.title,
        content=entry_in.content,
        meta=entry_in.meta,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_memory_entry_by_id(db: Session, entry_id: UUID) -> MemoryEntry | None:
    return db.scalar(select(MemoryEntry).where(MemoryEntry.id == entry_id))


def get_memory_entries_by_org(
    db: Session, organization_id: UUID, skip: int = 0, limit: int = 100
) -> Sequence[MemoryEntry]:
    stmt = (
        select(MemoryEntry)
        .where(MemoryEntry.organization_id == organization_id)
        .order_by(MemoryEntry.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return db.scalars(stmt).all()


def get_memory_entries_by_scenario(
    db: Session, scenario_id: UUID, skip: int = 0, limit: int = 100
) -> Sequence[MemoryEntry]:
    stmt = (
        select(MemoryEntry)
        .where(MemoryEntry.scenario_id == scenario_id)
        .order_by(MemoryEntry.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return db.scalars(stmt).all()


def store_embedding(
    db: Session,
    entry_id: UUID,
    embedding: list[float],
) -> MemoryEntry | None:
    """Write a pre-computed embedding vector to a memory entry.

    The caller is responsible for ensuring the vector has ``EMBEDDING_DIM``
    components and is already normalised if cosine similarity is desired.

    Returns the updated entry, or ``None`` if the entry was not found.
    """
    entry = get_memory_entry_by_id(db, entry_id)
    if entry is None:
        return None
    if len(embedding) != EMBEDDING_DIM:
        raise ValueError(
            f"Embedding has {len(embedding)} dimensions; expected {EMBEDDING_DIM}"
        )
    entry.embedding = embedding
    db.commit()
    db.refresh(entry)
    return entry


def semantic_search(
    db: Session,
    query_embedding: list[float],
    organization_id: UUID,
    top_k: int = 5,
    scenario_id: UUID | None = None,
) -> list[MemoryEntry]:
    """Return the top-k memory entries most similar to ``query_embedding``.

    Uses pgvector cosine distance (``<=>``).  Only entries that have a
    non-null embedding are considered.  Results are ordered by ascending
    cosine distance (most similar first).

    Args:
        db:               Active SQLAlchemy session.
        query_embedding:  Pre-computed query vector (EMBEDDING_DIM floats).
        organization_id:  Restrict search to this organisation's memories.
        top_k:            Maximum number of results to return.
        scenario_id:      Optional — further restrict to a single scenario.
    """
    if len(query_embedding) != EMBEDDING_DIM:
        raise ValueError(
            f"Query embedding has {len(query_embedding)} dimensions; "
            f"expected {EMBEDDING_DIM}"
        )

    # pgvector registers psycopg adapters that convert a Python list to the
    # ``vector`` wire type; the ``<=>`` operator computes cosine distance.
    stmt = (
        select(MemoryEntry)
        .where(
            MemoryEntry.organization_id == organization_id,
            MemoryEntry.embedding.isnot(None),
        )
        .order_by(
            # <=> is pgvector cosine distance; ascending = most similar first
            MemoryEntry.embedding.op("<=>")(query_embedding)
        )
        .limit(top_k)
    )
    if scenario_id is not None:
        stmt = stmt.where(MemoryEntry.scenario_id == scenario_id)

    return list(db.scalars(stmt).all())
