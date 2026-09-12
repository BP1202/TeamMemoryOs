"""
RAG generation service for TeamMemoryOS backed by LangChain Production Pipeline.

Orchestrates the complete LangChain retrieval-augmented generation workflow:
  1. Semantic retrieval via LangChain PGVector Retriever (or HybridRetriever in hybrid mode).
  2. Grounded Prompt Assembly via LangChain ChatPromptTemplates.
  3. LLM Inference via LangChain ChatOllama (with deterministic StubChatModel fallback).
  4. Structured Response Formatting via LangChain TeamMemoryOutputParser.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from typing import Any, TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.settings import settings
from app.graph.explanation_builder import RetrievalExplanation, build_retrieval_explanation
from app.graph.hybrid_retriever import HybridResult, HybridRetriever
from app.langchain.chains import build_rag_chain
from app.langchain.chat_model import StubChatModel, get_chat_model
from app.langchain.output_parser import TeamMemoryOutputParser, TeamMemoryRAGOutput
from app.langchain.prompt_templates import (
    format_documents_to_citations,
    format_documents_to_context,
    get_prompt_template,
)
from app.langchain.retriever import TeamMemoryPGVectorRetriever, get_memory_retriever
from app.langchain.streaming import stream_rag_chain
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
        explanation:            Full retrieval explanation (populated when
                                use_hybrid=True, else None).
    """

    answer: str
    citations: list[str] = field(default_factory=list)
    retrieved_memory_count: int = 0
    provider_used: str = "unknown"
    retrieval_mode: str = "semantic"
    explanation: RetrievalExplanation | None = None


def run_rag(
    db: Session,
    question: str,
    organization_id: UUID,
    top_k: int = 5,
    scenario_id: UUID | None = None,
    scenario_type: str | None = None,
    embedding_provider: EmbeddingProvider | None = None,
    generation_provider: GenerationProvider | None = None,
    use_hybrid: bool = False,
) -> ChatResponse:
    """Execute the LangChain RAG pipeline and return a ``ChatResponse``.

    Args:
        db:                   Active SQLAlchemy session.
        question:             The user's question.
        organization_id:      Restrict retrieval to this organisation's memory.
        top_k:                Maximum number of memory entries to retrieve.
        scenario_id:          Optional — restrict retrieval to one scenario.
        scenario_type:        Optional — prompt template selector ('engineering', 'incident', etc.).
        embedding_provider:   Override the embedding provider (useful in tests).
        generation_provider:  Override the generation provider (useful in tests).
        use_hybrid:           When True, use graph + link hybrid retrieval.

    Returns:
        A ``ChatResponse`` with the generated answer and structured metadata.
    """
    emb_provider = embedding_provider or StubEmbeddingProvider()

    # If an explicit legacy generation_provider is passed, handle through direct provider bridge
    if generation_provider is not None:
        return _run_rag_legacy_provider(
            db=db,
            question=question,
            organization_id=organization_id,
            top_k=top_k,
            scenario_id=scenario_id,
            embedding_provider=emb_provider,
            gen_provider=generation_provider,
            use_hybrid=use_hybrid,
        )

    retrieval_mode = "semantic"
    hybrid_results: list[HybridResult] = []
    explanation: RetrievalExplanation | None = None

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

        if hybrid_results:
            explanation = build_retrieval_explanation(
                question=question,
                hybrid_results=hybrid_results,
                db=db,
                organization_id=organization_id,
                retrieval_mode=retrieval_mode,
            )

        from app.memory.rag_context import _format_context
        context_text = _format_context(question, retrieved_entries)
        prompt = build_prompt(
            question=question,
            context_text=context_text,
            entries=retrieved_entries,
            max_chars=settings.GRANITE_MAX_PROMPT_CHARS,
        )
        chat_model = get_chat_model()
        try:
            response_msg = chat_model.invoke(prompt)
            answer = response_msg.content if hasattr(response_msg, "content") else str(response_msg)
        except Exception as exc:
            answer = (
                "I was unable to generate a response at this time. "
                f"Please try again later. (Provider error: {type(exc).__name__})"
            )
        citations = _build_citation_strings(retrieved_entries)
        provider_name = _normalize_provider_name(chat_model)

        return ChatResponse(
            answer=answer,
            citations=citations,
            retrieved_memory_count=len(retrieved_entries),
            provider_used=provider_name,
            retrieval_mode=retrieval_mode,
            explanation=explanation,
        )

    # LangChain Standard Pipeline Execution
    chain = build_rag_chain(
        db=db,
        organization_id=organization_id,
        scenario_id=scenario_id,
        top_k=top_k,
        scenario_type=scenario_type,
        embedding_provider=emb_provider,
    )

    try:
        output: TeamMemoryRAGOutput = chain.invoke(question)
        provider_name = output.provider_used
        if provider_name not in ("stub", "ollama"):
            provider_name = "stub" if getattr(settings, "LLM_PROVIDER", "ollama") == "stub" else "ollama"
        return ChatResponse(
            answer=output.answer,
            citations=output.citations,
            retrieved_memory_count=len(output.retrieved_memories) if output.retrieved_memories else len(output.citations),
            provider_used=provider_name,
            retrieval_mode=output.retrieval_mode,
            explanation=None,
        )
    except Exception as exc:
        return ChatResponse(
            answer=(
                "I was unable to generate a response at this time. "
                f"Please try again later. (Provider error: {type(exc).__name__})"
            ),
            citations=[],
            retrieved_memory_count=0,
            provider_used="unknown",
            retrieval_mode=retrieval_mode,
            explanation=None,
        )


