"""
Chat endpoint for TeamMemoryOS — POST /api/v1/chat/ask.

Drives the full RAG pipeline:
  receive question → retrieve memories → build prompt → Granite → return answer.
When use_hybrid=True the retrieval stage uses HybridRetriever and the response
includes a full RetrievalExplanation.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.memory.rag_generation import run_rag
from app.models.user import User
from app.schemas.chat import ChatAskRequest, ChatAskResponse
from app.schemas.retrieval import (
    CitationRead,
    GraphPathStepRead,
    RetrievalExplanationRead,
)

router = APIRouter()


def _serialize_explanation(explanation) -> RetrievalExplanationRead | None:
    """Convert internal RetrievalExplanation dataclass → Pydantic schema."""
    if explanation is None:
        return None
    return RetrievalExplanationRead(
        question=explanation.question,
        retrieval_mode=explanation.retrieval_mode,
        confidence=explanation.confidence,
        result_count=explanation.result_count,
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
            for c in explanation.citations
        ],
        graph_path=[
            GraphPathStepRead(
                source_entity_id=s.source_entity_id,
                source_entity_name=s.source_entity_name,
                relationship_type=s.relationship_type,
                target_entity_id=s.target_entity_id,
                target_entity_name=s.target_entity_name,
            )
            for s in explanation.graph_path
        ],
        summary=explanation.summary,
    )


@router.post("/ask", response_model=ChatAskResponse)
def ask(
    body: ChatAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ask a question grounded in the organisation's memory.

    Performs semantic retrieval over the caller's organisation, assembles a
    Granite prompt with citations, runs inference, and returns the generated
    answer alongside structured citation metadata.

    When ``use_hybrid=True`` the response also contains a full
    ``explanation`` block with citations, graph path, and confidence score.

    Authentication is required — the JWT must belong to a valid user.
    Organisation scoping is enforced in the retrieval layer.
    """
    result = run_rag(
        db=db,
        question=body.question,
        organization_id=body.organization_id,
        top_k=body.top_k,
        scenario_id=body.scenario_id,
        use_hybrid=body.use_hybrid,
    )
    return ChatAskResponse(
        answer=result.answer,
        citations=result.citations,
        retrieved_memory_count=result.retrieved_memory_count,
        provider_used=result.provider_used,
        retrieval_mode=result.retrieval_mode,
        explanation=_serialize_explanation(result.explanation),
    )
