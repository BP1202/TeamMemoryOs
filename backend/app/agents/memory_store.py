"""
Shared Memory Collaboration — Milestone 7.5.

Components:
* AgentMemoryStore  — in-process retrieval cache shared across agents in
                      a single workflow execution.
* ConversationHistory  — persists multi-agent conversation turn history.
* MultiAgentExplanationBuilder  — assembles the final explainable response
                                  combining contributions from all agents.
* memory_handoff()  — transfers enriched context from one agent to the next.

Design:
* The memory store is request-scoped (no global mutable state).
* Conversation history is stored as a list of dicts (portable to Redis later).
* The explanation builder extends ExplanationBuilder from Sprint 6.

LangGraph compatibility note:
    AgentMemoryStore maps to a LangGraph tool with a shared retriever.
    ConversationHistory maps to a LangGraph checkpointer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.agents.base import AgentResult, AgentState, AgentStatus
from app.graph.explanation_builder import build_retrieval_explanation
from app.graph.hybrid_retriever import HybridRetriever
from app.memory.embedding_provider import StubEmbeddingProvider


# ---------------------------------------------------------------------------
# AgentMemoryStore — shared retrieval cache
# ---------------------------------------------------------------------------

class AgentMemoryStore:
    """Request-scoped memory cache shared across all agents in a workflow.

    Prevents duplicate GraphRAG calls when multiple agents answer related
    questions within the same workflow execution.

    LangGraph compatibility:
        Wraps as a LangGraph ToolNode that checks the cache before calling
        the retriever.
    """

    def __init__(
        self,
        db: Session,
        organization_id: UUID,
        top_k: int = 5,
    ) -> None:
        self._db = db
        self._organization_id = organization_id
        self._top_k = top_k
        self._cache: dict[str, list] = {}  # question → hybrid_results

    def retrieve(self, question: str) -> list:
        """Return cached or fresh GraphRAG results for *question*."""
        cache_key = question.strip().lower()[:200]
        if cache_key in self._cache:
            return self._cache[cache_key]

        retriever = HybridRetriever(
            db=self._db,
            organization_id=self._organization_id,
            embedding_provider=StubEmbeddingProvider(),
            top_k=self._top_k,
        )
        results = retriever.retrieve(question)
        self._cache[cache_key] = results
        return results

    def warm(self, questions: list[str]) -> None:
        """Pre-populate the cache for a batch of questions."""
        for q in questions:
            self.retrieve(q)

    def cache_size(self) -> int:
        return len(self._cache)


# ---------------------------------------------------------------------------
# ConversationHistory — persists multi-agent turn history
# ---------------------------------------------------------------------------

@dataclass
class ConversationTurn:
    """One message turn in the multi-agent conversation."""
    agent: str
    role: str   # "user" | "agent" | "system" | "error"
    content: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ConversationHistory:
    """In-memory multi-agent conversation history.

    Thread-safe for single-request use; can be serialised to/from JSON
    for persistence in Redis or the database in a later sprint.

    LangGraph compatibility:
        Serialise ``to_dict()`` into the LangGraph checkpointer.
    """

    def __init__(self) -> None:
        self._turns: list[ConversationTurn] = []

    def add(self, agent: str, role: str, content: str) -> None:
        self._turns.append(ConversationTurn(agent=agent, role=role, content=content))

    def turns(self) -> list[ConversationTurn]:
        return list(self._turns)

    def to_dict(self) -> list[dict[str, str]]:
        """Serialise to a list of plain dicts (JSON-serialisable)."""
        return [
            {
                "agent": t.agent,
                "role": t.role,
                "content": t.content,
                "timestamp": t.timestamp,
            }
            for t in self._turns
        ]

    def agent_messages(self, agent_name: str) -> list[ConversationTurn]:
        """Return only turns contributed by *agent_name*."""
        return [t for t in self._turns if t.agent == agent_name]

    def __len__(self) -> int:
        return len(self._turns)


# ---------------------------------------------------------------------------
# memory_handoff — transfer enriched context between agents
# ---------------------------------------------------------------------------

def memory_handoff(
    source_result: AgentResult,
    target_state: AgentState,
    handoff_key: str,
) -> None:
    """Transfer the memory hits and citations from a completed agent result
    into the shared state for the next agent to build upon.

    Args:
        source_result:  AgentResult from the completed upstream agent.
        target_state:   Shared AgentState passed to the next agent.
        handoff_key:    Key under which to store the source result's data
                        in ``target_state.intermediate_results``.

    LangGraph compatibility:
        This maps to a LangGraph ``add_messages`` reducer between two nodes.
    """
    # Merge citations (avoid duplicates by memory_id)
    existing_ids = {c.get("memory_id") for c in target_state.citations}
    for c in source_result.citations:
        if c.get("memory_id") not in existing_ids:
            target_state.citations.append(c)
            existing_ids.add(c.get("memory_id"))

    # Merge graph path (avoid duplicates)
    existing_paths = {
        (p.get("source_entity_id"), p.get("target_entity_id"))
        for p in target_state.graph_path
    }
    for p in source_result.graph_path:
        key = (p.get("source_entity_id"), p.get("target_entity_id"))
        if key not in existing_paths:
            target_state.graph_path.append(p)
            existing_paths.add(key)

    # Merge suggested actions
    existing_actions = set(target_state.suggested_actions)
    for action in source_result.suggested_actions:
        if action not in existing_actions:
            target_state.suggested_actions.append(action)
            existing_actions.add(action)

    # Update confidence (take maximum)
    target_state.confidence = max(target_state.confidence, source_result.confidence)

    # Store intermediate for downstream access
    target_state.intermediate_results[handoff_key] = {
        "agent": source_result.agent_name,
        "answer": source_result.answer,
        "metadata": source_result.metadata,
    }


# ---------------------------------------------------------------------------
# MultiAgentExplanationBuilder
# ---------------------------------------------------------------------------

@dataclass
class MultiAgentExplanation:
    """Combined explanation from all agents in a workflow.

    This is the response structure for all Sprint 7 multi-agent endpoints.
    Fields match the sprint specification exactly.
    """
    answer: str
    participating_agents: list[str]
    citations: list[dict[str, Any]]
    graph_path: list[dict[str, Any]]
    confidence: float
    suggested_actions: list[str]
    conversation_history: list[dict[str, str]]
    retrieval_mode: str = "hybrid"
    status: str = "completed"


class MultiAgentExplanationBuilder:
    """Assembles the final explainable multi-agent response.

    Combines contributions from all agents in the shared state,
    deduplicates citations, merges graph paths, and builds a
    structured explanation that includes all required fields from
    the Sprint 7 specification.
    """

    def build(
        self,
        state: AgentState,
        conversation: ConversationHistory | None = None,
    ) -> MultiAgentExplanation:
        """Build the final response from shared agent state.

        Args:
            state:        Final AgentState after all agents ran.
            conversation: Optional ConversationHistory for history inclusion.

        Returns:
            MultiAgentExplanation with all sprint-required fields.
        """
        # Deduplicate citations
        seen_ids: set[str] = set()
        unique_citations: list[dict] = []
        for c in state.citations:
            mid = c.get("memory_id", "")
            if mid not in seen_ids:
                seen_ids.add(mid)
                unique_citations.append(c)

        # Deduplicate graph path
        seen_paths: set[tuple] = set()
        unique_path: list[dict] = []
        for p in state.graph_path:
            key = (p.get("source_entity_id", ""), p.get("target_entity_id", ""))
            if key not in seen_paths:
                seen_paths.add(key)
                unique_path.append(p)

        # Deduplicate suggested actions (preserve order)
        unique_actions: list[str] = list(dict.fromkeys(state.suggested_actions))

        # Assemble answer from agent messages
        agent_messages = [
            m["content"]
            for m in state.messages
            if m.get("role") == "agent" and m.get("content")
        ]
        answer = (
            state.final_answer
            or "\n\n---\n\n".join(agent_messages)
            or "No answer generated."
        )

        history = conversation.to_dict() if conversation else [
            {"agent": m.get("agent", ""), "role": m.get("role", ""), "content": m.get("content", "")}
            for m in state.messages
        ]

        return MultiAgentExplanation(
            answer=answer,
            participating_agents=state.participating_agents,
            citations=unique_citations,
            graph_path=unique_path,
            confidence=state.confidence,
            suggested_actions=unique_actions,
            conversation_history=history,
            retrieval_mode="hybrid",
            status=state.status.value,
        )
