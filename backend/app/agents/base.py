"""
Agent Framework Base — Milestone 7.1.

Defines:
* AgentCapability  — enum of what an agent can do.
* AgentStatus      — lifecycle state machine values.
* AgentContext     — per-execution, org-scoped execution context.
* AgentState       — mutable shared state passed between agents in a workflow.
* AgentResult      — structured, explainable output every agent must return.
* BaseAgent        — Protocol that every agent must satisfy.

Design goal: every component here is LangGraph-portable.
AgentContext  → maps to LangGraph State input dict.
AgentState    → maps to LangGraph State annotation.
AgentResult   → maps to node return value.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable
from uuid import UUID


# ---------------------------------------------------------------------------
# AgentCapability — what an agent exposes to the registry/router
# ---------------------------------------------------------------------------

class AgentCapability(str, enum.Enum):
    """Enumeration of first-class agent capabilities."""
    REPOSITORY_SEARCH = "repository_search"
    COMMIT_HISTORY = "commit_history"
    BRANCH_LOOKUP = "branch_lookup"
    FILE_HISTORY = "file_history"
    DEBUG_ANALYSIS = "debug_analysis"
    STACK_TRACE_PARSE = "stack_trace_parse"
    INCIDENT_RETRIEVAL = "incident_retrieval"
    GRAPHRAG_RETRIEVAL = "graphrag_retrieval"
    EXPLANATION_BUILD = "explanation_build"
    MEMORY_HANDOFF = "memory_handoff"
    WORKFLOW_PLAN = "workflow_plan"
    WORKFLOW_ROUTE = "workflow_route"


# ---------------------------------------------------------------------------
# AgentStatus — lifecycle state machine
# ---------------------------------------------------------------------------

class AgentStatus(str, enum.Enum):
    """Lifecycle status for an agent execution run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# ---------------------------------------------------------------------------
# AgentContext — per-execution, organisation-scoped context
# ---------------------------------------------------------------------------

@dataclass
class AgentContext:
    """Immutable execution context supplied to every agent run.

    LangGraph compatibility note:
        This maps to the *input* keys of a LangGraph State dict.
        When porting, unpack into: ``state["organization_id"]``, etc.

    Attributes:
        organization_id:  Tenant isolation — all DB queries must be scoped.
        user_id:          Authenticated user who triggered the workflow.
        question:         Raw question or task description.
        metadata:         Arbitrary extra context (e.g. repo_id, session_id).
    """
    organization_id: UUID
    user_id: UUID
    question: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# AgentState — shared mutable state for multi-agent workflows
# ---------------------------------------------------------------------------

@dataclass
class AgentState:
    """Shared mutable state threaded through a multi-agent workflow.

    Agents append to ``messages``, ``memory_hits``, ``citations``,
    ``graph_path``, and ``suggested_actions``.  ``intermediate_results``
    is a free-form store keyed by agent name for handoff data.

    LangGraph compatibility note:
        This becomes a TypedDict / Annotated state class when ported.
        Each list field uses ``operator.add`` (append reducer) annotation.
    """
    context: AgentContext
    messages: list[dict[str, Any]] = field(default_factory=list)
    memory_hits: list[dict[str, Any]] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    graph_path: list[dict[str, Any]] = field(default_factory=list)
    suggested_actions: list[str] = field(default_factory=list)
    intermediate_results: dict[str, Any] = field(default_factory=dict)
    participating_agents: list[str] = field(default_factory=list)
    confidence: float = 0.0
    final_answer: str = ""
    status: AgentStatus = AgentStatus.PENDING

    def record_agent(self, agent_name: str) -> None:
        """Track which agents have contributed to the current state."""
        if agent_name not in self.participating_agents:
            self.participating_agents.append(agent_name)

    def add_message(self, role: str, content: str, agent: str) -> None:
        """Append a message to the shared conversation history."""
        self.messages.append({"role": role, "content": content, "agent": agent})


# ---------------------------------------------------------------------------
# AgentResult — structured explainable output
# ---------------------------------------------------------------------------

@dataclass
class AgentResult:
    """Structured result returned by every agent execution.

    Attributes:
        agent_name:        Identifies which agent produced this result.
        status:            Outcome of the execution.
        answer:            Plain-text answer or empty string.
        citations:         List of memory citation dicts.
        graph_path:        List of entity-relationship path dicts.
        confidence:        Aggregate retrieval confidence [0.0, 1.0].
        suggested_actions: Next-step recommendations.
        participating_agents: All agents that contributed to the answer.
        metadata:          Free-form extra data (e.g. error details, debug info).
    """
    agent_name: str
    status: AgentStatus
    answer: str = ""
    citations: list[dict[str, Any]] = field(default_factory=list)
    graph_path: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    suggested_actions: list[str] = field(default_factory=list)
    participating_agents: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# BaseAgent — Protocol every agent must satisfy
# ---------------------------------------------------------------------------

@runtime_checkable
class BaseAgent(Protocol):
    """Protocol contract that every TeamMemoryOS agent must satisfy.

    Implementing class rules:
    1. ``name`` must be unique within the AgentRegistry.
    2. ``capabilities`` declares what the agent can do.
    3. ``run()`` must be organisation-scoped and never raise uncaught exceptions.
    4. ``run()`` must return an ``AgentResult`` with a populated ``agent_name``.
    """

    @property
    def name(self) -> str:
        """Unique agent identifier used in routing and state tracking."""
        ...

    @property
    def capabilities(self) -> list[AgentCapability]:
        """Capabilities this agent exposes to the router."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description of the agent's purpose."""
        ...

    def run(self, state: AgentState) -> AgentResult:
        """Execute the agent against the supplied state.

        Contract:
        - Must read ``state.context.organization_id`` and scope all queries.
        - Must append to ``state`` before returning (state is mutable).
        - Must call ``state.record_agent(self.name)``.
        - Must return an ``AgentResult`` even on internal failure.
        - Must never raise an uncaught exception to the caller.
        """
        ...
