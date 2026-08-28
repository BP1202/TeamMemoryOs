"""
Debug Agent — Milestone 7.3.

Autonomous agent responsible for:
* Parsing stack traces and terminal sessions.
* Retrieving similar historical incidents from organisational memory.
* Explaining likely root cause deterministically + via Granite reasoning.
* Suggesting engineering actions.

Reuses:
* Terminal service error classifiers (Sprint 6).
* HybridRetriever (Sprint 6 GraphRAG pipeline).
* ExplanationBuilder (Sprint 6).

LangGraph compatibility: ``run()`` maps to a LangGraph node function.
"""
from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.agents.base import (
    AgentCapability,
    AgentResult,
    AgentState,
    AgentStatus,
)
from app.graph.explanation_builder import build_retrieval_explanation
from app.graph.hybrid_retriever import HybridRetriever
from app.memory.embedding_provider import StubEmbeddingProvider
from app.memory.generation_provider import get_generation_provider
from app.memory.prompt_builder import build_prompt
from app.memory.rag_context import _format_context


# ---------------------------------------------------------------------------
# Stack trace / error parsing
# ---------------------------------------------------------------------------

_TRACEBACK_RE = re.compile(r"Traceback \(most recent call last\)", re.IGNORECASE)
_EXCEPTION_LINE_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)*):\s+(.+)$", re.MULTILINE)
_FILE_LINE_RE = re.compile(r'File "([^"]+)", line (\d+), in (.+)', re.MULTILINE)


def parse_stack_trace(text: str) -> dict[str, Any]:
    """Extract structured information from a Python or generic stack trace.

    Returns:
        {
            "has_traceback": bool,
            "exception_type": str | None,
            "exception_message": str | None,
            "frames": [{"file": str, "line": int, "context": str}],
            "raw_excerpt": str  — first 500 chars of text
        }
    """
    has_tb = bool(_TRACEBACK_RE.search(text))
    frames = [
        {"file": m.group(1), "line": int(m.group(2)), "context": m.group(3)}
        for m in _FILE_LINE_RE.finditer(text)
    ]

    exc_type: str | None = None
    exc_msg: str | None = None
    for m in _EXCEPTION_LINE_RE.finditer(text):
        exc_type = m.group(1)
        exc_msg = m.group(2)[:300]
        break  # first match is usually the root cause

    return {
        "has_traceback": has_tb,
        "exception_type": exc_type,
        "exception_message": exc_msg,
        "frames": frames[-5:],  # last 5 frames (innermost)
        "raw_excerpt": text[:500],
    }


def _build_debug_query(
    error_message: str,
    stack_trace: str | None,
    parsed: dict[str, Any],
) -> str:
    """Construct an enriched search query from error information."""
    parts = [error_message[:300]]
    if parsed["exception_type"]:
        parts.append(parsed["exception_type"])
    if parsed["exception_message"]:
        parts.append(parsed["exception_message"])
    if stack_trace:
        parts.append(stack_trace[:500])
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Debug Agent
# ---------------------------------------------------------------------------

