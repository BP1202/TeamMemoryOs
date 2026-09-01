from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.memory_entry import MemoryEntryRead


# ---------------------------------------------------------------------------
# Hybrid search schemas (existing — unchanged)
# ---------------------------------------------------------------------------

class HybridSearchRequest(BaseModel):
    """Request body for POST /api/v1/retrieval/hybrid-search."""

    organization_id: UUID
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class HybridResultRead(BaseModel):
    """A single ranked result in the hybrid search response."""

    memory: MemoryEntryRead
    score: float = Field(..., ge=0.0, le=1.0)
    semantic_score: float = Field(..., ge=0.0, le=1.0)
    graph_score: float = Field(..., ge=0.0, le=1.0)
    link_score: float = Field(..., ge=0.0, le=1.0)
    retrieval_reason: str
    matched_entities: list[str]
    graph_distance: int

    model_config = ConfigDict(from_attributes=True)


class GraphStats(BaseModel):
    """Statistics about the graph expansion pass for explainability."""

    seed_count: int
    entity_count: int
    graph_expanded_entity_count: int
    link_expanded_count: int
    total_candidates_evaluated: int


class HybridSearchResponse(BaseModel):
    """Response body for POST /api/v1/retrieval/hybrid-search."""

    question: str
    organization_id: UUID
    results: list[HybridResultRead]
    graph_stats: GraphStats
    retrieval_mode: str = "hybrid"


# ---------------------------------------------------------------------------
# Explanation schemas (new — Milestone 5.5)
# ---------------------------------------------------------------------------

class CitationRead(BaseModel):
    """Structured citation for one retrieved memory."""

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


class GraphPathStepRead(BaseModel):
    """One hop in the entity graph path."""

    source_entity_id: UUID
    source_entity_name: str
    relationship_type: str
    target_entity_id: UUID
    target_entity_name: str


class RetrievalExplanationRead(BaseModel):
    """Complete retrieval explanation returned by /retrieval/explain."""

    question: str
    retrieval_mode: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    result_count: int
    citations: list[CitationRead]
    graph_path: list[GraphPathStepRead]
    summary: str


class ExplainRequest(BaseModel):
    """Request body for POST /api/v1/retrieval/explain."""

    organization_id: UUID
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class ExplainResponse(BaseModel):
    """Response body for POST /api/v1/retrieval/explain.

    Returns the full retrieval explanation without LLM generation.
    """

    explanation: RetrievalExplanationRead
    results: list[HybridResultRead]
