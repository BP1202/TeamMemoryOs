"""
LangChain Streaming Engine for TeamMemoryOS.

Yields Server-Sent Events (SSE) compatible with FastAPI StreamingResponse:
  1. metadata  — Emits retrieved documents, citations count, provider used, and retrieval mode.
  2. token     — Emits individual LLM generation token chunks as they arrive.
  3. citation  — Emits individual citation entries for client rendering.
  4. done      — Emits final completion payload with accumulated text and metrics.
"""
from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any, Optional
from uuid import UUID

from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessageChunk
from langchain_core.prompts import ChatPromptTemplate
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.langchain.chat_model import get_chat_model
from app.langchain.prompt_templates import (
    format_documents_to_citations,
    format_documents_to_context,
    get_prompt_template,
)
from app.langchain.retriever import TeamMemoryPGVectorRetriever, get_memory_retriever
from app.memory.embedding_provider import EmbeddingProvider

logger = logging.getLogger(__name__)


def _format_sse(event_data: dict[str, Any]) -> str:
    """Format dictionary payload as SSE event."""
    return f"data: {json.dumps(event_data)}\n\n"


def stream_rag_chain(
    db: Session,
    question: str,
    organization_id: UUID,
    top_k: int = 5,
    scenario_id: Optional[UUID] = None,
    scenario_type: Optional[str] = None,
    prompt_template: Optional[ChatPromptTemplate] = None,
    chat_model: Optional[BaseChatModel] = None,
    embedding_provider: Optional[EmbeddingProvider] = None,
    retriever: Optional[TeamMemoryPGVectorRetriever] = None,
    score_threshold: Optional[float] = None,
) -> Iterator[str]:
    """Execute LangChain RAG pipeline and yield SSE-formatted stream events.

    Yields:
        SSE-formatted strings ("data: {...}\\n\\n") for metadata, tokens, citations, and done.
    """
    active_retriever = retriever or get_memory_retriever(
        db=db,
        organization_id=organization_id,
        scenario_id=scenario_id,
        top_k=top_k,
        score_threshold=score_threshold,
        embedding_provider=embedding_provider,
    )
    active_prompt = prompt_template or get_prompt_template(scenario_type)
    active_llm = chat_model or get_chat_model(streaming=True)
    provider_name = getattr(active_llm, "model_name", "ollama") or "ollama"

    # 1. Retrieve relevant documents
    docs: list[Document] = active_retriever.invoke(question)

    citations: list[str] = []
    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata or {}
        m_type = meta.get("memory_type", "memory")
        title = f" — {meta['title']}" if meta.get("title") else ""
        m_id = meta.get("memory_id") or meta.get("id") or "unknown"
        citations.append(f"[{i}] {m_type}{title} (id: {m_id})")

    # 2. Emit initial metadata event
    metadata_event = {
        "type": "metadata",
        "citations": citations,
        "retrieved_memory_count": len(docs),
        "provider_used": provider_name,
        "retrieval_mode": "semantic",
    }
    yield _format_sse(metadata_event)

    # 3. Emit individual citation events for UI components
    for cit in citations:
        yield _format_sse({
            "type": "citation",
            "citation": cit,
        })

    # 4. Format prompt
    context = format_documents_to_context(docs)
    citations_text = format_documents_to_citations(docs)
    prompt_value = active_prompt.invoke({
        "question": question,
        "context": context,
        "citations": citations_text,
    })

    # 5. Stream LLM tokens
    accumulated_tokens: list[str] = []
    try:
        for chunk in active_llm.stream(prompt_value):
            token = chunk.content if isinstance(chunk, AIMessageChunk) else str(chunk)
            if token:
                accumulated_tokens.append(token)
                yield _format_sse({
                    "type": "token",
                    "token": token,
                })
    except Exception as exc:
        logger.error("[StreamRAG] Generation stream error: %s", exc)
        err_msg = f"\n[Generation error: {type(exc).__name__} - {str(exc)}]"
        accumulated_tokens.append(err_msg)
        yield _format_sse({"type": "token", "token": err_msg})

    # 6. Emit done event
    full_answer = "".join(accumulated_tokens).strip()
    done_event = {
        "type": "done",
        "answer": full_answer,
        "citations": citations,
        "retrieved_memory_count": len(docs),
        "provider_used": provider_name,
        "retrieval_mode": "semantic",
    }
    yield _format_sse(done_event)


async def astream_rag_chain(
    db: Session,
    question: str,
    organization_id: UUID,
    top_k: int = 5,
    scenario_id: Optional[UUID] = None,
    scenario_type: Optional[str] = None,
    prompt_template: Optional[ChatPromptTemplate] = None,
    chat_model: Optional[BaseChatModel] = None,
    embedding_provider: Optional[EmbeddingProvider] = None,
    retriever: Optional[TeamMemoryPGVectorRetriever] = None,
    score_threshold: Optional[float] = None,
) -> AsyncIterator[str]:
    """Asynchronous variant of stream_rag_chain yielding SSE chunks."""
    active_retriever = retriever or get_memory_retriever(
        db=db,
        organization_id=organization_id,
        scenario_id=scenario_id,
        top_k=top_k,
        score_threshold=score_threshold,
        embedding_provider=embedding_provider,
    )
    active_prompt = prompt_template or get_prompt_template(scenario_type)
    active_llm = chat_model or get_chat_model(streaming=True)
    provider_name = getattr(active_llm, "model_name", "ollama") or "ollama"

    docs: list[Document] = await active_retriever.ainvoke(question)

    citations: list[str] = []
    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata or {}
        m_type = meta.get("memory_type", "memory")
        title = f" — {meta['title']}" if meta.get("title") else ""
        m_id = meta.get("memory_id") or meta.get("id") or "unknown"
        citations.append(f"[{i}] {m_type}{title} (id: {m_id})")

    yield _format_sse({
        "type": "metadata",
        "citations": citations,
        "retrieved_memory_count": len(docs),
        "provider_used": provider_name,
        "retrieval_mode": "semantic",
    })

    for cit in citations:
        yield _format_sse({
            "type": "citation",
            "citation": cit,
        })

    context = format_documents_to_context(docs)
    citations_text = format_documents_to_citations(docs)
    prompt_value = await active_prompt.ainvoke({
        "question": question,
        "context": context,
        "citations": citations_text,
    })

    accumulated_tokens: list[str] = []
    try:
        async for chunk in active_llm.astream(prompt_value):
            token = chunk.content if isinstance(chunk, AIMessageChunk) else str(chunk)
            if token:
                accumulated_tokens.append(token)
                yield _format_sse({
                    "type": "token",
                    "token": token,
                })
    except Exception as exc:
        logger.error("[AstreamRAG] Async generation stream error: %s", exc)
        err_msg = f"\n[Generation error: {type(exc).__name__} - {str(exc)}]"
        accumulated_tokens.append(err_msg)
        yield _format_sse({"type": "token", "token": err_msg})

    full_answer = "".join(accumulated_tokens).strip()
    yield _format_sse({
        "type": "done",
        "answer": full_answer,
        "citations": citations,
        "retrieved_memory_count": len(docs),
        "provider_used": provider_name,
        "retrieval_mode": "semantic",
    })