class DebugAgent:
    """Incident analysis and root-cause explanation agent."""

    @property
    def name(self) -> str:
        return "debug_agent"

    @property
    def description(self) -> str:
        return (
            "Parses stack traces and terminal sessions, retrieves similar historical "
            "incidents from organisational memory, and explains root cause with "
            "engineering suggestions."
        )

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [
            AgentCapability.DEBUG_ANALYSIS,
            AgentCapability.STACK_TRACE_PARSE,
            AgentCapability.INCIDENT_RETRIEVAL,
            AgentCapability.GRAPHRAG_RETRIEVAL,
            AgentCapability.EXPLANATION_BUILD,
        ]

    def run(self, state: AgentState) -> AgentResult:
        """Execute debug analysis against the current state.

        Reads from state.context:
            question, organization_id, metadata.get("db"),
            metadata.get("stack_trace"), metadata.get("command")
        """
        state.record_agent(self.name)
        db: Session | None = state.context.metadata.get("db")
        if db is None:
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                answer="No database session provided to DebugAgent.",
                participating_agents=[self.name],
                metadata={"error": "missing_db"},
            )

        org_id: UUID = state.context.organization_id
        error_message: str = state.context.question
        stack_trace: str | None = state.context.metadata.get("stack_trace")
        command: str | None = state.context.metadata.get("command")

        try:
            # 1. Parse stack trace
            parsed = parse_stack_trace(stack_trace or error_message)

            # 2. Build enriched search query
            search_query = _build_debug_query(error_message, stack_trace, parsed)

            # 3. GraphRAG retrieval for historical incidents
            retriever = HybridRetriever(
                db=db,
                organization_id=org_id,
                embedding_provider=StubEmbeddingProvider(),
                top_k=5,
            )
            hybrid_results = retriever.retrieve(search_query)
            retrieved_entries = [r.memory for r in hybrid_results]

            # 4. Build explanation
            explanation = build_retrieval_explanation(
                question=search_query,
                hybrid_results=hybrid_results,
                db=db,
                organization_id=org_id,
                retrieval_mode="hybrid",
            )

            # 5. Build prompt for Granite reasoning
            debug_system = (
                "You are an expert debugging assistant. "
                "Analyse the error and suggest root causes and fixes based on "
                "the team's recorded engineering history shown in the context. "
                "Be specific and actionable."
            )
            context_text = _format_context(search_query, retrieved_entries)
            prompt = build_prompt(
                question=f"Debug this error:\n{error_message}"
                + (f"\n\nStack trace:\n{stack_trace[:1000]}" if stack_trace else "")
                + (f"\n\nCommand: {command}" if command else ""),
                context_text=f"{debug_system}\n\n{context_text}",
                entries=retrieved_entries,
            )

            # 6. Generate answer (safe failure)
            gen_provider = get_generation_provider()
            try:
                answer = gen_provider.generate(prompt)
            except Exception as exc:
                answer = (
                    f"Debug analysis: {parsed.get('exception_type', 'UnknownError')}: "
                    f"{parsed.get('exception_message', error_message[:200])}. "
                    f"Found {explanation.result_count} similar historical incidents. "
                    f"(Generation provider error: {type(exc).__name__})"
                )

            # 7. Serialize
            citations = _serialize_citations(explanation.citations)
            graph_path = _serialize_graph_path(explanation.graph_path)

            suggested = [
                "Search terminal error history for similar failures.",
                "Check repository commits that changed related files.",
                "Review historical incidents for this error type.",
            ]
            if parsed["exception_type"]:
                suggested.insert(0, f"Search for '{parsed['exception_type']}' in organizational memory.")
            if command:
                suggested.append(f"Verify command: {command[:80]}")

            # 8. Update shared state
            state.citations.extend(citations)
            state.graph_path.extend(graph_path)
            state.memory_hits.extend(
                [{"memory_id": str(r.memory.id), "score": r.score} for r in hybrid_results]
            )
            state.confidence = max(state.confidence, explanation.confidence)
            state.suggested_actions.extend(suggested)
            state.intermediate_results["debug_agent"] = {
                "parsed_trace": parsed,
                "incidents_found": explanation.result_count,
            }
            state.add_message(role="agent", content=answer, agent=self.name)
            state.status = AgentStatus.COMPLETED

            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                answer=answer,
                citations=citations,
                graph_path=graph_path,
                confidence=explanation.confidence,
                suggested_actions=suggested,
                participating_agents=[self.name],
                metadata={
                    "parsed_trace": parsed,
                    "incidents_found": explanation.result_count,
                },
            )

        except Exception as exc:
            error_msg = f"DebugAgent failed: {type(exc).__name__}: {exc}"
            state.add_message(role="error", content=error_msg, agent=self.name)
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                answer=error_msg,
                participating_agents=[self.name],
                metadata={"error": str(exc)},
            )


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _serialize_citations(citations) -> list[dict[str, Any]]:
    return [
        {
            "memory_id": str(c.memory_id),
            "memory_title": c.memory_title,
            "memory_type": c.memory_type,
            "retrieval_reason": c.retrieval_reason,
            "semantic_score": c.semantic_score,
            "graph_score": c.graph_score,
            "link_score": c.link_score,
            "final_score": c.final_score,
            "graph_distance": c.graph_distance,
            "matched_entities": c.matched_entities,
            "rank": c.rank,
        }
        for c in citations
    ]


def _serialize_graph_path(graph_path) -> list[dict[str, Any]]:
    return [
        {
            "source_entity_id": str(s.source_entity_id),
            "source_entity_name": s.source_entity_name,
            "relationship_type": s.relationship_type,
            "target_entity_id": str(s.target_entity_id),
            "target_entity_name": s.target_entity_name,
        }
        for s in graph_path
    ]
