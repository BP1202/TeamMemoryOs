"""
LangChain Runnable Pipeline and Chains for TeamMemoryOS.

Composes the complete LCEL RunnableSequence:
  Retriever (PGVector)
      ↓
  PromptTemplate (Engineering/Incident/Repo/PR)
      ↓
  ChatModel (ChatOllama / Stub)
      ↓
  OutputParser (Structured Response)

Provides sync, async, and streaming invocation workflows.
"""
from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional
from uuid import UUID

from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    Runnable,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.langchain.chat_model import get_chat_model
from app.langchain.output_parser import TeamMemoryOutputParser, TeamMemoryRAGOutput
from app.langchain.prompt_templates import (
    format_documents_to_citations,
    format_documents_to_context,
    get_prompt_template,
)
from app.langchain.retriever import TeamMemoryPGVectorRetriever, get_memory_retriever
from app.memory.embedding_provider import EmbeddingProvider

logger = logging.getLogger(__name__)


def build_rag_chain(
    db: Session,
    organization_id: UUID,
    scenario_id: Optional[UUID] = None,
    top_k: int = 5,
    score_threshold: Optional[float] = None,
    scenario_type: Optional[str] = None,
    prompt_template: Optional[ChatPromptTemplate] = None,
    chat_model: Optional[BaseChatModel] = None,
    embedding_provider: Optional[EmbeddingProvider] = None,
    retriever: Optional[TeamMemoryPGVectorRetriever] = None,
) -> Runnable:
    """Construct an end-to-end LCEL Runnable pipeline.

    Args:
        db: Active SQLAlchemy session.
        organization_id: Scope retrieval to this organization.
        scenario_id: Optional scenario filter.
        top_k: Number of memories to retrieve.
        score_threshold: Optional similarity threshold.
        scenario_type: Template selector ('engineering', 'incident', 'repository', 'pr').
        prompt_template: Custom prompt template override.
        chat_model: Custom chat model override.
        embedding_provider: Embedding provider override.
        retriever: Custom retriever override.

    Returns:
        A LangChain Runnable that accepts a string question or dict {"question": str}
        and returns a TeamMemoryRAGOutput.
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
    active_llm = chat_model or get_chat_model()
    parser = TeamMemoryOutputParser(
        retrieval_mode="semantic",
        provider_used=getattr(active_llm, "model_name", "ollama") or "ollama",
    )

    def extract_question(input_val: Any) -> str:
        if isinstance(input_val, dict):
            return input_val.get("question", "")
        return str(input_val)

    def retrieve_docs(input_dict: dict[str, Any]) -> dict[str, Any]:
        question = input_dict["question"]
        docs = active_retriever.invoke(question)
        context = format_documents_to_context(docs)
        citations = format_documents_to_citations(docs)
        return {
            "question": question,
            "docs": docs,
            "context": context,
            "citations": citations,
        }

    async def aretrieve_docs(input_dict: dict[str, Any]) -> dict[str, Any]:
        question = input_dict["question"]
        docs = await active_retriever.ainvoke(question)
        context = format_documents_to_context(docs)
        citations = format_documents_to_citations(docs)
        return {
            "question": question,
            "docs": docs,
            "context": context,
            "citations": citations,
        }

    def run_generation(prep: dict[str, Any]) -> TeamMemoryRAGOutput:
        prompt_val = active_prompt.invoke({
            "question": prep["question"],
            "context": prep["context"],
            "citations": prep["citations"],
        })
        response = active_llm.invoke(prompt_val)
        return parser.parse_with_documents(
            text_or_message=response,
            documents=prep["docs"],
            retrieval_mode="semantic",
            provider_used=getattr(active_llm, "model_name", "ollama") or "ollama",
        )

    async def arun_generation(prep: dict[str, Any]) -> TeamMemoryRAGOutput:
        prompt_val = await active_prompt.ainvoke({
            "question": prep["question"],
            "context": prep["context"],
            "citations": prep["citations"],
        })
        response = await active_llm.ainvoke(prompt_val)
        return parser.parse_with_documents(
            text_or_message=response,
            documents=prep["docs"],
            retrieval_mode="semantic",
            provider_used=getattr(active_llm, "model_name", "ollama") or "ollama",
        )

    pipeline = (
        RunnableLambda(extract_question)
        | RunnableLambda(lambda q: {"question": q})
        | RunnableLambda(retrieve_docs, afunc=aretrieve_docs)
        | RunnableLambda(run_generation, afunc=arun_generation)
    )

    return pipeline


def run_rag_chain(
    db: Session,
    question: str,
    organization_id: UUID,
    top_k: int = 5,
    scenario_id: Optional[UUID] = None,
    scenario_type: Optional[str] = None,
    embedding_provider: Optional[EmbeddingProvider] = None,
    chat_model: Optional[BaseChatModel] = None,
) -> TeamMemoryRAGOutput:
    """Convenience synchronous execution wrapper for RAG chain."""
    chain = build_rag_chain(
        db=db,
        organization_id=organization_id,
        scenario_id=scenario_id,
        top_k=top_k,
        scenario_type=scenario_type,
        embedding_provider=embedding_provider,
        chat_model=chat_model,
    )
    return chain.invoke(question)


async def arun_rag_chain(
    db: Session,
    question: str,
    organization_id: UUID,
    top_k: int = 5,
    scenario_id: Optional[UUID] = None,
    scenario_type: Optional[str] = None,
    embedding_provider: Optional[EmbeddingProvider] = None,
    chat_model: Optional[BaseChatModel] = None,
) -> TeamMemoryRAGOutput:
    """Convenience asynchronous execution wrapper for RAG chain."""
    chain = build_rag_chain(
        db=db,
        organization_id=organization_id,
        scenario_id=scenario_id,
        top_k=top_k,
        scenario_type=scenario_type,
        embedding_provider=embedding_provider,
        chat_model=chat_model,
    )
    return await chain.ainvoke(question)
