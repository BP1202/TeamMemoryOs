"""
TeamMemoryOS LangGraph Workflow Streaming Helpers.

This module provides SSE (Server-Sent Events) formatting generators and dictionary
payload builders for streaming multi-agent execution events to clients.
"""
from __future__ import annotations

import json
from typing import Any

from app.langgraph.state import WorkflowState


def stream_metadata(
    state: WorkflowState | None = None,
    organization_id: str | None = None,
    conversation_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an SSE metadata event payload for workflow execution start.

    Args:
        state: Optional current WorkflowState to extract metadata from.
        organization_id: Optional explicit organization ID.
        conversation_id: Optional explicit conversation ID.
        extra: Optional additional metadata fields.

    Returns:
        dict[str, Any]: SSE-formatted event dictionary.
    """
    payload: dict[str, Any] = {
        "organization_id": organization_id or (state.get("organization_id") if state else None),
        "conversation_id": conversation_id or (state.get("conversation_id") if state else None),
        "query": state.get("query") if state else None,
        "intent": state.get("intent") if state else None,
        "extra": extra or (state.get("metadata") if state else {}),
    }
    return {
        "event": "metadata",
        "data": payload,
    }


def stream_agent_event(
    agent: str,
    event_type: str,
    data: dict[str, Any] | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    """Build an SSE agent execution event payload.

    Args:
        agent: Identifier of the agent node (e.g. "router", "repository", "memory", "debug", "merge").
        event_type: Type of agent event (e.g. "started", "progress", "token", "completed", "error").
        data: Optional structured data payload produced by the agent.
        message: Optional human-readable status message.

    Returns:
        dict[str, Any]: SSE-formatted event dictionary.
    """
    payload: dict[str, Any] = {
        "agent": agent,
        "event_type": event_type,
        "message": message or f"Agent '{agent}' executed event '{event_type}'",
        "data": data or {},
    }
    return {
        "event": "agent_event",
        "data": payload,
    }


def stream_done(
    metadata: dict[str, Any] | None = None,
    final_answer: str | None = None,
    confidence: float | None = None,
) -> dict[str, Any]:
    """Build an SSE completion event payload.

    Args:
        metadata: Optional metadata dictionary summarizing execution.
        final_answer: Optional final synthesized response text.
        confidence: Optional final confidence score.

    Returns:
        dict[str, Any]: SSE-formatted event dictionary signaling completion.
    """
    payload: dict[str, Any] = {
        "status": "completed",
        "final_answer": final_answer,
        "confidence": confidence,
        "metadata": metadata or {},
    }
    return {
        "event": "done",
        "data": payload,
    }


def format_sse_event(event_dict: dict[str, Any]) -> str:
    """Format an event dictionary into standard SSE wire format string.

    Args:
        event_dict: Dictionary containing "event" and "data" keys.

    Returns:
        str: Serialized SSE string (e.g. `event: metadata\\ndata: {...}\\n\\n`).
    """
    event_name = event_dict.get("event", "message")
    data_content = event_dict.get("data", {})
    json_data = json.dumps(data_content, default=str)
    return f"event: {event_name}\ndata: {json_data}\n\n"
