"""
RAG generation service for TeamMemoryOS.

Orchestrates the complete end-to-end pipeline:

  1. Semantic retrieval   — embed the question, fetch top-k memory entries.
  2. Context building     — format entries into a structured context block.
  3. Prompt assembly      — combine system prompt, context, and question.
  4. Granite inference    — send the prompt to the configured generation provider.
  5. Response formatting  — return a structured ``ChatResponse`` dataclass.

When ``use_hybrid=True`` the retrieval stage is replaced by the five-stage
HybridRetriever (semantic + entity graph + memory links).  All other stages
are unchanged — the same prompt builder and Granite provider are used.

No LangChain.  Each step is a direct function call.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.settings import settings
from app.graph.hybrid_retriever import HybridRetriever
from app.memory.embedding_provider import EmbeddingProvider, StubEmbeddingProvider
from app.memory.generation_provider import GenerationProvider, get_generation_provider
from app.memory.prompt_builder import build_prompt
from app.memory.rag_context import build_rag_context
from app.schemas.memory_entry import MemoryEntryRead


@dataclass
class ChatResponse:
    """Structured result from a single RAG generation pass.

    Attributes:
        answer:                 Generated text from the model.
        citations:              Brief citation strings for each retrieved memory.
        retrieved_memory_count: Number of memory entries that were retrieved.
        provider_used:          Identifier of the generation provider that ran.
        retrieval_mode:         'semantic' or 'hybrid'.
    """

    answer: str
    citations: list[str] = field(default_factory=list)
    retrieved_memory_count: int = 0
    provider_used: str = "unknown"
    retrieval_mode: str = "semantic"


def run_rag(
    db: Session,
    question: str,
    organization_id: UUID,
    top_k: int = 5,
    scenario_id: UUID | None = None,
    embedding_provider: EmbeddingProvider | None = None,
    generation_provider: GenerationProvider | None = None,
    use_hybrid: bool = False,
) -> ChatResponse:
    """Execute the full RAG pipeline and return a ``ChatResponse``.

    Args:
        db:                   Active SQLAlchemy session.
        question:             The user's question.
        organization_id:      Restrict retrieval to this organisation's memory.
        top_k:                Maximum number of memory entries to retrieve.
        scenario_id:          Optional — restrict retrieval to one scenario.
        embedding_provider:   Override the embedding provider (useful in tests).
        generation_provider:  Override the generation provider (useful in tests).

    Returns:
        A ``ChatResponse`` with the generated answer and structured metadata.
    """
    emb_provider = embedding_provider or StubEmbeddingProvider()
    gen_provider = generation_provider or get_generation_provider()

    # ------------------------------------------------------------------ #
    # 1 + 2: Retrieve top-k memories and build context block              #
    # ------------------------------------------------------------------ #
    retrieval_mode = "semantic"
    if use_hybrid:
        retrieval_mode = "hybrid"
        retriever = HybridRetriever(
            db=db,
            organization_id=organization_id,
            embedding_provider=emb_provider,
            top_k=top_k,
        )
        hybrid_results = retriever.retrieve(question)
        retrieved_entries = [r.memory for r in hybrid_results]
        from app.memory.rag_context import _format_context
        context_text = _format_context(question, retrieved_entries)
    else:
        rag_ctx = build_rag_context(
            db=db,
            query=question,
            organization_id=organization_id,
            provider=emb_provider,
            top_k=top_k,
            scenario_id=scenario_id,
        )
        retrieved_entries = rag_ctx.entries
        context_text = rag_ctx.context_text

    # ------------------------------------------------------------------ #
    # 3: Assemble the prompt                                               #
    # ------------------------------------------------------------------ #
    prompt = build_prompt(
        question=question,
        context_text=context_text,
        entries=retrieved_entries,
        max_chars=settings.GRANITE_MAX_PROMPT_CHARS,
    )

    # ------------------------------------------------------------------ #
    # 4: Generate                                                          #
    # ------------------------------------------------------------------ #
    try:
        answer = gen_provider.generate(prompt)
    except Exception as exc:  # provider failure must not crash the API
        answer = (
            "I was unable to generate a response at this time. "
            f"Please try again later. (Provider error: {type(exc).__name__})"
        )

    # ------------------------------------------------------------------ #
    # 5: Build response citations                                          #
    # ------------------------------------------------------------------ #
    citations = _build_citation_strings(retrieved_entries)

    return ChatResponse(
        answer=answer,
        citations=citations,
        retrieved_memory_count=len(retrieved_entries),
        provider_used=gen_provider.provider_name,
        retrieval_mode=retrieval_mode,
    )


def _build_citation_strings(entries: list) -> list[str]:
    """Convert retrieved memory entries to compact citation strings."""
    result = []
    for i, entry in enumerate(entries, start=1):
        title = f" — {entry.title}" if entry.title else ""
        result.append(
            f"[{i}] {entry.memory_type.value}{title} (id: {entry.id})"
        )
    return result
