"""
POST /api/v1/retrieval/hybrid-search

Executes the five-stage HybridRetriever pipeline and returns ranked memory
results with full explainability metadata.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.graph.hybrid_retriever import HybridRetriever
from app.models.user import User
from app.schemas.memory_entry import MemoryEntryRead
from app.schemas.retrieval import (
    GraphStats,
    HybridResultRead,
    HybridSearchRequest,
    HybridSearchResponse,
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
