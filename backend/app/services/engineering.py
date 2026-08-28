"""Engineering Conversation Engine service (Milestone 6.5).

Orchestrates the prompt router combining all Sprint 6 memory sources:
* GraphRAG retrieval (repository, PR, terminal, code, and general memories)
* Prompt routing by mode (debug, architecture, review, search, incident, auto)
* GraniteProvider through existing interface
* Explainable responses with citations, graph path, confidence, suggested actions
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy.orm import Session

from app.graph.explanation_builder import Citation, GraphPathStep, build_retrieval_explanation
from app.graph.hybrid_retriever import HybridRetriever
from app.memory.embedding_provider import StubEmbeddingProvider
from app.memory.generation_provider import get_generation_provider
from app.memory.prompt_builder import build_prompt
from app.memory.rag_context import _format_context
from app.schemas.engineering import (
    DebugRequest,
    EngineeringChatRequest,
    EngineeringResponse,
    ReviewRequest,
)
from app.schemas.retrieval import CitationRead, GraphPathStepRead


# ---------------------------------------------------------------------------
# Prompt templates per routing mode
# ---------------------------------------------------------------------------

_PROMPTS: dict[str, str] = {
    "debug": (
        "You are an expert debugging assistant for an engineering team. "
        "Analyse the error below and suggest fixes based on the team's recorded "
        "engineering history shown in the context. Be specific and actionable."
    ),
    "architecture": (
        "You are an expert software architect. Answer the question about system "
        "design and architecture using the team's recorded decisions in the context. "
        "Reference specific decisions where relevant."
    ),
    "review": (
        "You are a code reviewer. Review the provided pull request or diff using "
        "the team's historical PR decisions and patterns shown in the context. "
        "Identify risks and suggest improvements."
    ),
    "search": (
        "You are a codebase search assistant. Help the engineer find relevant code, "
        "files, or services based on the query and the indexed codebase context."
    ),
    "incident": (
        "You are an incident investigator. Analyse the described incident using the "
        "team's historical incidents, fixes, and decisions from the context. "
        "Identify root cause and suggest remediation steps."
    ),
    "auto": (
        "You are an AI engineering assistant for a software team. Answer the "
        "question using the team's organizational memory shown in the context. "
        "Be specific, cite sources, and suggest next actions where appropriate."
    ),
}

_SUGGESTED_ACTIONS: dict[str, list[str]] = {
    "debug": [
        "Search terminal error history for similar failures.",
        "Check repository commits that changed related files.",
        "Review PR history for recent changes to the affected component.",
    ],
    "architecture": [
        "Review related architectural decisions in organizational memory.",
        "Check entity relationships for the referenced components.",
        "Search repository history for prior implementation attempts.",
    ],
    "review": [
        "Run risk analysis on the pull request.",
        "Check historical PRs for similar patterns.",
        "Review related entity relationships in the knowledge graph.",
    ],
    "search": [
        "Index the repository to improve code search coverage.",
        "Refine query with specific file names or function names.",
        "Use hybrid retrieval for broader context.",
    ],
    "incident": [
        "Search terminal error history for related failures.",
        "Review repository commits during the incident window.",
        "Check entity relationships for affected services.",
    ],
    "auto": [
        "Use /engineering/debug for error analysis.",
        "Use /engineering/review for PR review.",
        "Refine query for more specific results.",
    ],
}


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def _detect_mode(question: str) -> str:
    """Automatically detect the appropriate routing mode from the question."""
    q = question.lower()
    if re.search(r"\b(error|exception|traceback|fail|crash|bug|broken|importerror|valueerror|typeerror|keyerror)\b", q):
        return "debug"
    if re.search(r"\b(architecture|design|pattern|structure|how does|why did)\b", q):
        return "architecture"
    if re.search(r"\b(pr|pull request|diff|review|merge|branch)\b", q):
        return "review"
    if re.search(r"\b(find|search|where is|show me|code|function|class|file)\b", q):
        return "search"
    if re.search(r"\b(incident|outage|down|slow|latency|sla|alert)\b", q):
        return "incident"
    return "auto"


def _serialize_citations(citations) -> list[CitationRead]:
    return [
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
        for c in citations
    ]


def _serialize_graph_path(graph_path) -> list[GraphPathStepRead]:
    return [
        GraphPathStepRead(
            source_entity_id=s.source_entity_id,
            source_entity_name=s.source_entity_name,
            relationship_type=s.relationship_type,
            target_entity_id=s.target_entity_id,
            target_entity_name=s.target_entity_name,
        )
        for s in graph_path
    ]


# ---------------------------------------------------------------------------
# Core engine
# ---------------------------------------------------------------------------

def run_engineering_chat(
    db: Session,
    request: EngineeringChatRequest,
) -> EngineeringResponse:
    """Orchestrate the full engineering conversation pipeline."""
    mode = request.mode if request.mode != "auto" else _detect_mode(request.question)

    # 1. Retrieve context via HybridRetriever
    retriever = HybridRetriever(
        db=db,
        organization_id=request.organization_id,
        embedding_provider=StubEmbeddingProvider(),
        top_k=request.top_k,
    )
    hybrid_results = retriever.retrieve(request.question)
    retrieved_entries = [r.memory for r in hybrid_results]

    # 2. Build explanation
    explanation = build_retrieval_explanation(
        question=request.question,
        hybrid_results=hybrid_results,
        db=db,
        organization_id=request.organization_id,
        retrieval_mode="hybrid",
    )

    # 3. Build prompt with mode-specific system context
    system_preamble = _PROMPTS.get(mode, _PROMPTS["auto"])
    context_text = _format_context(request.question, retrieved_entries)
    full_question = f"{request.question}"

    prompt = build_prompt(
        question=full_question,
        context_text=f"{system_preamble}\n\n{context_text}",
        entries=retrieved_entries,
    )

    # 4. Generate response (safe fallback)
    gen_provider = get_generation_provider()
    try:
        answer = gen_provider.generate(prompt)
    except Exception as exc:
        answer = (
            f"Unable to generate response at this time. "
            f"(Provider error: {type(exc).__name__})"
        )

    # 5. Build suggested actions
    suggested_actions = _SUGGESTED_ACTIONS.get(mode, _SUGGESTED_ACTIONS["auto"])

    return EngineeringResponse(
        answer=answer,
        citations=_serialize_citations(explanation.citations),
        graph_path=_serialize_graph_path(explanation.graph_path),
        confidence=explanation.confidence,
        retrieval_mode="hybrid",
        suggested_actions=list(suggested_actions),
        provider_used=gen_provider.provider_name,
    )


def run_engineering_debug(
    db: Session,
    request: DebugRequest,
) -> EngineeringResponse:
    """Debug mode: enrich query with stack trace, route as debug."""
    query_parts = [request.error_message]
    if request.stack_trace:
        query_parts.append(request.stack_trace[:1000])
    if request.command:
        query_parts.append(f"Command: {request.command}")

    chat_request = EngineeringChatRequest(
        organization_id=request.organization_id,
        question="\n".join(query_parts),
        top_k=request.top_k,
        mode="debug",
    )
    return run_engineering_chat(db, chat_request)


def run_engineering_review(
    db: Session,
    request: ReviewRequest,
) -> EngineeringResponse:
    """Review mode: enrich query with PR content."""
    question_parts = ["Please review the following changes:"]
    if request.title:
        question_parts.append(f"Title: {request.title}")
    if request.diff_text:
        question_parts.append(f"Diff (excerpt):\n{request.diff_text[:2000]}")

    chat_request = EngineeringChatRequest(
        organization_id=request.organization_id,
        question="\n".join(question_parts),
        top_k=request.top_k,
        mode="review",
    )
    return run_engineering_chat(db, chat_request)
