"""Memory linking engine — automatic inference of relationships between
MemoryEntry records.

Three deterministic signals are used to score links:

1. Shared entities   — Jaccard overlap of the two entries' entity sets.
                       Weight: 0.5
2. Same scenario     — Binary flag (both entries share the same scenario_id).
                       Weight: 0.3
3. Semantic sim.     — Dot-product (cosine) similarity of pgvector embeddings.
                       Only applied when both entries have non-null embeddings.
                       Weight: 0.2

Final score = sum(signal * weight), normalised to [0.0, 1.0].
Links are only written when the computed score > 0.0.
Duplicate (org, src, tgt, type) combinations are silently skipped.
"""

from __future__ import annotations

import math
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.entity import Entity, MemoryEntity
from app.models.memory_entry import MemoryEntry
from app.models.memory_link import MemoryLink, MemoryLinkType
from app.schemas.memory_link import (
    GenerateLinksResponse,
    MemoryLinkCreate,
    MemoryLinkRead,
)


# ---------------------------------------------------------------------------
# Scoring weights — must sum to 1.0
# ---------------------------------------------------------------------------
_W_SHARED_ENTITY = 0.5
_W_SAME_SCENARIO = 0.3
_W_SEMANTIC_SIM = 0.2


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def create_memory_link(db: Session, link_in: MemoryLinkCreate) -> MemoryLink:
    """Persist a single MemoryLink.

    Raises ``ValueError`` for self-links.
    Raises ``IntegrityError`` for duplicate (org, src, tgt, type) or bad FK.
    """
    if link_in.source_memory_id == link_in.target_memory_id:
        raise ValueError("source_memory_id and target_memory_id must be different")

    link = MemoryLink(
        organization_id=link_in.organization_id,
        source_memory_id=link_in.source_memory_id,
        target_memory_id=link_in.target_memory_id,
        link_type=link_in.link_type,
        score=max(0.0, min(1.0, link_in.score)),  # clamp to [0, 1]
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def get_memory_links(
    db: Session,
    memory_id: UUID,
    organization_id: UUID,
    link_type: MemoryLinkType | None = None,
    min_score: float = 0.0,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[MemoryLink]:
    """Return all outgoing links for *memory_id*, scoped to *organization_id*.

    Results are ordered by descending score (most relevant first).
    """
    stmt = (
        select(MemoryLink)
        .where(
            MemoryLink.source_memory_id == memory_id,
            MemoryLink.organization_id == organization_id,
            MemoryLink.score >= min_score,
        )
        .order_by(MemoryLink.score.desc())
        .offset(skip)
        .limit(limit)
    )
    if link_type is not None:
        stmt = stmt.where(MemoryLink.link_type == link_type)
    return db.scalars(stmt).all()


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _get_entity_ids(db: Session, memory_id: UUID) -> frozenset[UUID]:
    """Return the set of entity UUIDs attached to *memory_id*."""
    rows = db.scalars(
        select(MemoryEntity.entity_id).where(
            MemoryEntity.memory_entry_id == memory_id
        )
    ).all()
    return frozenset(rows)


def calculate_link_score(
    *,
    shared_entity_count: int,
    total_entity_count: int,
    same_scenario: bool,
    cosine_similarity: float | None,
) -> float:
    """Compute a normalised score in [0.0, 1.0] from the three signals.

    Args:
        shared_entity_count:  Number of entities common to both entries.
        total_entity_count:   Union size of both entity sets (for Jaccard).
        same_scenario:        True if both entries share the same scenario_id.
        cosine_similarity:    Pre-computed cosine similarity in [0, 1], or
                              None when either entry lacks an embedding.

    Returns:
        Final weighted score clamped to [0.0, 1.0].
    """
    # --- Signal 1: shared entities (Jaccard similarity) ---
    if total_entity_count > 0:
        entity_signal = shared_entity_count / total_entity_count
    else:
        entity_signal = 0.0

    # --- Signal 2: same scenario ---
    scenario_signal = 1.0 if same_scenario else 0.0

    # --- Signal 3: semantic similarity ---
    if cosine_similarity is not None:
        # cosine_similarity is already in [0, 1] (distance = 1 - similarity)
        semantic_signal = max(0.0, min(1.0, cosine_similarity))
        effective_semantic_weight = _W_SEMANTIC_SIM
    else:
        # No embeddings — redistribute weight equally to the other two signals
        semantic_signal = 0.0
        effective_semantic_weight = 0.0

    # Rebalance weights when semantic signal is unavailable
    if effective_semantic_weight == 0.0:
        total_available = _W_SHARED_ENTITY + _W_SAME_SCENARIO
        w_entity = _W_SHARED_ENTITY / total_available
        w_scenario = _W_SAME_SCENARIO / total_available
    else:
        w_entity = _W_SHARED_ENTITY
        w_scenario = _W_SAME_SCENARIO

    score = (
        entity_signal * w_entity
        + scenario_signal * w_scenario
        + semantic_signal * effective_semantic_weight
    )
    return max(0.0, min(1.0, score))


def _cosine_similarity(a: list[float], b: list[float]) -> float | None:
    """Return cosine similarity in [0.0, 1.0] between two equal-length vectors.

    Returns None if either vector is all-zeros.
    """
    if len(a) != len(b):
        return None
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return None
    # Clamp to [0, 1] — cosine ranges [-1, 1] but embeddings are non-negative
    raw = dot / (mag_a * mag_b)
    return max(0.0, min(1.0, (raw + 1.0) / 2.0))


# ---------------------------------------------------------------------------
# Auto-generation
# ---------------------------------------------------------------------------

def generate_memory_links(
    db: Session,
    memory_id: UUID,
    organization_id: UUID,
) -> GenerateLinksResponse:
    """Infer and persist all link types for *memory_id* against every other
    memory in the same organisation.

    For each candidate memory the engine evaluates three signals:
    - Shared entities (SHARED_ENTITY link)
    - Same scenario  (SAME_SCENARIO link)
    - Semantic similarity (SEMANTIC_SIMILARITY link, requires embeddings)

    Duplicate links are skipped (not raised as errors).

    Returns a :class:`GenerateLinksResponse` summarising what was created.
    """
    source = db.scalar(
        select(MemoryEntry).where(
            MemoryEntry.id == memory_id,
            MemoryEntry.organization_id == organization_id,
        )
    )
    if source is None:
        return GenerateLinksResponse(
            memory_id=memory_id,
            links_created=0,
            links_skipped=0,
            links=[],
        )

    # Load all other memories in the org
    candidates = db.scalars(
        select(MemoryEntry).where(
            MemoryEntry.organization_id == organization_id,
            MemoryEntry.id != memory_id,
        )
    ).all()

    source_entities = _get_entity_ids(db, memory_id)

    created: list[MemoryLinkRead] = []
    skipped = 0

    for candidate in candidates:
        cand_entities = _get_entity_ids(db, candidate.id)

        # ---- SHARED_ENTITY ----
        intersection = source_entities & cand_entities
        union = source_entities | cand_entities
        if intersection:
            score = calculate_link_score(
                shared_entity_count=len(intersection),
                total_entity_count=len(union),
                same_scenario=False,
                cosine_similarity=None,
            )
            link = _upsert_link(
                db,
                organization_id=organization_id,
                source_memory_id=memory_id,
                target_memory_id=candidate.id,
                link_type=MemoryLinkType.SHARED_ENTITY,
                score=score,
            )
            if link is not None:
                created.append(MemoryLinkRead.model_validate(link))
            else:
                skipped += 1

        # ---- SAME_SCENARIO ----
        if (
            source.scenario_id is not None
            and candidate.scenario_id is not None
            and source.scenario_id == candidate.scenario_id
        ):
            score = calculate_link_score(
                shared_entity_count=0,
                total_entity_count=0,
                same_scenario=True,
                cosine_similarity=None,
            )
            link = _upsert_link(
                db,
                organization_id=organization_id,
                source_memory_id=memory_id,
                target_memory_id=candidate.id,
                link_type=MemoryLinkType.SAME_SCENARIO,
                score=score,
            )
            if link is not None:
                created.append(MemoryLinkRead.model_validate(link))
            else:
                skipped += 1

        # ---- SEMANTIC_SIMILARITY ----
        if source.embedding is not None and candidate.embedding is not None:
            sim = _cosine_similarity(
                list(source.embedding), list(candidate.embedding)
            )
            if sim is not None and sim > 0.0:
                score = calculate_link_score(
                    shared_entity_count=0,
                    total_entity_count=0,
                    same_scenario=False,
                    cosine_similarity=sim,
                )
                link = _upsert_link(
                    db,
                    organization_id=organization_id,
                    source_memory_id=memory_id,
                    target_memory_id=candidate.id,
                    link_type=MemoryLinkType.SEMANTIC_SIMILARITY,
                    score=score,
                )
                if link is not None:
                    created.append(MemoryLinkRead.model_validate(link))
                else:
                    skipped += 1

    return GenerateLinksResponse(
        memory_id=memory_id,
        links_created=len(created),
        links_skipped=skipped,
        links=sorted(created, key=lambda l: l.score, reverse=True),
    )


def _upsert_link(
    db: Session,
    *,
    organization_id: UUID,
    source_memory_id: UUID,
    target_memory_id: UUID,
    link_type: MemoryLinkType,
    score: float,
) -> MemoryLink | None:
    """Create a MemoryLink, returning None (not raising) on duplicate."""
    link = MemoryLink(
        organization_id=organization_id,
        source_memory_id=source_memory_id,
        target_memory_id=target_memory_id,
        link_type=link_type,
        score=max(0.0, min(1.0, score)),
    )
    db.add(link)
    try:
        db.commit()
        db.refresh(link)
        return link
    except IntegrityError:
        db.rollback()
        return None
