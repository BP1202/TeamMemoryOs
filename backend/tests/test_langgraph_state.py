"""
Unit tests for TeamMemoryOS LangGraph Workflow State Foundation (AI-006 Step 6.1).

Tests:
1. Initial state creation and default values.
2. Trace append and immutability.
3. Citation append and immutability.
4. Confidence update, bounding, and immutability.
5. Final answer setting and optional confidence update.
6. Graph builder returning compiled graph with registered nodes.
7. Node placeholder invocations.
8. Streaming SSE helpers.
"""
from __future__ import annotations

import json
from uuid import uuid4

import pytest

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


class TestLangGraphWorkflowState:
    """Test suite for WorkflowState and state helper functions."""

    def test_create_initial_state_defaults(self):
        """Test initial state creation with default values."""
        org_id = str(uuid4())
        state = create_initial_state(
            query="How does authentication work?",
            organization_id=org_id,
        )

        assert state["query"] == "How does authentication work?"
        assert state["organization_id"] == org_id
        assert state["repository_path"] is None
        assert state["conversation_id"] is None
        assert state["intent"] is None
        assert state["retrieved_memories"] == []
        assert state["repository_context"] == []
        assert state["incident_context"] == []
        assert state["repository_health"] is None
        assert state["citations"] == []
        assert state["agent_trace"] == []
        assert state["confidence"] == 0.0
        assert state["final_answer"] is None
        assert state["metadata"] == {}

    def test_create_initial_state_custom_params(self):
        """Test initial state creation with all optional arguments provided."""
        org_id = str(uuid4())
        conv_id = str(uuid4())
        metadata = {"user_id": "usr_123", "model": "ibm-granite"}

        state = create_initial_state(
            query="Analyze commit history",
            organization_id=org_id,
            repository_path="backend/app",
            conversation_id=conv_id,
            intent="repository_analysis",
            metadata=metadata,
        )

        assert state["query"] == "Analyze commit history"
        assert state["organization_id"] == org_id
        assert state["repository_path"] == "backend/app"
        assert state["conversation_id"] == conv_id
        assert state["intent"] == "repository_analysis"
        assert state["metadata"] == metadata

    def test_append_trace_immutability(self):
        """Test appending trace entries without mutating the original state."""
        org_id = str(uuid4())
        initial = create_initial_state("Fix bug", org_id)

        updated = append_trace(
            initial,
            agent="router_node",
            action="classify_intent",
            details={"intent": "incident_investigation"},
        )

        # Immutability assertion
        assert len(initial["agent_trace"]) == 0
        assert len(updated["agent_trace"]) == 1
        assert updated["agent_trace"][0]["agent"] == "router_node"
        assert updated["agent_trace"][0]["action"] == "classify_intent"
        assert updated["agent_trace"][0]["details"]["intent"] == "incident_investigation"

        # Successive appends
        second_update = append_trace(
            updated,
            agent="memory_node",
            action="retrieve_memories",
            details={"matches": 3},
        )
        assert len(updated["agent_trace"]) == 1
        assert len(second_update["agent_trace"]) == 2
        assert second_update["agent_trace"][1]["agent"] == "memory_node"

    def test_add_citation_immutability(self):
        """Test adding citation entries without mutating the original state."""
        org_id = str(uuid4())
        initial = create_initial_state("Explain caching", org_id)

        citation = {
            "file": "backend/app/core/cache.py",
            "lines": "10-45",
            "score": 0.94,
        }
        updated = add_citation(initial, citation)

        assert len(initial["citations"]) == 0
        assert len(updated["citations"]) == 1
        assert updated["citations"][0]["file"] == "backend/app/core/cache.py"
        assert updated["citations"][0]["score"] == 0.94

    def test_update_confidence_bounds(self):
        """Test confidence updates with upper/lower bounds clamping."""
        org_id = str(uuid4())
        initial = create_initial_state("Review PR", org_id)

        # Standard update
        s1 = update_confidence(initial, 0.85231)
        assert initial["confidence"] == 0.0
        assert s1["confidence"] == 0.8523

        # Clamping upper bound > 1.0
        s2 = update_confidence(initial, 1.5)
        assert s2["confidence"] == 1.0

        # Clamping lower bound < 0.0
        s3 = update_confidence(initial, -0.2)
        assert s3["confidence"] == 0.0

    def test_set_final_answer(self):
        """Test setting final answer and optional confidence updating."""
        org_id = str(uuid4())
        initial = create_initial_state("What is the DB schema?", org_id)

        s1 = set_final_answer(initial, "The DB uses PostgreSQL 17.")
        assert initial["final_answer"] is None
        assert s1["final_answer"] == "The DB uses PostgreSQL 17."
        assert s1["confidence"] == 0.0

        # With confidence specified
        s2 = set_final_answer(initial, "Final verified answer.", confidence=0.98)
        assert s2["final_answer"] == "Final verified answer."
        assert s2["confidence"] == 0.98


