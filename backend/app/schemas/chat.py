from uuid import UUID
from typing import List

from pydantic import BaseModel, Field


class ChatAskRequest(BaseModel):
    """Request body for POST /api/v1/chat/ask."""

    organization_id: UUID
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    scenario_id: UUID | None = None
    use_hybrid: bool = Field(
        default=False,
        description=(
            "When True, use the HybridRetriever (semantic + graph + memory-link) "
            "instead of semantic-only retrieval."
        ),
    )


class ChatAskResponse(BaseModel):
    """Response body for POST /api/v1/chat/ask."""

    answer: str
    citations: List[str]
    retrieved_memory_count: int
    provider_used: str
    retrieval_mode: str = "semantic"
