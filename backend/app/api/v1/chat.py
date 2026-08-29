"""
Chat endpoint for TeamMemoryOS — POST /api/v1/chat/ask.

Drives the full RAG pipeline:
  receive question → retrieve memories → build prompt → Granite → return answer.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.memory.rag_generation import run_rag
from app.models.user import User
from app.schemas.chat import ChatAskRequest, ChatAskResponse

router = APIRouter()


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

    Authentication is required — the JWT must belong to a valid user.
    Organisation scoping is enforced in the retrieval layer.
    """
    result = run_rag(
        db=db,
        question=body.question,
        organization_id=body.organization_id,
        top_k=body.top_k,
        scenario_id=body.scenario_id,
    )
    return ChatAskResponse(
        answer=result.answer,
        citations=result.citations,
        retrieved_memory_count=result.retrieved_memory_count,
        provider_used=result.provider_used,
    )
