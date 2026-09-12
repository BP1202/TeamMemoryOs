"""
TeamMemoryOS LangGraph Workflow State Definition and State Helper Functions.

This module provides the strongly typed WorkflowState TypedDict and immutable
helper functions for managing multi-agent workflow state transitions.
"""
from __future__ import annotations

import copy
from typing import Any, TypedDict


class WorkflowState(TypedDict):
    """Strongly typed state dictionary for LangGraph workflow execution.

    Attributes:
        query: The incoming user query or instruction.
        organization_id: UUID of the organization/tenant context.
        repository_path: Optional relative/absolute path of target repository.
        conversation_id: Optional conversation ID for multi-turn thread tracking.
        intent: Classified intent (e.g. engineering_chat, incident_investigation, repo_health).
        retrieved_memories: List of retrieved engineering memory snippets and metadata.
        repository_context: List of retrieved repository chunks / AST structures.
        incident_context: List of retrieved incident / root cause contexts.
        repository_health: Health metrics and repository analytics dictionary.
        citations: List of source citations gathered across workflow nodes.
        agent_trace: Chronological audit trail of agent node executions and reasoning steps.
        confidence: Aggregated confidence score of workflow reasoning (0.0 to 1.0).
        final_answer: Synthesized final output response for the user.
        metadata: Arbitrary workflow metadata and execution parameters.
    """

    query: str
    organization_id: str
    repository_path: str | None
    conversation_id: str | None
    intent: str | None
    retrieved_memories: list[dict[str, Any]]
    repository_context: list[dict[str, Any]]
    incident_context: list[dict[str, Any]]
    repository_health: dict[str, Any] | None
    citations: list[dict[str, Any]]
    agent_trace: list[dict[str, Any]]
    confidence: float
    final_answer: str | None
    metadata: dict[str, Any]


def create_initial_state(
    query: str,
    organization_id: str,
    repository_path: str | None = None,
    conversation_id: str | None = None,
    intent: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> WorkflowState:
    """Create a new WorkflowState with sanitized default values.

    Args:
        query: The user query to be processed by the workflow.
        organization_id: Tenant / organization UUID.
        repository_path: Optional repository path context.
        conversation_id: Optional conversation thread ID.
        intent: Optional initial intent classification.
        metadata: Optional dictionary of additional execution metadata.

    Returns:
        WorkflowState: A initialized workflow state dictionary.
    """
    return WorkflowState(
        query=query,
        organization_id=organization_id,
        repository_path=repository_path,
        conversation_id=conversation_id,
        intent=intent,
        retrieved_memories=[],
        repository_context=[],
        incident_context=[],
        repository_health=None,
        citations=[],
        agent_trace=[],
        confidence=0.0,
        final_answer=None,
        metadata=dict(metadata) if metadata else {},
    )


def append_trace(
    state: WorkflowState,
    agent: str,
    action: str,
    details: dict[str, Any] | None = None,
) -> WorkflowState:
    """Append an execution step to the agent trace in an immutable-friendly manner.

    Args:
        state: Current WorkflowState.
        agent: Identifier/name of the agent or node executing the action.
        action: Summary of action performed (e.g. "retrieve_memories", "classify_intent").
        details: Optional supplementary data or reasoning details.

    Returns:
        WorkflowState: Updated state copy with the new trace entry appended.
    """
    new_state = copy.deepcopy(state)
    trace_entry = {
        "agent": agent,
        "action": action,
        "details": details or {},
    }
    new_state["agent_trace"].append(trace_entry)
    return new_state


def update_confidence(state: WorkflowState, confidence: float) -> WorkflowState:
    """Update the aggregated confidence score in an immutable-friendly manner.

    Clamps the confidence value to the interval [0.0, 1.0].

    Args:
        state: Current WorkflowState.
        confidence: New confidence score.

    Returns:
        WorkflowState: Updated state copy with clamped confidence.
    """
    new_state = copy.deepcopy(state)
    clamped_confidence = max(0.0, min(1.0, float(confidence)))
    new_state["confidence"] = round(clamped_confidence, 4)
    return new_state


def add_citation(
    state: WorkflowState,
    citation: dict[str, Any],
) -> WorkflowState:
    """Add a citation to the citations list in an immutable-friendly manner.

    Args:
        state: Current WorkflowState.
        citation: Citation dictionary containing source details (e.g. file, chunk, score).

    Returns:
        WorkflowState: Updated state copy containing the appended citation.
    """
    new_state = copy.deepcopy(state)
    new_state["citations"].append(dict(citation))
    return new_state


def set_final_answer(
    state: WorkflowState,
    answer: str,
    confidence: float | None = None,
) -> WorkflowState:
    """Set the final synthesized answer on the state in an immutable-friendly manner.

    Args:
        state: Current WorkflowState.
        answer: Synthesized final answer string.
        confidence: Optional confidence score to update simultaneously.

    Returns:
        WorkflowState: Updated state copy with the final answer set.
    """
    new_state = copy.deepcopy(state)
    new_state["final_answer"] = answer
    if confidence is not None:
        clamped_confidence = max(0.0, min(1.0, float(confidence)))
        new_state["confidence"] = round(clamped_confidence, 4)
    return new_state
