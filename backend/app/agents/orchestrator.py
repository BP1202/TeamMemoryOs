"""
Workflow Orchestrator — Milestone 7.4.

Implements an agent workflow engine compatible with future LangGraph integration.

Components:
* WorkflowPlanner   — decides which agents are needed based on the question.
* WorkflowRouter    — resolves agent instances from the registry.
* WorkflowExecutor  — runs sequential or conditional agent pipelines.
* ToolInvocationPipeline — wraps a single agent run as a tool invocation.

Architecture is designed for LangGraph portability:
* WorkflowPlanner.plan() → LangGraph conditional edge + node selector.
* WorkflowExecutor.run_sequential() → LangGraph StateGraph with linear edges.
* WorkflowExecutor.run_conditional() → LangGraph conditional routing graph.
* AgentState is the shared TypedDict-equivalent state.

No LangGraph runtime dependency is introduced in this milestone.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.agents.base import (
    AgentCapability,
    AgentContext,
    AgentResult,
    AgentState,
    AgentStatus,
)
from app.agents.registry import AgentRegistry


# ---------------------------------------------------------------------------
# WorkflowPlan — output of the planner
# ---------------------------------------------------------------------------

@dataclass
class WorkflowPlan:
    """A resolved plan describing which agents will execute and in what order.

    LangGraph compatibility note:
        ``steps`` maps to a list of (node_name, condition) pairs in a
        StateGraph.  Extend with ``condition_fn`` per step for full
        conditional edge support.
    """
    steps: list[str]             # agent names in execution order
    mode: str                    # "sequential" | "conditional"
    rationale: str               # human-readable explanation of the plan


# ---------------------------------------------------------------------------
# WorkflowPlanner — decides what to run
# ---------------------------------------------------------------------------

class WorkflowPlanner:
    """Determine which agents should execute for a given question.

    Uses lightweight keyword routing — deterministic, no LLM.

    LangGraph compatibility:
        Replace ``plan()`` with a LangGraph conditional edge that reads
        the same question from state and returns node names.
    """

    def plan(self, question: str, context_metadata: dict[str, Any] | None = None) -> WorkflowPlan:
        """Produce a WorkflowPlan from the natural-language *question*."""
        q = question.lower()
        context_metadata = context_metadata or {}
        steps: list[str] = []
        reasons: list[str] = []

        # Repository-related patterns
        if re.search(
            r"\b(commit|branch|repository|repo|git|file history|merge|diff|push|tag)\b", q
        ):
            steps.append("repository_agent")
            reasons.append("repository/commit query detected")

        # Debug-related patterns
        if re.search(
            r"\b(error|exception|traceback|fail|crash|bug|broken|importerror|valueerror|"
            r"typeerror|keyerror|segfault|oom|incident|outage|down)\b", q
        ):
            steps.append("debug_agent")
            reasons.append("error/debug query detected")

        # Force both agents for complex questions
        if re.search(r"\b(and|also|plus|additionally|both)\b", q) and len(steps) == 1:
            opposite = "debug_agent" if steps[0] == "repository_agent" else "repository_agent"
            steps.append(opposite)
            reasons.append("compound question — adding complementary agent")

        # Default: run both agents when question is ambiguous
        if not steps:
            steps = ["debug_agent", "repository_agent"]
            reasons.append("ambiguous question — running full pipeline")

        # Override: explicit repo_id in context → always include repository agent
        if context_metadata.get("repo_id") and "repository_agent" not in steps:
            steps.insert(0, "repository_agent")
            reasons.append("repo_id context provided")

        mode = "sequential"
        return WorkflowPlan(
            steps=steps,
            mode=mode,
            rationale="; ".join(reasons),
        )


# ---------------------------------------------------------------------------
# WorkflowRouter — resolves agent instances from registry
# ---------------------------------------------------------------------------

class WorkflowRouter:
    """Resolve agent names from a plan into concrete agent instances.

    LangGraph compatibility:
        The router maps to the graph's node registry — each agent name
        corresponds to a node registered with ``graph.add_node()``.
    """

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    def resolve(self, plan: WorkflowPlan) -> list[Any]:
        """Return ordered list of agent instances for the plan.

        Agents not found in the registry are silently skipped.
        """
        resolved = []
        for name in plan.steps:
            agent = self._registry.get(name)
            if agent is not None:
                resolved.append(agent)
        return resolved

    def route_by_capability(
        self, capabilities: list[AgentCapability]
    ) -> list[Any]:
        """Select agents from the registry by capability requirements."""
        return self._registry.route(capabilities)


# ---------------------------------------------------------------------------
# ToolInvocationPipeline — wraps a single agent as a tool call
# ---------------------------------------------------------------------------

@dataclass
class ToolInvocationResult:
    """Result of a single tool invocation in the pipeline."""
    tool_name: str
    agent_name: str
    success: bool
    result: AgentResult | None = None
    error: str | None = None


class ToolInvocationPipeline:
    """Wraps agent execution as a named tool invocation.

    LangGraph compatibility:
        Each ToolInvocationPipeline corresponds to a LangGraph ToolNode.
    """

    def invoke(self, agent: Any, state: AgentState) -> ToolInvocationResult:
        """Run *agent* and return a structured ToolInvocationResult."""
        tool_name = f"tool:{agent.name}"
        try:
            result = agent.run(state)
            return ToolInvocationResult(
                tool_name=tool_name,
                agent_name=agent.name,
                success=result.status == AgentStatus.COMPLETED,
                result=result,
            )
        except Exception as exc:
            return ToolInvocationResult(
                tool_name=tool_name,
                agent_name=agent.name,
                success=False,
                error=f"{type(exc).__name__}: {exc}",
            )


# ---------------------------------------------------------------------------
# WorkflowExecutor — runs the pipeline
# ---------------------------------------------------------------------------

class WorkflowExecutor:
    """Execute agent workflows using sequential or conditional strategies.

    LangGraph compatibility:
        ``run_sequential()`` → StateGraph with linear edges.
        ``run_conditional()`` → StateGraph with a conditional entry edge.
    """

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry
        self._router = WorkflowRouter(registry)
        self._tool_pipeline = ToolInvocationPipeline()

    def run_sequential(
        self,
        context: AgentContext,
        agent_names: list[str] | None = None,
        plan: WorkflowPlan | None = None,
    ) -> AgentState:
        """Execute agents sequentially, sharing state between steps.

        Args:
            context:     Execution context (org-scoped).
            agent_names: Explicit ordered list of agent names.  If None,
                         *plan* must be supplied.
            plan:        WorkflowPlan from the planner.

        Returns:
            Final ``AgentState`` after all agents have run.
        """
        if agent_names is None and plan is not None:
            agent_names = plan.steps
        elif agent_names is None:
            agent_names = []

        state = AgentState(context=context)
        state.status = AgentStatus.RUNNING

        agents = self._router.resolve(
            WorkflowPlan(steps=agent_names, mode="sequential", rationale="")
        )

        for agent in agents:
            invocation = self._tool_pipeline.invoke(agent, state)
            if not invocation.success:
                # Continue on individual agent failure — resilient pipeline
                state.add_message(
                    role="error",
                    content=invocation.error or "Unknown error",
                    agent=agent.name,
                )

        # Consolidate final state
        if all(
            msg.get("role") == "error"
            for msg in state.messages
            if msg.get("agent") != "system"
        ):
            state.status = AgentStatus.FAILED
        else:
            state.status = AgentStatus.COMPLETED

        return state

    def run_conditional(
        self,
        context: AgentContext,
    ) -> AgentState:
        """Use the WorkflowPlanner to determine and execute agents.

        Args:
            context: Execution context.  The planner reads ``context.question``
                     and ``context.metadata``.

        Returns:
            Final ``AgentState`` after conditional pipeline execution.
        """
        planner = WorkflowPlanner()
        plan = planner.plan(context.question, context.metadata)
        return self.run_sequential(context=context, plan=plan)

    def build_final_response(self, state: AgentState) -> dict[str, Any]:
        """Assemble the final multi-agent response from the shared state.

        Returns a dict matching the AgentWorkflowResponse schema.
        """
        # Deduplicate citations by memory_id
        seen_cid: set[str] = set()
        unique_citations: list[dict] = []
        for c in state.citations:
            mid = c.get("memory_id", "")
            if mid not in seen_cid:
                seen_cid.add(mid)
                unique_citations.append(c)

        # Aggregate answer from agent messages
        agent_messages = [
            m["content"] for m in state.messages
            if m.get("role") == "agent" and m.get("content")
        ]
        final_answer = (
            state.final_answer
            or "\n\n---\n\n".join(agent_messages)
            or "No answer generated."
        )

        return {
            "answer": final_answer,
            "participating_agents": state.participating_agents,
            "citations": unique_citations,
            "graph_path": state.graph_path,
            "confidence": state.confidence,
            "suggested_actions": list(dict.fromkeys(state.suggested_actions)),  # dedup order-preserving
            "status": state.status.value,
        }