def _normalize_provider_name(model: Any) -> str:
    """Normalize model identifier to 'stub' or 'ollama'."""
    if isinstance(model, StubChatModel) or getattr(settings, "LLM_PROVIDER", "ollama") == "stub":
        return "stub"
    name = getattr(model, "model_name", "ollama") or "ollama"
    if name in ("stub", "ollama"):
        return name
    return "stub" if "stub" in name.lower() else "ollama"


def _run_rag_legacy_provider(
    db: Session,
    question: str,
    organization_id: UUID,
    top_k: int,
    scenario_id: UUID | None,
    embedding_provider: EmbeddingProvider,
    gen_provider: GenerationProvider,
    use_hybrid: bool,
) -> ChatResponse:
    """Internal helper to support custom GenerationProvider instances passed in tests."""
    retrieval_mode = "semantic"
    hybrid_results: list[HybridResult] = []
    if use_hybrid:
        retrieval_mode = "hybrid"
        retriever = HybridRetriever(
            db=db,
            organization_id=organization_id,
            embedding_provider=embedding_provider,
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
            provider=embedding_provider,
            top_k=top_k,
            scenario_id=scenario_id,
        )
        retrieved_entries = rag_ctx.entries
        context_text = rag_ctx.context_text

    prompt = build_prompt(
        question=question,
        context_text=context_text,
        entries=retrieved_entries,
        max_chars=settings.GRANITE_MAX_PROMPT_CHARS,
    )

    try:
        answer = gen_provider.generate(prompt)
    except Exception as exc:
        answer = (
            "I was unable to generate a response at this time. "
            f"Please try again later. (Provider error: {type(exc).__name__})"
        )

    citations = _build_citation_strings(retrieved_entries)
    explanation: RetrievalExplanation | None = None
    if use_hybrid and hybrid_results:
        explanation = build_retrieval_explanation(
            question=question,
            hybrid_results=hybrid_results,
            db=db,
            organization_id=organization_id,
            retrieval_mode=retrieval_mode,
        )

    return ChatResponse(
        answer=answer,
        citations=citations,
        retrieved_memory_count=len(retrieved_entries),
        provider_used=gen_provider.provider_name,
        retrieval_mode=retrieval_mode,
        explanation=explanation,
    )


def _build_citation_strings(entries: list) -> list[str]:
    """Convert retrieved memory entries to compact citation strings."""
    result = []
    for i, entry in enumerate(entries, start=1):
        title = f" — {entry.title}" if getattr(entry, "title", None) else ""
        m_type = getattr(entry, "memory_type", "memory")
        m_type_val = m_type.value if hasattr(m_type, "value") else str(m_type)
        m_id = getattr(entry, "id", "unknown")
        result.append(f"[{i}] {m_type_val}{title} (id: {m_id})")
    return result


def stream_rag(
    db: Session,
    question: str,
    organization_id: UUID,
    top_k: int = 5,
    scenario_id: UUID | None = None,
    scenario_type: str | None = None,
    embedding_provider: EmbeddingProvider | None = None,
    generation_provider: GenerationProvider | None = None,
    use_hybrid: bool = False,
):
    """Execute LangChain RAG pipeline and yield Server-Sent Events (SSE) chunks."""
    if use_hybrid or generation_provider is not None:
        emb_provider = embedding_provider or StubEmbeddingProvider()
        gen_provider = generation_provider or get_generation_provider()
        retrieval_mode = "semantic"
        hybrid_results: list[HybridResult] = []
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

        citations = _build_citation_strings(retrieved_entries)

        metadata_event = {
            "type": "metadata",
            "citations": citations,
            "retrieved_memory_count": len(retrieved_entries),
            "provider_used": gen_provider.provider_name,
            "retrieval_mode": retrieval_mode,
        }
        yield f"data: {json.dumps(metadata_event)}\n\n"

        prompt = build_prompt(
            question=question,
            context_text=context_text,
            entries=retrieved_entries,
            max_chars=settings.GRANITE_MAX_PROMPT_CHARS,
        )

        accumulated_tokens: list[str] = []
        try:
            if hasattr(gen_provider, "stream_generate"):
                for token in gen_provider.stream_generate(prompt):
                    accumulated_tokens.append(token)
                    yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
            else:
                full_text = gen_provider.generate(prompt)
                accumulated_tokens.append(full_text)
                yield f"data: {json.dumps({'type': 'token', 'token': full_text})}\n\n"
        except Exception as exc:
            err_msg = f"\n[Generation error: {type(exc).__name__} - {str(exc)}]"
            accumulated_tokens.append(err_msg)
            yield f"data: {json.dumps({'type': 'token', 'token': err_msg})}\n\n"

        full_answer = "".join(accumulated_tokens)
        done_event = {
            "type": "done",
            "answer": full_answer,
            "citations": citations,
            "retrieved_memory_count": len(retrieved_entries),
            "provider_used": gen_provider.provider_name,
            "retrieval_mode": retrieval_mode,
        }
        yield f"data: {json.dumps(done_event)}\n\n"
    else:
        # Route through LangChain streaming engine
        for chunk in stream_rag_chain(
            db=db,
            question=question,
            organization_id=organization_id,
            top_k=top_k,
            scenario_id=scenario_id,
            scenario_type=scenario_type,
            embedding_provider=embedding_provider,
        ):
            yield chunk