class TestLangGraphNodePlaceholders:
    """Test suite for node placeholder functions."""

    def test_router_node_placeholder(self):
        """Test router node appends trace and returns valid state."""
        state = create_initial_state("Test query", str(uuid4()))
        result = router_node(state)
        assert len(result["agent_trace"]) == 1
        assert result["agent_trace"][0]["agent"] == "router_node"

    def test_repository_node_placeholder(self):
        """Test repository node appends trace and returns valid state."""
        state = create_initial_state("Test query", str(uuid4()), repository_path="repo/path")
        result = repository_node(state)
        assert len(result["agent_trace"]) == 1
        assert result["agent_trace"][0]["agent"] == "repository_node"
        assert result["agent_trace"][0]["details"]["repository_path"] == "repo/path"

    def test_memory_node_placeholder(self):
        """Test memory node appends trace and returns valid state."""
        org_id = str(uuid4())
        state = create_initial_state("Test query", org_id)
        result = memory_node(state)
        assert len(result["agent_trace"]) == 1
        assert result["agent_trace"][0]["agent"] == "memory_node"
        assert result["agent_trace"][0]["details"]["organization_id"] == org_id

    def test_debug_node_placeholder(self):
        """Test debug node appends trace and returns valid state."""
        state = create_initial_state("Test error trace", str(uuid4()))
        result = debug_node(state)
        assert len(result["agent_trace"]) == 1
        assert result["agent_trace"][0]["agent"] == "debug_node"

    def test_merge_node_placeholder(self):
        """Test merge node appends trace and sets placeholder answer."""
        state = create_initial_state("Test query", str(uuid4()))
        result = merge_node(state)
        assert len(result["agent_trace"]) == 1
        assert result["agent_trace"][0]["agent"] == "merge_node"
        assert result["final_answer"] is not None
        assert result["confidence"] > 0.0


class TestLangGraphBuilder:
    """Test suite for graph builder skeleton."""

    def test_build_teammemory_graph(self):
        """Test graph builder returns a valid compiled LangGraph instance with registered nodes."""
        graph = build_teammemory_graph()
        assert graph is not None

        # Verify registered node names in compiled graph
        nodes = list(graph.nodes.keys())
        expected_nodes = ["router", "repository", "memory", "debug", "merge"]
        for node in expected_nodes:
            assert node in nodes


class TestLangGraphStreamingHelpers:
    """Test suite for streaming SSE helpers."""

    def test_stream_metadata(self):
        """Test stream_metadata produces correct SSE dictionary structure."""
        org_id = str(uuid4())
        conv_id = str(uuid4())
        state = create_initial_state("Query", org_id, conversation_id=conv_id, intent="chat")
        
        event = stream_metadata(state)
        assert event["event"] == "metadata"
        assert event["data"]["organization_id"] == org_id
        assert event["data"]["conversation_id"] == conv_id
        assert event["data"]["query"] == "Query"
        assert event["data"]["intent"] == "chat"

    def test_stream_agent_event(self):
        """Test stream_agent_event produces structured agent activity payload."""
        event = stream_agent_event(
            agent="repository_node",
            event_type="indexing_completed",
            data={"indexed_files": 42},
            message="Indexed 42 files.",
        )
        assert event["event"] == "agent_event"
        assert event["data"]["agent"] == "repository_node"
        assert event["data"]["event_type"] == "indexing_completed"
        assert event["data"]["data"]["indexed_files"] == 42
        assert event["data"]["message"] == "Indexed 42 files."

    def test_stream_done(self):
        """Test stream_done produces completion payload."""
        event = stream_done(
            metadata={"total_duration_ms": 120},
            final_answer="All checks passed.",
            confidence=0.99,
        )
        assert event["event"] == "done"
        assert event["data"]["status"] == "completed"
        assert event["data"]["final_answer"] == "All checks passed."
        assert event["data"]["confidence"] == 0.99
        assert event["data"]["metadata"]["total_duration_ms"] == 120

    def test_format_sse_event(self):
        """Test SSE wire format serialization."""
        event = {"event": "agent_event", "data": {"agent": "router", "status": "ok"}}
        raw_sse = format_sse_event(event)

        assert raw_sse.startswith("event: agent_event\ndata: ")
        assert raw_sse.endswith("\n\n")
        
        lines = raw_sse.strip().split("\n")
        assert lines[0] == "event: agent_event"
        assert lines[1].startswith("data: ")
        parsed_data = json.loads(lines[1][6:])
        assert parsed_data["agent"] == "router"
        assert parsed_data["status"] == "ok"
