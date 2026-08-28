"""
Retrieval endpoints for TeamMemoryOS.

POST /api/v1/retrieval/hybrid-search
    Five-stage HybridRetriever pipeline with score breakdown.

POST /api/v1/retrieval/explain
    Same pipeline but returns the full RetrievalExplanation without LLM
    generation — useful for debugging, UI citation panels, and audit trails.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.graph.explanation_builder import build_retrieval_explanation
from app.graph.hybrid_retriever import HybridRetriever
from app.models.user import User
from app.schemas.memory_entry import MemoryEntryRead
from app.schemas.retrieval import (
    CitationRead,
    ExplainRequest,
    ExplainResponse,
    GraphPathStepRead,
    GraphStats,
    HybridResultRead,
    HybridSearchRequest,
    HybridSearchResponse,
    RetrievalExplanationRead,
)

router = APIRouter()


@router.post("/hybrid-search", response_model=HybridSearchResponse)
def hybrid_search(
    body: HybridSearchRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Hybrid (semantic + graph + memory-link) retrieval over organisational memory.

    Pipeline:
    1. Semantic pgvector retrieval (seed memories).
    2. Entity expansion from seed memories.
    3. One-hop graph neighbor expansion via EntityRelationship.
    4. MemoryLink expansion from seeds.
    5. Merge, score, and rank all candidates.

    Returns ranked results with explainability metadata (retrieval reason,
    matched entities, graph distance, score breakdown).
    """
    retriever = HybridRetriever(
        db=db,
        organization_id=body.organization_id,
        top_k=body.top_k,
    )
    hybrid_results = retriever.retrieve(body.question)

    # Build graph stats for the response
    seed_count = sum(1 for r in hybrid_results if r.graph_distance == 0)
    graph_exp = sum(1 for r in hybrid_results if r.graph_distance == 1)
    link_exp = sum(1 for r in hybrid_results if r.graph_distance == 2)
    all_entities = {e for r in hybrid_results for e in r.matched_entities}

    stats = GraphStats(
        seed_count=seed_count,
        entity_count=len(all_entities),
        graph_expanded_entity_count=graph_exp,
        link_expanded_count=link_exp,
        total_candidates_evaluated=len(hybrid_results),
    )

    results = [
        HybridResultRead(
            memory=MemoryEntryRead.model_validate(r.memory),
            score=r.score,
            semantic_score=r.semantic_score,
            graph_score=r.graph_score,
            link_score=r.link_score,
            retrieval_reason=r.retrieval_reason,
            matched_entities=r.matched_entities,
            graph_distance=r.graph_distance,
        )
        for r in hybrid_results
    ]

    return HybridSearchResponse(
        question=body.question,
        organization_id=body.organization_id,
        results=results,
        graph_stats=stats,
        retrieval_mode="hybrid",
    )


@router.post("/explain", response_model=ExplainResponse)
def explain_retrieval(
    body: ExplainRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Explain hybrid retrieval without LLM generation.

    Runs the full HybridRetriever pipeline and returns:
    * Ranked result list with per-memory score breakdowns.
    * A ``RetrievalExplanation`` with citations, graph path, confidence,
      and a plain-English summary.

    No Granite inference is performed — purely deterministic retrieval
    metadata.  Useful for UI citation panels, audit trails, and debugging.
    """
    retriever = HybridRetriever(
        db=db,
        organization_id=body.organization_id,
        top_k=body.top_k,
    )
    hybrid_results = retriever.retrieve(body.question)

    explanation_obj = build_retrieval_explanation(
        question=body.question,
        hybrid_results=hybrid_results,
        db=db,
        organization_id=body.organization_id,
        retrieval_mode="hybrid",
    )

    explanation_read = RetrievalExplanationRead(
        question=explanation_obj.question,
        retrieval_mode=explanation_obj.retrieval_mode,
        confidence=explanation_obj.confidence,
        result_count=explanation_obj.result_count,
        citations=[
            CitationRead(
                memory_id=c.memory_id,
                memory_title=c.memory_title,
                memory_type=c.memory_type,
                retrieval_reason=c.retrieval_reason,
                semantic_score=c.semantic_score,
                graph_score=c.graph_score,
                link_score=c.link_score,
                final_score=c.final_score,
                graph_distance=c.graph_distance,
                matched_entities=c.matched_entities,
                rank=c.rank,
            )
            for c in explanation_obj.citations
        ],
        graph_path=[
            GraphPathStepRead(
                source_entity_id=s.source_entity_id,
                source_entity_name=s.source_entity_name,
                relationship_type=s.relationship_type,
                target_entity_id=s.target_entity_id,
                target_entity_name=s.target_entity_name,
            )
            for s in explanation_obj.graph_path
        ],
        summary=explanation_obj.summary,
    )

    results = [
        HybridResultRead(
            memory=MemoryEntryRead.model_validate(r.memory),
            score=r.score,
            semantic_score=r.semantic_score,
            graph_score=r.graph_score,
            link_score=r.link_score,
            retrieval_reason=r.retrieval_reason,
            matched_entities=r.matched_entities,
            graph_distance=r.graph_distance,
        )
        for r in hybrid_results
    ]

    return ExplainResponse(explanation=explanation_read, results=results)
