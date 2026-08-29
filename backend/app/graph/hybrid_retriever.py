"""
HybridRetriever — deterministic five-stage GraphRAG retrieval pipeline.

Pipeline stages
───────────────
1. Semantic retrieval    — pgvector cosine search for the top-k seed memories.
2. Entity expansion      — collect all entities attached to seed memories.
3. Graph expansion       — walk one hop to neighbor entities via EntityRelationship.
4. MemoryLink expansion  — find high-scored MemoryLink targets from seeds.
5. Merge + rank          — combine all candidate memories, score, deduplicate.

Ranking weights
───────────────
  semantic_score          0.5   (1 − cosine_distance, normalised)
  memory_link_score       0.3   (best MemoryLink score connecting seed → candidate)
  graph_boost             0.2   (1.0 if candidate shares a graph-expanded entity, else 0)

Final score is always in [0.0, 1.0].
Retrieval is fully deterministic and LLM-free.

The interface is designed to be compatible with a future LangChain retriever
wrapper — the public ``retrieve()`` method accepts a plain ``str`` question
and returns a list of ``HybridResult`` dataclasses.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.memory.embedding_provider import EmbeddingProvider, StubEmbeddingProvider
from app.models.entity import Entity, EntityRelationship, MemoryEntity
from app.models.memory_entry import EMBEDDING_DIM, MemoryEntry
from app.models.memory_link import MemoryLink
from app.services.memory_entry import semantic_search

# ---------------------------------------------------------------------------
# Weights — must sum to 1.0
# ---------------------------------------------------------------------------
_W_SEMANTIC = 0.5
_W_MEMORY_LINK = 0.3
_W_GRAPH = 0.2


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class HybridResult:
    """A single ranked memory entry returned by the HybridRetriever.

    Attributes:
        memory:          The retrieved ``MemoryEntry``.
        score:           Final weighted score in [0.0, 1.0].
        semantic_score:  Normalised cosine similarity (0 when not a seed).
        graph_score:     1.0 when a graph-expanded entity connects this memory.
        link_score:      Best MemoryLink score from any seed to this memory.
        retrieval_reason: Human-readable explanation of why this was retrieved.
        matched_entities: Names of entities that contributed to retrieval.
        graph_distance:  0 for seeds, 1 for graph-expanded, 2 for link-only.
    """

    memory: MemoryEntry
    score: float
    semantic_score: float = 0.0
    graph_score: float = 0.0
    link_score: float = 0.0
    retrieval_reason: str = ""
    matched_entities: list[str] = field(default_factory=list)
    graph_distance: int = 0


# ---------------------------------------------------------------------------
# HybridRetriever
# ---------------------------------------------------------------------------

class HybridRetriever:
    """Hybrid (semantic + graph + link) retriever for organisational memory.

    Designed to be LangChain-compatible in interface: ``retrieve(question)``
    returns a ranked list of ``HybridResult`` objects.

    Instantiate once per request — it holds no mutable state between calls.
    """

    def __init__(
        self,
        db: Session,
        organization_id: UUID,
        embedding_provider: EmbeddingProvider | None = None,
        top_k: int = 5,
        seed_multiplier: int = 3,
    ) -> None:
        """
        Args:
            db:                Active SQLAlchemy session.
            organization_id:   Scope all queries to this organisation.
            embedding_provider: Override the embedding provider (useful in tests).
            top_k:             Number of final results to return.
            seed_multiplier:   Fetch ``top_k * seed_multiplier`` semantic seeds
                               before graph expansion.  Default 3.
        """
        self.db = db
        self.organization_id = organization_id
        self.provider: EmbeddingProvider = embedding_provider or StubEmbeddingProvider()
        self.top_k = top_k
        self.seed_k = top_k * seed_multiplier

    # ------------------------------------------------------------------
    # Public interface (LangChain-compatible entry point)
    # ------------------------------------------------------------------

    def retrieve(self, question: str) -> list[HybridResult]:
        """Execute the full hybrid pipeline and return ``top_k`` ranked results.

        Args:
            question: Free-form question or query string.

        Returns:
            List of ``HybridResult`` objects, sorted by descending score,
            length ≤ ``top_k``.
        """
        query_embedding = self.provider.embed(question)
        return self._run_pipeline(query_embedding)

    # ------------------------------------------------------------------
    # Internal pipeline stages
    # ------------------------------------------------------------------

    def _run_pipeline(self, query_embedding: list[float]) -> list[HybridResult]:
        # Stage 1 — Semantic seeds
        seed_entries = self._semantic_stage(query_embedding)
        if not seed_entries:
            return []

        seed_ids = {e.id for e in seed_entries}
        seed_distances = self._compute_distances(query_embedding, seed_entries)

        # Stage 2 — Entity expansion from seeds
        seed_entity_ids: set[UUID] = set()
        entity_to_memories: dict[UUID, set[UUID]] = {}  # entity_id → memory_ids
        for entry in seed_entries:
            eids = self._get_entity_ids_for_memory(entry.id)
            seed_entity_ids.update(eids)
            for eid in eids:
                entity_to_memories.setdefault(eid, set()).add(entry.id)

        # Stage 3 — Graph neighbor entity expansion (1 hop)
        graph_entity_ids: set[UUID] = set()
        if seed_entity_ids:
            graph_entity_ids = self._graph_expand(seed_entity_ids)

        # All expanded entity IDs (seed + graph neighbors)
        all_entity_ids = seed_entity_ids | graph_entity_ids

        # Stage 4 — MemoryLink expansion from seeds
        link_scores: dict[UUID, float] = {}  # target_memory_id → best score
        for seed_id in seed_ids:
            for link in self._get_best_memory_links(seed_id):
                tid = link.target_memory_id
                if tid not in seed_ids:
                    link_scores[tid] = max(link_scores.get(tid, 0.0), link.score)

        # Stage 5 — Collect all candidate memory IDs (excluding seeds initially)
        candidate_ids: set[UUID] = set(link_scores.keys())
        if all_entity_ids:
            candidate_ids.update(
                self._memories_sharing_entities(all_entity_ids, exclude_ids=seed_ids)
            )

        # Load candidate memory entries
        candidates = self._load_memories(candidate_ids - seed_ids)
        candidate_map: dict[UUID, MemoryEntry] = {e.id: e for e in candidates}

        # Build entity lookup for candidates
        cand_entities: dict[UUID, set[UUID]] = {}
        for mid in candidate_ids - seed_ids:
            cand_entities[mid] = self._get_entity_ids_for_memory(mid)

        # Stage 5 — Rank: assemble HybridResult for all candidates + seeds
        results: dict[UUID, HybridResult] = {}

        # Seeds
        for entry in seed_entries:
            dist = seed_distances.get(entry.id, 1.0)
            sem = max(0.0, min(1.0, 1.0 - dist))
            link = link_scores.get(entry.id, 0.0)
            graph = 0.0
            entities_hit = self._entity_names_for_ids(
                self._get_entity_ids_for_memory(entry.id)
            )
            reasons = ["semantic similarity"]
            if graph:
                reasons.append("graph neighbor")
            if link > 0:
                reasons.append(f"memory link ({link:.2f})")
            score = _weighted_score(sem, graph, link)
            results[entry.id] = HybridResult(
                memory=entry,
                score=score,
                semantic_score=sem,
                graph_score=graph,
                link_score=link,
                retrieval_reason=", ".join(reasons),
                matched_entities=entities_hit,
                graph_distance=0,
            )

        # Graph-expanded + link-expanded candidates
        for mid in candidate_ids - seed_ids:
            entry = candidate_map.get(mid)
            if entry is None:
                continue

            eid_set = cand_entities.get(mid, set())
            graph = 1.0 if eid_set & graph_entity_ids else 0.0
            link = link_scores.get(mid, 0.0)
            sem = 0.0  # not a semantic seed
            entities_hit = self._entity_names_for_ids(eid_set & all_entity_ids)

            reasons: list[str] = []
            if graph:
                reasons.append("graph entity expansion")
            if link > 0:
                reasons.append(f"memory link ({link:.2f})")
            if not reasons:
                reasons.append("entity overlap")

            distance = 1 if graph else 2

            score = _weighted_score(sem, graph, link)
            results[mid] = HybridResult(
                memory=entry,
                score=score,
                semantic_score=sem,
                graph_score=graph,
                link_score=link,
                retrieval_reason=", ".join(reasons),
                matched_entities=entities_hit,
                graph_distance=distance,
            )

        # Sort and truncate
        ranked = sorted(results.values(), key=lambda r: r.score, reverse=True)
        return ranked[: self.top_k]

    # ------------------------------------------------------------------
    # Stage helpers
    # ------------------------------------------------------------------

    def _semantic_stage(self, query_embedding: list[float]) -> list[MemoryEntry]:
        return semantic_search(
            db=self.db,
            query_embedding=query_embedding,
            organization_id=self.organization_id,
            top_k=self.seed_k,
        )

    def _compute_distances(
        self, query_embedding: list[float], entries: list[MemoryEntry]
    ) -> dict[UUID, float]:
        """Compute cosine distance for each seed entry.

        When the entry has no stored embedding, distance defaults to 1.0
        (maximum distance — will yield semantic_score = 0.0).
        """
        distances: dict[UUID, float] = {}
        for entry in entries:
            if entry.embedding is not None:
                distances[entry.id] = _cosine_distance(
                    query_embedding, list(entry.embedding)
                )
            else:
                distances[entry.id] = 1.0
        return distances

    def _get_entity_ids_for_memory(self, memory_id: UUID) -> set[UUID]:
        rows = self.db.scalars(
            select(MemoryEntity.entity_id).where(
                MemoryEntity.memory_entry_id == memory_id
            )
        ).all()
        return set(rows)

    def _graph_expand(self, entity_ids: set[UUID]) -> set[UUID]:
        """Return entity IDs reachable in one hop from *entity_ids* via any
        relationship direction, scoped to the current organisation."""
        if not entity_ids:
            return set()
        eids = list(entity_ids)
        # Outgoing targets
        targets = set(
            self.db.scalars(
                select(EntityRelationship.target_entity_id).where(
                    EntityRelationship.source_entity_id.in_(eids),
                    EntityRelationship.organization_id == self.organization_id,
                )
            ).all()
        )
        # Incoming sources
        sources = set(
            self.db.scalars(
                select(EntityRelationship.source_entity_id).where(
                    EntityRelationship.target_entity_id.in_(eids),
                    EntityRelationship.organization_id == self.organization_id,
                )
            ).all()
        )
        return (targets | sources) - entity_ids

    def _get_best_memory_links(self, memory_id: UUID) -> list[MemoryLink]:
        """Return outgoing MemoryLinks from *memory_id*, best score first."""
        return list(
            self.db.scalars(
                select(MemoryLink)
                .where(
                    MemoryLink.source_memory_id == memory_id,
                    MemoryLink.organization_id == self.organization_id,
                )
                .order_by(MemoryLink.score.desc())
            ).all()
        )

    def _memories_sharing_entities(
        self, entity_ids: set[UUID], exclude_ids: set[UUID]
    ) -> set[UUID]:
        """Return memory IDs that have at least one entity in *entity_ids*."""
        if not entity_ids:
            return set()
        rows = self.db.scalars(
            select(MemoryEntity.memory_entry_id)
            .where(
                MemoryEntity.entity_id.in_(list(entity_ids)),
            )
            .distinct()
        ).all()
        return {r for r in rows if r not in exclude_ids}

    def _load_memories(self, memory_ids: set[UUID]) -> list[MemoryEntry]:
        if not memory_ids:
            return []
        return list(
            self.db.scalars(
                select(MemoryEntry).where(
                    MemoryEntry.id.in_(list(memory_ids)),
                    MemoryEntry.organization_id == self.organization_id,
                )
            ).all()
        )

    def _entity_names_for_ids(self, entity_ids: set[UUID]) -> list[str]:
        if not entity_ids:
            return []
        rows = self.db.scalars(
            select(Entity.name).where(Entity.id.in_(list(entity_ids)))
        ).all()
        return sorted(rows)


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _weighted_score(
    semantic: float,
    graph: float,
    link: float,
) -> float:
    score = (
        semantic * _W_SEMANTIC
        + graph * _W_GRAPH
        + link * _W_MEMORY_LINK
    )
    return max(0.0, min(1.0, score))


def _cosine_distance(a: list[float], b: list[float]) -> float:
    """Return cosine distance in [0.0, 2.0] between two vectors.

    Distance 0 = identical, 1 = orthogonal, 2 = opposite.
    Clamps to [0.0, 1.0] for safety.
    """
    if len(a) != len(b):
        return 1.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 1.0
    raw_dist = 1.0 - dot / (mag_a * mag_b)
    return max(0.0, min(1.0, raw_dist))
