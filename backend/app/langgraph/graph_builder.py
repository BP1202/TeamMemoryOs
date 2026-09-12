"""
TeamMemoryOS LangGraph Graph Builder.

This module provides the graph compilation and assembly skeleton for the
TeamMemoryOS multi-agent workflow engine.
"""
from __future__ import annotations

from langgraph.graph import START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.langgraph.debug_node import debug_node
from app.langgraph.memory_node import memory_node
from app.langgraph.merge_node import merge_node
from app.langgraph.repository_node import repository_node
from app.langgraph.router_node import router_node
from app.langgraph.state import WorkflowState


def build_teammemory_graph() -> CompiledStateGraph:
    """Construct and compile the foundational TeamMemoryOS multi-agent workflow graph.

    Initializes a StateGraph with WorkflowState, registers the primary agent nodes
    (router, repository, memory, debug, merge), defines the initial entry point,
    and compiles the workflow.

    TODO (AI-006 Step 6.2+): Implement dynamic conditional edges based on router intent,
    parallel fan-out to repository/memory/debug nodes, and merge fan-in to synthesize
    the response.

    Returns:
        CompiledStateGraph: The compiled, runnable LangGraph state graph.
    """
    builder = StateGraph(WorkflowState)

    # Register foundational agent nodes
    builder.add_node("router", router_node)
    builder.add_node("repository", repository_node)
    builder.add_node("memory", memory_node)
    builder.add_node("debug", debug_node)
    builder.add_node("merge", merge_node)

    # Foundational entry point from START to router
    builder.add_edge(START, "router")

    # Compile and return executable graph
    return builder.compile()
