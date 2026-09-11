from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cache.embedding_cache import EmbeddingCache
from app.chunking import chunk_text, chunk_to_memory_meta
from app.chunking.chunk_models import ChunkingConfig, ChunkingStrategy
from app.models.memory_entry import EMBEDDING_DIM, MemoryEntry
from app.providers.embedding_provider import get_embedding_provider
from app.schemas.memory_entry import MemoryEntryCreate


def create_memory_entry(
    db: Session,
    entry_in: MemoryEntryCreate,
    auto_embed: bool = True,
) -> MemoryEntry:
    """Create a new memory entry with automatic chunk hash and vector embedding."""
    meta = dict(entry_in.meta) if entry_in.meta else {}
    chunk_hash = EmbeddingCache.compute_hash(entry_in.content)
    meta["chunk_hash"] = chunk_hash

    embedding: list[float] | None = None
    if auto_embed:
        emb_provider = get_embedding_provider()
        try:
            embedding = emb_provider.embed(entry_in.content)
        except Exception:
            embedding = None

    entry = MemoryEntry(
        organization_id=entry_in.organization_id,
        scenario_id=entry_in.scenario_id,
        created_by_user_id=entry_in.created_by_user_id,
        memory_type=entry_in.memory_type,
        title=entry_in.title,
        content=entry_in.content,
        meta=meta,
        embedding=embedding,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def create_memory_entries_chunked(
    db: Session,
    entry_in: MemoryEntryCreate,
    chunking_config: ChunkingConfig | None = None,
    auto_embed: bool = True,
    skip_duplicates: bool = True,
) -> list[MemoryEntry]:
    """Split large memory entry content into semantic chunks and store them.
    
    Generates SHA-256 hashes for each chunk, skips duplicate chunks when configured,
    attaches parent-child and header metadata, and computes vector embeddings.
    """
    config = chunking_config or ChunkingConfig(strategy=ChunkingStrategy.AUTO)
    chunk_result = chunk_text(
        text=entry_in.content,
        strategy=config.strategy,
        metadata=entry_in.meta,
        config=config,
    )

    if not chunk_result.chunks:
        return [create_memory_entry(db, entry_in, auto_embed=auto_embed)]

    emb_provider = get_embedding_provider() if auto_embed else None
    created_entries: list[MemoryEntry] = []
    seen_hashes: set[str] = set()

    for ch in chunk_result.chunks:
        if skip_duplicates:
            if ch.chunk_hash in seen_hashes:
                continue
            seen_hashes.add(ch.chunk_hash)

        chunk_meta = chunk_to_memory_meta(
            ch,
            extra_fields={"parent_title": entry_in.title} if entry_in.title else None,
        )
        if entry_in.meta:
            # Preserve non-conflicting original user meta
            for k, v in entry_in.meta.items():
                if k not in chunk_meta:
                    chunk_meta[k] = v

        # Determine chunk title
        if ch.metadata.section_header:
            chunk_title = f"{entry_in.title} — {ch.metadata.section_header}" if entry_in.title else ch.metadata.section_header
        elif ch.metadata.symbol_name:
            chunk_title = f"{entry_in.title} — {ch.metadata.symbol_name}" if entry_in.title else ch.metadata.symbol_name
        elif len(chunk_result.chunks) > 1:
            chunk_title = f"{entry_in.title} [Part {ch.chunk_index + 1}/{chunk_result.total_chunks}]" if entry_in.title else f"Part {ch.chunk_index + 1}"
        else:
            chunk_title = entry_in.title

        embedding: list[float] | None = None
        if auto_embed and emb_provider:
            try:
                embedding = emb_provider.embed(ch.content)
            except Exception:
                embedding = None

        entry = MemoryEntry(
            organization_id=entry_in.organization_id,
            scenario_id=entry_in.scenario_id,
            created_by_user_id=entry_in.created_by_user_id,
            memory_type=entry_in.memory_type,
            title=chunk_title,
            content=ch.content,
            meta=chunk_meta,
            embedding=embedding,
        )
        db.add(entry)
        created_entries.append(entry)

    db.commit()
    for e in created_entries:
        db.refresh(e)

    return created_entries


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
    chunk_hash: str | None = None,
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
    
    meta = dict(entry.meta) if entry.meta else {}
    h = chunk_hash or EmbeddingCache.compute_hash(entry.content)
    meta["chunk_hash"] = h
    entry.meta = meta

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
