"""
TeamMemoryOS LangGraph Multi-Agent Workflow Engine Foundation.

Exports core state structures, helper functions, and graph builder:
- State & Helpers: WorkflowState, create_initial_state, append_trace, update_confidence, add_citation, set_final_answer
- Graph Builder: build_teammemory_graph
- Node Placeholders: router_node, repository_node, memory_node, debug_node, merge_node
- Streaming: stream_metadata, stream_agent_event, stream_done, format_sse_event
"""
from app.langgraph.debug_node import debug_node
from app.langgraph.graph_builder import build_teammemory_graph
from app.langgraph.memory_node import memory_node
from app.langgraph.merge_node import merge_node
from app.langgraph.repository_node import repository_node
from app.langgraph.router_node import router_node
from app.langgraph.state import (
    WorkflowState,
    add_citation,
    append_trace,
    create_initial_state,
    set_final_answer,
    update_confidence,
)
from app.langgraph.streaming import (
    format_sse_event,
    stream_agent_event,
    stream_done,
    stream_metadata,
)

__all__ = [
    "WorkflowState",
    "create_initial_state",
    "append_trace",
    "update_confidence",
    "add_citation",
    "set_final_answer",
    "build_teammemory_graph",
    "router_node",
    "repository_node",
    "memory_node",
    "debug_node",
    "merge_node",
    "stream_metadata",
    "stream_agent_event",
    "stream_done",
    "format_sse_event",
]
