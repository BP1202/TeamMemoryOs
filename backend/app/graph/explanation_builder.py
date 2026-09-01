"""
Explainable Retrieval layer for TeamMemoryOS.

Transforms raw HybridRetriever results into structured, human-readable
explanations that surface:

* Per-memory citations with score breakdowns.
* The shortest entity path connecting retrieved memories through the graph.
* An aggregated confidence score for the overall retrieval pass.

No LLM is used — all explanations are derived deterministically from
retrieval metadata.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.graph.hybrid_retriever import HybridResult
from app.models.entity import Entity, EntityRelationship


# ---------------------------------------------------------------------------
# Data classes (internal — serialised to Pydantic schemas at API boundary)
# ---------------------------------------------------------------------------

@dataclass
class Citation:
    """Structured citation for a single retrieved memory."""

    memory_id: UUID
    memory_title: str | None
    memory_type: str
    retrieval_reason: str
    semantic_score: float
    graph_score: float
    link_score: float
    final_score: float
    graph_distance: int
    matched_entities: list[str]
    rank: int


@dataclass
class GraphPathStep:
    """One step in an entity path: entity → relationship → entity."""

    source_entity_id: UUID
    source_entity_name: str
    relationship_type: str
    target_entity_id: UUID
    target_entity_name: str


@dataclass
class RetrievalExplanation:
    """Complete explanation for one retrieval pass.

    Attributes:
        question:           The original query.
        retrieval_mode:     'semantic' or 'hybrid'.
        confidence:         Aggregated confidence in [0.0, 1.0].
        result_count:       Number of ranked results.
        citations:          Ordered list of per-result citations.
        graph_path:         Shortest entity path linking results (may be empty).
        summary:            One-line plain-English summary of the retrieval.
    """

    question: str
    retrieval_mode: str
    confidence: float
    result_count: int
    citations: list[Citation]
    graph_path: list[GraphPathStep]
    summary: str


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_retrieval_explanation(
    question: str,
    hybrid_results: list[HybridResult],
    db: Session,
    organization_id: UUID,
    retrieval_mode: str = "hybrid",
) -> RetrievalExplanation:
    """Build a full ``RetrievalExplanation`` from hybrid retrieval results.

    Args:
        question:         Original query string.
        hybrid_results:   Ordered list of ``HybridResult`` objects.
        db:               Active SQLAlchemy session (for graph path lookup).
        organization_id:  Used to scope entity path queries.
        retrieval_mode:   'semantic' or 'hybrid'.

    Returns:
        A fully populated ``RetrievalExplanation``.
    """
    citations = _build_citations(hybrid_results)
    confidence = aggregate_confidence(hybrid_results)
    graph_path = build_graph_path(hybrid_results, db, organization_id)
    summary = _build_summary(hybrid_results, confidence, retrieval_mode)

    return RetrievalExplanation(
        question=question,
        retrieval_mode=retrieval_mode,
        confidence=confidence,
        result_count=len(hybrid_results),
        citations=citations,
        graph_path=graph_path,
        summary=summary,
    )


def aggregate_confidence(hybrid_results: list[HybridResult]) -> float:
    """Compute a single confidence value in [0.0, 1.0] for the retrieval pass.

    Strategy:
    - If no results: confidence = 0.0.
    - If one result: confidence = that result's score.
    - Otherwise: weighted average using rank-decay weights (1/rank).
      The top result has 2× the influence of the second, 3× the third, etc.
      This rewards retrievals where the top hit is strong.

    The final value is clamped to [0.0, 1.0].
    """
    if not hybrid_results:
        return 0.0
    if len(hybrid_results) == 1:
        return max(0.0, min(1.0, hybrid_results[0].score))

    total_weight = 0.0
    weighted_sum = 0.0
    for rank, result in enumerate(hybrid_results, start=1):
        w = 1.0 / rank
        total_weight += w
        weighted_sum += result.score * w

    return max(0.0, min(1.0, weighted_sum / total_weight))


def build_graph_path(
    hybrid_results: list[HybridResult],
    db: Session,
    organization_id: UUID,
) -> list[GraphPathStep]:
    """Return the shortest entity relationship path linking the top retrieved
    memories.

    The path connects the first entity of result[0] to the first entity of
    result[1] (when both exist and a direct relationship exists between them).
    For brevity, only direct edges between any entity in result[0]'s set and
    any entity in result[1]'s set are returned — no multi-hop BFS, which is
    reserved for Milestone 5.5+ graph traversal features.

    Returns an empty list when:
    - fewer than two results
    - no results have matched entities
    - no direct graph edge exists between the top two results' entity sets
    """
    if len(hybrid_results) < 2:
        return []

    # Collect entity names → IDs for first two results
    top_entity_names_0 = set(hybrid_results[0].matched_entities)
    top_entity_names_1 = set(hybrid_results[1].matched_entities)

    if not top_entity_names_0 or not top_entity_names_1:
        return []

    # Look up entity objects by name (scoped to org)
    entities_0 = _entities_by_names(db, organization_id, top_entity_names_0)
    entities_1 = _entities_by_names(db, organization_id, top_entity_names_1)

    if not entities_0 or not entities_1:
        return []

    ids_0 = {e.id for e in entities_0}
    ids_1 = {e.id for e in entities_1}
    name_map: dict[UUID, str] = {e.id: e.name for e in entities_0 + entities_1}

    # Find direct relationships between the two sets
    rels = db.scalars(
        select(EntityRelationship).where(
            EntityRelationship.organization_id == organization_id,
            EntityRelationship.source_entity_id.in_(list(ids_0)),
            EntityRelationship.target_entity_id.in_(list(ids_1)),
        )
    ).all()

    # Also check reverse direction
    rels_rev = db.scalars(
        select(EntityRelationship).where(
            EntityRelationship.organization_id == organization_id,
            EntityRelationship.source_entity_id.in_(list(ids_1)),
            EntityRelationship.target_entity_id.in_(list(ids_0)),
        )
    ).all()

    steps: list[GraphPathStep] = []

    for rel in rels:
        src_name = name_map.get(rel.source_entity_id, str(rel.source_entity_id))
        tgt_name = name_map.get(rel.target_entity_id, str(rel.target_entity_id))
        steps.append(
            GraphPathStep(
                source_entity_id=rel.source_entity_id,
                source_entity_name=src_name,
                relationship_type=rel.relationship_type.value,
                target_entity_id=rel.target_entity_id,
                target_entity_name=tgt_name,
            )
        )

    for rel in rels_rev:
        src_name = name_map.get(rel.source_entity_id, str(rel.source_entity_id))
        tgt_name = name_map.get(rel.target_entity_id, str(rel.target_entity_id))
        steps.append(
            GraphPathStep(
                source_entity_id=rel.source_entity_id,
                source_entity_name=src_name,
                relationship_type=rel.relationship_type.value,
                target_entity_id=rel.target_entity_id,
                target_entity_name=tgt_name,
            )
        )

    return steps


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_citations(hybrid_results: list[HybridResult]) -> list[Citation]:
    citations = []
    for rank, result in enumerate(hybrid_results, start=1):
        citations.append(
            Citation(
                memory_id=result.memory.id,
                memory_title=result.memory.title,
                memory_type=result.memory.memory_type.value,
                retrieval_reason=result.retrieval_reason,
                semantic_score=result.semantic_score,
                graph_score=result.graph_score,
                link_score=result.link_score,
                final_score=result.score,
                graph_distance=result.graph_distance,
                matched_entities=result.matched_entities,
                rank=rank,
            )
        )
    return citations


def _build_summary(
    hybrid_results: list[HybridResult],
    confidence: float,
    retrieval_mode: str,
) -> str:
    """Build a one-line plain-English retrieval summary."""
    n = len(hybrid_results)
    if n == 0:
        return "No relevant memories were found for this query."

    semantic_count = sum(1 for r in hybrid_results if r.semantic_score > 0)
    graph_count = sum(1 for r in hybrid_results if r.graph_score > 0)
    link_count = sum(1 for r in hybrid_results if r.link_score > 0)

    parts = [f"Retrieved {n} memory {'entry' if n == 1 else 'entries'}"]
    if retrieval_mode == "hybrid":
        signals = []
        if semantic_count:
            signals.append(f"{semantic_count} via semantic similarity")
        if graph_count:
            signals.append(f"{graph_count} via graph expansion")
        if link_count:
            signals.append(f"{link_count} via memory links")
        if signals:
            parts.append("(" + ", ".join(signals) + ")")
    parts.append(f"with confidence {confidence:.2f}.")
    return " ".join(parts)


def _entities_by_names(
    db: Session, organization_id: UUID, names: set[str]
) -> list[Entity]:
    if not names:
        return []
    return list(
        db.scalars(
            select(Entity).where(
                Entity.organization_id == organization_id,
                Entity.name.in_(list(names)),
            )
        ).all()
    )
