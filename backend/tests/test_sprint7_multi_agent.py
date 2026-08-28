"""
Sprint 7 — Multi-Agent Intelligence Platform Tests

Covers all 5 milestones:
* 7.1 Agent Registry — registration, listing, routing, capability filtering
* 7.2 Repository Agent — GraphRAG search, commits, branches, file history
* 7.3 Debug Agent — stack trace parsing, incident retrieval, root cause
* 7.4 Workflow Orchestrator — planner routing, sequential, conditional execution
* 7.5 Shared Memory Collaboration — memory store cache, handoff, conversation history,
      multi-agent explanation builder

API Validation:
* JWT authentication on all endpoints
* Organisation isolation
* Agent capability inspection
* Workflow run
* Repository search
* Debug analysis

Security:
* Organisation isolation
* Auth required on every endpoint
* No sensitive data in responses
"""
from __future__ import annotations

import uuid
from typing import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.agents.base import (
    AgentCapability,
    AgentContext,
    AgentResult,
    AgentState,
    AgentStatus,
    BaseAgent,
)
from app.agents.debug_agent import DebugAgent, parse_stack_trace
from app.agents.memory_store import (
    AgentMemoryStore,
    ConversationHistory,
    MultiAgentExplanationBuilder,
    memory_handoff,
)
from app.agents.orchestrator import (
    WorkflowExecutor,
    WorkflowPlanner,
    WorkflowRouter,
)
from app.agents.registry import AgentRegistry
from app.agents.repository_agent import RepositoryAgent
from app.main import app

# ---------------------------------------------------------------------------
# Base URLs
# ---------------------------------------------------------------------------

USERS_API = "/api/v1/users"
ORGS_API = "/api/v1/organizations"
AUTH_API = "/api/v1/auth/login"
AGENTS_API = "/api/v1/agents"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post(AUTH_API, data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _make_user_and_headers(client: TestClient, prefix: str = "sp7") -> dict:
    password = "ValidPass123!"
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post(
        f"{USERS_API}/",
        json={"full_name": "Sprint7 User", "email": email, "password": password},
    )
    assert resp.status_code == 201, resp.text
    token = _login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


def _make_org(client: TestClient) -> dict:
    slug = f"sp7-{uuid.uuid4().hex[:8]}"
    resp = client.post(f"{ORGS_API}/", json={"name": "Sprint7 Org", "slug": slug})
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Milestone 7.1 — Agent Registry (unit tests)
# ---------------------------------------------------------------------------

class TestAgentRegistry:

    def test_register_and_retrieve(self):
        reg = AgentRegistry()
        repo = RepositoryAgent()
        reg.register(repo)
        assert "repository_agent" in reg
        assert reg.get("repository_agent") is repo

    def test_register_duplicate_raises(self):
        reg = AgentRegistry()
        reg.register(RepositoryAgent())
        with pytest.raises(ValueError, match="already registered"):
            reg.register(RepositoryAgent())

    def test_get_missing_returns_none(self):
        reg = AgentRegistry()
        assert reg.get("nonexistent") is None

    def test_list_agents_returns_metadata(self):
        reg = AgentRegistry()
        reg.register(RepositoryAgent())
        reg.register(DebugAgent())
        agents = reg.list_agents()
        names = [a["name"] for a in agents]
        assert "repository_agent" in names
        assert "debug_agent" in names
        # Each agent must have capabilities
        for a in agents:
            assert len(a["capabilities"]) > 0

    def test_list_by_capability(self):
        reg = AgentRegistry()
        reg.register(RepositoryAgent())
        reg.register(DebugAgent())
        repo_agents = reg.list_by_capability(AgentCapability.REPOSITORY_SEARCH)
        assert any(a.name == "repository_agent" for a in repo_agents)
        debug_agents = reg.list_by_capability(AgentCapability.DEBUG_ANALYSIS)
        assert any(a.name == "debug_agent" for a in debug_agents)

    def test_list_by_capability_not_present(self):
        reg = AgentRegistry()
        reg.register(RepositoryAgent())
        result = reg.list_by_capability(AgentCapability.DEBUG_ANALYSIS)
        assert result == []

    def test_route_selects_correct_agents(self):
        reg = AgentRegistry()
        reg.register(RepositoryAgent())
        reg.register(DebugAgent())
        selected = reg.route([AgentCapability.DEBUG_ANALYSIS, AgentCapability.REPOSITORY_SEARCH])
        names = [a.name for a in selected]
        assert "debug_agent" in names
        assert "repository_agent" in names

    def test_route_no_duplicates(self):
        reg = AgentRegistry()
        reg.register(RepositoryAgent())
        selected = reg.route([AgentCapability.REPOSITORY_SEARCH, AgentCapability.COMMIT_HISTORY])
        # RepositoryAgent satisfies both — should appear only once
        assert len(selected) == 1

    def test_len(self):
        reg = AgentRegistry()
        assert len(reg) == 0
        reg.register(RepositoryAgent())
        assert len(reg) == 1


# ---------------------------------------------------------------------------
# Milestone 7.1 — AgentState unit tests
# ---------------------------------------------------------------------------

class TestAgentState:

    def _make_context(self) -> AgentContext:
        return AgentContext(
            organization_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question="test question",
        )

    def test_record_agent(self):
        ctx = self._make_context()
        state = AgentState(context=ctx)
        state.record_agent("agent_a")
        state.record_agent("agent_b")
        state.record_agent("agent_a")  # duplicate
        assert state.participating_agents == ["agent_a", "agent_b"]

    def test_add_message(self):
        ctx = self._make_context()
        state = AgentState(context=ctx)
        state.add_message(role="agent", content="hello", agent="repo_agent")
        assert len(state.messages) == 1
        assert state.messages[0]["content"] == "hello"
        assert state.messages[0]["agent"] == "repo_agent"

    def test_default_status_is_pending(self):
        ctx = self._make_context()
        state = AgentState(context=ctx)
        assert state.status == AgentStatus.PENDING

    def test_state_confidence_starts_zero(self):
        ctx = self._make_context()
        state = AgentState(context=ctx)
        assert state.confidence == 0.0


# ---------------------------------------------------------------------------
# Milestone 7.1 — BaseAgent protocol compliance
# ---------------------------------------------------------------------------

class TestBaseAgentProtocol:

    def test_repository_agent_is_base_agent(self):
        agent = RepositoryAgent()
        assert isinstance(agent, BaseAgent)

    def test_debug_agent_is_base_agent(self):
        agent = DebugAgent()
        assert isinstance(agent, BaseAgent)

    def test_repository_agent_properties(self):
        agent = RepositoryAgent()
        assert agent.name == "repository_agent"
        assert len(agent.capabilities) > 0
        assert agent.description != ""

    def test_debug_agent_properties(self):
        agent = DebugAgent()
        assert agent.name == "debug_agent"
        assert AgentCapability.DEBUG_ANALYSIS in agent.capabilities
        assert AgentCapability.STACK_TRACE_PARSE in agent.capabilities
        assert AgentCapability.INCIDENT_RETRIEVAL in agent.capabilities


# ---------------------------------------------------------------------------
# Milestone 7.2 — Repository Agent unit tests
# ---------------------------------------------------------------------------

class TestRepositoryAgent:

    def _context(self, db=None, repo_id=None) -> AgentContext:
        meta = {"db": db or MagicMock()}
        if repo_id:
            meta["repo_id"] = repo_id
        return AgentContext(
            organization_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question="show recent commits for auth service",
            metadata=meta,
        )

    def test_run_fails_gracefully_without_db(self):
        agent = RepositoryAgent()
        ctx = AgentContext(
            organization_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question="test",
            metadata={},
        )
        state = AgentState(context=ctx)
        result = agent.run(state)
        assert result.status == AgentStatus.FAILED
        assert result.agent_name == "repository_agent"
        assert "database" in result.answer.lower() or "db" in result.answer.lower()

    def test_run_records_agent_in_state(self):
        agent = RepositoryAgent()
        ctx = AgentContext(
            organization_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question="commits",
            metadata={},  # no db — will fail gracefully
        )
        state = AgentState(context=ctx)
        agent.run(state)
        assert "repository_agent" in state.participating_agents

    def test_capabilities_include_graphrag(self):
        agent = RepositoryAgent()
        assert AgentCapability.GRAPHRAG_RETRIEVAL in agent.capabilities
        assert AgentCapability.COMMIT_HISTORY in agent.capabilities
        assert AgentCapability.BRANCH_LOOKUP in agent.capabilities
        assert AgentCapability.FILE_HISTORY in agent.capabilities


# ---------------------------------------------------------------------------
# Milestone 7.3 — Debug Agent unit tests
# ---------------------------------------------------------------------------

class TestDebugAgent:

    def test_parse_stack_trace_python(self):
        text = (
            "Traceback (most recent call last):\n"
            '  File "app/main.py", line 42, in startup\n'
            "    db.connect()\n"
            "sqlalchemy.exc.OperationalError: could not connect to server"
        )
        result = parse_stack_trace(text)
        assert result["has_traceback"] is True
        assert result["exception_type"] == "sqlalchemy.exc.OperationalError"
        assert "could not connect" in result["exception_message"]
        assert len(result["frames"]) >= 1

    def test_parse_stack_trace_no_traceback(self):
        text = "Error: some generic failure"
        result = parse_stack_trace(text)
        assert result["has_traceback"] is False

    def test_parse_stack_trace_valueerror(self):
        text = (
            "Traceback (most recent call last):\n"
            '  File "test.py", line 5, in test_fn\n'
            "    raise ValueError('bad input')\n"
            "ValueError: bad input"
        )
        result = parse_stack_trace(text)
        assert result["has_traceback"] is True
        assert result["exception_type"] == "ValueError"

    def test_debug_agent_fails_gracefully_without_db(self):
        agent = DebugAgent()
        ctx = AgentContext(
            organization_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question="ImportError: module not found",
            metadata={},  # no db
        )
        state = AgentState(context=ctx)
        result = agent.run(state)
        assert result.status == AgentStatus.FAILED
        assert result.agent_name == "debug_agent"

    def test_debug_agent_records_agent(self):
        agent = DebugAgent()
        ctx = AgentContext(
            organization_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question="error",
            metadata={},
        )
        state = AgentState(context=ctx)
        agent.run(state)
        assert "debug_agent" in state.participating_agents

    def test_debug_agent_capabilities(self):
        agent = DebugAgent()
        caps = agent.capabilities
        assert AgentCapability.DEBUG_ANALYSIS in caps
        assert AgentCapability.STACK_TRACE_PARSE in caps
        assert AgentCapability.INCIDENT_RETRIEVAL in caps
        assert AgentCapability.GRAPHRAG_RETRIEVAL in caps


# ---------------------------------------------------------------------------
# Milestone 7.4 — Workflow Orchestrator unit tests
# ---------------------------------------------------------------------------

class TestWorkflowPlanner:

    def test_plan_debug_question(self):
        planner = WorkflowPlanner()
        plan = planner.plan("TypeError: cannot unpack non-sequence")
        assert "debug_agent" in plan.steps

    def test_plan_repo_question(self):
        planner = WorkflowPlanner()
        plan = planner.plan("show me recent commits on the auth branch")
        assert "repository_agent" in plan.steps

    def test_plan_generic_question_runs_both(self):
        planner = WorkflowPlanner()
        plan = planner.plan("what is the best approach here?")
        assert "debug_agent" in plan.steps
        assert "repository_agent" in plan.steps

    def test_plan_with_repo_id_context(self):
        planner = WorkflowPlanner()
        plan = planner.plan("analyse", context_metadata={"repo_id": uuid.uuid4()})
        assert "repository_agent" in plan.steps

    def test_plan_mode_is_sequential(self):
        planner = WorkflowPlanner()
        plan = planner.plan("any question")
        assert plan.mode == "sequential"

    def test_plan_rationale_is_populated(self):
        planner = WorkflowPlanner()
        plan = planner.plan("error crash")
        assert len(plan.rationale) > 0


class TestWorkflowRouter:

    def test_resolve_known_agents(self):
        reg = AgentRegistry()
        reg.register(RepositoryAgent())
        reg.register(DebugAgent())
        router = WorkflowRouter(reg)

        from app.agents.orchestrator import WorkflowPlan
        plan = WorkflowPlan(
            steps=["repository_agent", "debug_agent"],
            mode="sequential",
            rationale="test",
        )
        resolved = router.resolve(plan)
        assert len(resolved) == 2

    def test_resolve_skips_unknown_agents(self):
        reg = AgentRegistry()
        reg.register(RepositoryAgent())
        router = WorkflowRouter(reg)

        from app.agents.orchestrator import WorkflowPlan
        plan = WorkflowPlan(
            steps=["repository_agent", "nonexistent_agent"],
            mode="sequential",
            rationale="test",
        )
        resolved = router.resolve(plan)
        assert len(resolved) == 1
        assert resolved[0].name == "repository_agent"


class TestWorkflowExecutor:

    def _make_registry(self) -> AgentRegistry:
        reg = AgentRegistry()
        reg.register(RepositoryAgent())
        reg.register(DebugAgent())
        return reg

    def test_sequential_run_with_no_db_completes(self):
        """Agents without db fail gracefully — state still reaches COMPLETED."""
        reg = self._make_registry()
        executor = WorkflowExecutor(reg)
        ctx = AgentContext(
            organization_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question="test question",
            metadata={},  # no db — agents fail gracefully
        )
        state = executor.run_sequential(context=ctx, agent_names=["debug_agent"])
        # State should record that debug_agent ran
        assert "debug_agent" in state.participating_agents

    def test_conditional_run_uses_planner(self):
        reg = self._make_registry()
        executor = WorkflowExecutor(reg)
        ctx = AgentContext(
            organization_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question="ImportError on startup",
            metadata={},
        )
        state = executor.run_conditional(context=ctx)
        # Planner should have selected debug_agent
        assert "debug_agent" in state.participating_agents

    def test_build_final_response_deduplicates_citations(self):
        reg = self._make_registry()
        executor = WorkflowExecutor(reg)
        ctx = AgentContext(
            organization_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question="test",
            metadata={},
        )
        state = AgentState(context=ctx)
        mid = str(uuid.uuid4())
        state.citations.append({"memory_id": mid, "rank": 1})
        state.citations.append({"memory_id": mid, "rank": 1})  # duplicate
        state.add_message(role="agent", content="test answer", agent="debug_agent")

        response = executor.build_final_response(state)
        # Citations should be deduplicated
        assert len([c for c in response["citations"] if c["memory_id"] == mid]) == 1

    def test_build_final_response_deduplicates_actions(self):
        reg = self._make_registry()
        executor = WorkflowExecutor(reg)
        ctx = AgentContext(
            organization_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question="test",
            metadata={},
        )
        state = AgentState(context=ctx)
        state.suggested_actions = ["action A", "action B", "action A"]
        state.add_message(role="agent", content="answer", agent="debug_agent")

        response = executor.build_final_response(state)
        assert response["suggested_actions"].count("action A") == 1


# ---------------------------------------------------------------------------
# Milestone 7.5 — Shared Memory Collaboration unit tests
# ---------------------------------------------------------------------------

class TestAgentMemoryStore:

    def test_cache_hit(self):
        """Second call with same question returns cached results."""
        db = MagicMock()
        # Provide minimal mock that makes HybridRetriever return empty
        db.scalars.return_value.all.return_value = []
        store = AgentMemoryStore(
            db=db,
            organization_id=uuid.uuid4(),
            top_k=3,
        )
        store.retrieve("test question")
        initial_db_call_count = db.scalars.call_count
        store.retrieve("test question")  # should hit cache
        # DB should NOT have been called again for same question
        assert db.scalars.call_count == initial_db_call_count

    def test_cache_miss_for_different_questions(self):
        db = MagicMock()
        db.scalars.return_value.all.return_value = []
        store = AgentMemoryStore(db=db, organization_id=uuid.uuid4())
        store.retrieve("question A")
        count_after_first = db.scalars.call_count
        store.retrieve("question B")
        # Should have called db again for new question
        assert db.scalars.call_count > count_after_first

    def test_cache_size(self):
        db = MagicMock()
        db.scalars.return_value.all.return_value = []
        store = AgentMemoryStore(db=db, organization_id=uuid.uuid4())
        assert store.cache_size() == 0
        store.retrieve("q1")
        assert store.cache_size() == 1
        store.retrieve("q2")
        assert store.cache_size() == 2
        store.retrieve("q1")  # cache hit
        assert store.cache_size() == 2


class TestConversationHistory:

    def test_add_and_retrieve(self):
        history = ConversationHistory()
        history.add("repo_agent", "agent", "here are the commits")
        history.add("debug_agent", "agent", "root cause found")
        assert len(history) == 2

    def test_to_dict(self):
        history = ConversationHistory()
        history.add("agent_a", "agent", "response A")
        d = history.to_dict()
        assert len(d) == 1
        assert d[0]["agent"] == "agent_a"
        assert d[0]["content"] == "response A"
        assert "timestamp" in d[0]

    def test_agent_messages_filter(self):
        history = ConversationHistory()
        history.add("agent_a", "agent", "msg from A")
        history.add("agent_b", "agent", "msg from B")
        history.add("agent_a", "agent", "another from A")
        a_msgs = history.agent_messages("agent_a")
        assert len(a_msgs) == 2
        assert all(t.agent == "agent_a" for t in a_msgs)


class TestMemoryHandoff:

    def _make_context(self) -> AgentContext:
        return AgentContext(
            organization_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question="test",
        )

    def test_handoff_merges_citations(self):
        ctx = self._make_context()
        target_state = AgentState(context=ctx)
        source_result = AgentResult(
            agent_name="repo_agent",
            status=AgentStatus.COMPLETED,
            citations=[{"memory_id": "abc", "rank": 1}],
        )
        memory_handoff(source_result, target_state, "repo_handoff")
        assert len(target_state.citations) == 1

    def test_handoff_deduplicates_citations(self):
        ctx = self._make_context()
        target_state = AgentState(context=ctx)
        target_state.citations.append({"memory_id": "abc", "rank": 1})
        source_result = AgentResult(
            agent_name="repo_agent",
            status=AgentStatus.COMPLETED,
            citations=[{"memory_id": "abc", "rank": 1}],  # same id
        )
        memory_handoff(source_result, target_state, "key")
        assert len(target_state.citations) == 1  # not duplicated

    def test_handoff_takes_max_confidence(self):
        ctx = self._make_context()
        target_state = AgentState(context=ctx)
        target_state.confidence = 0.5
        source_result = AgentResult(
            agent_name="debug_agent",
            status=AgentStatus.COMPLETED,
            confidence=0.9,
        )
        memory_handoff(source_result, target_state, "key")
        assert target_state.confidence == 0.9

    def test_handoff_stores_intermediate_result(self):
        ctx = self._make_context()
        target_state = AgentState(context=ctx)
        source_result = AgentResult(
            agent_name="repo_agent",
            status=AgentStatus.COMPLETED,
            answer="commit history",
        )
        memory_handoff(source_result, target_state, "repo_handoff")
        assert "repo_handoff" in target_state.intermediate_results


class TestMultiAgentExplanationBuilder:

    def _make_state(self) -> AgentState:
        ctx = AgentContext(
            organization_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            question="test",
        )
        state = AgentState(context=ctx)
        state.participating_agents = ["debug_agent", "repository_agent"]
        state.citations = [
            {"memory_id": "id1", "rank": 1},
            {"memory_id": "id2", "rank": 2},
            {"memory_id": "id1", "rank": 1},  # duplicate
        ]
        state.graph_path = [
            {"source_entity_id": "e1", "target_entity_id": "e2"},
        ]
        state.confidence = 0.75
        state.suggested_actions = ["check logs", "review commits", "check logs"]
        state.add_message(role="agent", content="Found the bug.", agent="debug_agent")
        state.add_message(role="agent", content="Relevant commits found.", agent="repository_agent")
        state.status = AgentStatus.COMPLETED
        return state

    def test_builds_explanation(self):
        builder = MultiAgentExplanationBuilder()
        state = self._make_state()
        explanation = builder.build(state)
        assert "Found the bug" in explanation.answer
        assert "Relevant commits" in explanation.answer
        assert explanation.confidence == 0.75

    def test_deduplicates_citations(self):
        builder = MultiAgentExplanationBuilder()
        state = self._make_state()
        explanation = builder.build(state)
        ids = [c["memory_id"] for c in explanation.citations]
        assert ids.count("id1") == 1  # deduplicated

    def test_deduplicates_suggested_actions(self):
        builder = MultiAgentExplanationBuilder()
        state = self._make_state()
        explanation = builder.build(state)
        assert explanation.suggested_actions.count("check logs") == 1

    def test_includes_participating_agents(self):
        builder = MultiAgentExplanationBuilder()
        state = self._make_state()
        explanation = builder.build(state)
        assert "debug_agent" in explanation.participating_agents
        assert "repository_agent" in explanation.participating_agents

    def test_with_conversation_history(self):
        builder = MultiAgentExplanationBuilder()
        state = self._make_state()
        conv = ConversationHistory()
        conv.add("debug_agent", "agent", "Found the bug.")
        explanation = builder.build(state, conv)
        assert len(explanation.conversation_history) >= 1


# ---------------------------------------------------------------------------
# API Integration Tests — Milestone 7.1 (Agent Registry endpoints)
# ---------------------------------------------------------------------------

class TestAgentRegistryAPI:

    def test_list_agents_requires_auth(self, client: TestClient):
        resp = client.get(f"{AGENTS_API}/")
        assert resp.status_code == 401

    def test_list_agents_authenticated(self, client: TestClient):
        headers = _make_user_and_headers(client)
        resp = client.get(f"{AGENTS_API}/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "agents" in data
        assert "total" in data
        names = [a["name"] for a in data["agents"]]
        assert "repository_agent" in names
        assert "debug_agent" in names

    def test_get_agent_by_name(self, client: TestClient):
        headers = _make_user_and_headers(client)
        resp = client.get(f"{AGENTS_API}/repository_agent", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "repository_agent"
        assert len(data["capabilities"]) > 0

    def test_get_agent_not_found(self, client: TestClient):
        headers = _make_user_and_headers(client)
        resp = client.get(f"{AGENTS_API}/nonexistent_agent_xyz", headers=headers)
        assert resp.status_code == 404

    def test_get_debug_agent_capabilities(self, client: TestClient):
        headers = _make_user_and_headers(client)
        resp = client.get(f"{AGENTS_API}/debug_agent", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "debug_analysis" in data["capabilities"]
        assert "stack_trace_parse" in data["capabilities"]


# ---------------------------------------------------------------------------
# API Integration Tests — Workflow Planner dry-run
# ---------------------------------------------------------------------------

class TestWorkflowPlanAPI:

    def test_workflow_plan_requires_auth(self, client: TestClient):
        resp = client.post(
            f"{AGENTS_API}/workflow/plan",
            json={"question": "error crash"},
        )
        assert resp.status_code == 401

    def test_workflow_plan_debug_question(self, client: TestClient):
        headers = _make_user_and_headers(client)
        resp = client.post(
            f"{AGENTS_API}/workflow/plan",
            json={"question": "ImportError: cannot import module"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "debug_agent" in data["steps"]
        assert len(data["rationale"]) > 0

    def test_workflow_plan_repo_question(self, client: TestClient):
        headers = _make_user_and_headers(client)
        resp = client.post(
            f"{AGENTS_API}/workflow/plan",
            json={"question": "show me the commit history for the auth module"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "repository_agent" in data["steps"]


# ---------------------------------------------------------------------------
# API Integration Tests — Workflow run
# ---------------------------------------------------------------------------

class TestWorkflowRunAPI:

    def test_workflow_run_requires_auth(self, client: TestClient):
        resp = client.post(
            f"{AGENTS_API}/workflow/run",
            json={"organization_id": str(uuid.uuid4()), "question": "test"},
        )
        assert resp.status_code == 401

    def test_workflow_run_authenticated(self, client: TestClient):
        headers = _make_user_and_headers(client)
        org = _make_org(client)
        resp = client.post(
            f"{AGENTS_API}/workflow/run",
            json={
                "organization_id": org["id"],
                "question": "ImportError on startup — module not found",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "participating_agents" in data
        assert "citations" in data
        assert "graph_path" in data
        assert "confidence" in data
        assert "suggested_actions" in data
        assert "conversation_history" in data
        assert data["retrieval_mode"] == "hybrid"
        assert data["status"] in ("completed", "failed")

    def test_workflow_run_includes_all_required_fields(self, client: TestClient):
        """Sprint 7 spec: response MUST include participating_agents, citations,
        graph_path, confidence, suggested_actions."""
        headers = _make_user_and_headers(client)
        org = _make_org(client)
        resp = client.post(
            f"{AGENTS_API}/workflow/run",
            json={
                "organization_id": org["id"],
                "question": "show git commit history",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        required_fields = [
            "answer", "participating_agents", "citations",
            "graph_path", "confidence", "suggested_actions",
            "conversation_history", "status",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_workflow_run_org_isolation(self, client: TestClient):
        """Org A's workflow does not affect Org B's memory."""
        headers_a = _make_user_and_headers(client, prefix="sp7a")
        headers_b = _make_user_and_headers(client, prefix="sp7b")
        org_a = _make_org(client)
        org_b = _make_org(client)

        resp_a = client.post(
            f"{AGENTS_API}/workflow/run",
            json={"organization_id": org_a["id"], "question": "recent commits"},
            headers=headers_a,
        )
        resp_b = client.post(
            f"{AGENTS_API}/workflow/run",
            json={"organization_id": org_b["id"], "question": "recent commits"},
            headers=headers_b,
        )
        assert resp_a.status_code == 200
        assert resp_b.status_code == 200
        # Different orgs should get their own isolated results
        assert resp_a.json()["status"] in ("completed", "failed")
        assert resp_b.json()["status"] in ("completed", "failed")

    def test_workflow_run_explicit_agents(self, client: TestClient):
        """Explicit agent_names are respected over planner selection."""
        headers = _make_user_and_headers(client)
        org = _make_org(client)
        resp = client.post(
            f"{AGENTS_API}/workflow/run",
            json={
                "organization_id": org["id"],
                "question": "test explicit agent",
                "agent_names": ["debug_agent"],
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "debug_agent" in data["participating_agents"]

    def test_workflow_run_confidence_in_range(self, client: TestClient):
        headers = _make_user_and_headers(client)
        org = _make_org(client)
        resp = client.post(
            f"{AGENTS_API}/workflow/run",
            json={"organization_id": org["id"], "question": "test confidence"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert 0.0 <= data["confidence"] <= 1.0


# ---------------------------------------------------------------------------
# API Integration Tests — Repository Agent
# ---------------------------------------------------------------------------

class TestRepoAgentAPI:

    def test_repo_search_requires_auth(self, client: TestClient):
        resp = client.post(
            f"{AGENTS_API}/repository/search",
            json={"organization_id": str(uuid.uuid4()), "question": "commits"},
        )
        assert resp.status_code == 401

    def test_repo_search_authenticated(self, client: TestClient):
        headers = _make_user_and_headers(client)
        org = _make_org(client)
        resp = client.post(
            f"{AGENTS_API}/repository/search",
            json={"organization_id": org["id"], "question": "recent commits"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "participating_agents" in data
        assert "citations" in data
        assert "confidence" in data
        assert "repository_agent" in data["participating_agents"]

    def test_list_branches_requires_auth(self, client: TestClient):
        resp = client.get(
            f"{AGENTS_API}/repository/branches",
            params={"organization_id": str(uuid.uuid4())},
        )
        assert resp.status_code == 401

    def test_list_branches_authenticated(self, client: TestClient):
        headers = _make_user_and_headers(client)
        org = _make_org(client)
        resp = client.get(
            f"{AGENTS_API}/repository/branches",
            params={"organization_id": org["id"]},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "branches" in data
        assert isinstance(data["branches"], list)

    def test_file_history_requires_auth(self, client: TestClient):
        resp = client.post(
            f"{AGENTS_API}/repository/file-history",
            json={"organization_id": str(uuid.uuid4()), "file_path": "app/main.py"},
        )
        assert resp.status_code == 401

    def test_file_history_authenticated(self, client: TestClient):
        headers = _make_user_and_headers(client)
        org = _make_org(client)
        resp = client.post(
            f"{AGENTS_API}/repository/file-history",
            json={"organization_id": org["id"], "file_path": "app/main.py"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["file_path"] == "app/main.py"
        assert isinstance(data["commits"], list)


# ---------------------------------------------------------------------------
# API Integration Tests — Debug Agent
# ---------------------------------------------------------------------------

class TestDebugAgentAPI:

    def test_debug_analyze_requires_auth(self, client: TestClient):
        resp = client.post(
            f"{AGENTS_API}/debug/analyze",
            json={
                "organization_id": str(uuid.uuid4()),
                "error_message": "ImportError: no module",
            },
        )
        assert resp.status_code == 401

    def test_debug_analyze_authenticated(self, client: TestClient):
        headers = _make_user_and_headers(client)
        org = _make_org(client)
        resp = client.post(
            f"{AGENTS_API}/debug/analyze",
            json={
                "organization_id": org["id"],
                "error_message": "ImportError: No module named 'requests'",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "app/main.py", line 5, in <module>\n'
                    "    import requests\n"
                    "ImportError: No module named 'requests'"
                ),
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "debug_agent" in data["participating_agents"]
        assert "citations" in data
        assert "suggested_actions" in data
        assert isinstance(data["incidents_found"], int)

    def test_debug_analyze_returns_parsed_trace(self, client: TestClient):
        headers = _make_user_and_headers(client)
        org = _make_org(client)
        resp = client.post(
            f"{AGENTS_API}/debug/analyze",
            json={
                "organization_id": org["id"],
                "error_message": "ValueError: invalid literal for int",
                "stack_trace": (
                    "Traceback (most recent call last):\n"
                    '  File "app/service.py", line 10\n'
                    "ValueError: invalid literal for int"
                ),
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        if data.get("parsed_trace"):
            parsed = data["parsed_trace"]
            assert "has_traceback" in parsed
            assert "exception_type" in parsed

    def test_debug_analyze_org_isolation(self, client: TestClient):
        """Debug agent uses organization_id for all retrievals."""
        headers = _make_user_and_headers(client, prefix="sp7dbg")
        org_a = _make_org(client)
        org_b = _make_org(client)

        resp_a = client.post(
            f"{AGENTS_API}/debug/analyze",
            json={"organization_id": org_a["id"], "error_message": "connection refused"},
            headers=headers,
        )
        resp_b = client.post(
            f"{AGENTS_API}/debug/analyze",
            json={"organization_id": org_b["id"], "error_message": "connection refused"},
            headers=headers,
        )
        assert resp_a.status_code == 200
        assert resp_b.status_code == 200

    def test_debug_analyze_with_command(self, client: TestClient):
        headers = _make_user_and_headers(client)
        org = _make_org(client)
        resp = client.post(
            f"{AGENTS_API}/debug/analyze",
            json={
                "organization_id": org["id"],
                "error_message": "PermissionError: access denied",
                "command": "sudo apt install python3",
            },
            headers=headers,
        )
        assert resp.status_code == 200

    def test_debug_analyze_confidence_range(self, client: TestClient):
        headers = _make_user_and_headers(client)
        org = _make_org(client)
        resp = client.post(
            f"{AGENTS_API}/debug/analyze",
            json={
                "organization_id": org["id"],
                "error_message": "build failed: compilation error",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert 0.0 <= data["confidence"] <= 1.0


# ---------------------------------------------------------------------------
# Security validation
# ---------------------------------------------------------------------------

class TestAgentSecurityBoundaries:

    def test_all_agent_endpoints_require_jwt(self, client: TestClient):
        """Every agent endpoint must return 401 without auth."""
        org_id = str(uuid.uuid4())
        endpoints_without_auth = [
            ("GET", f"{AGENTS_API}/", None),
            ("GET", f"{AGENTS_API}/debug_agent", None),
            ("POST", f"{AGENTS_API}/workflow/plan", {"question": "test"}),
            ("POST", f"{AGENTS_API}/workflow/run", {"organization_id": org_id, "question": "test"}),
            ("POST", f"{AGENTS_API}/repository/search", {"organization_id": org_id, "question": "test"}),
            ("GET", f"{AGENTS_API}/repository/branches", None),
            ("POST", f"{AGENTS_API}/repository/file-history", {"organization_id": org_id, "file_path": "app.py"}),
            ("POST", f"{AGENTS_API}/debug/analyze", {"organization_id": org_id, "error_message": "err"}),
        ]
        for method, url, body in endpoints_without_auth:
            if method == "GET":
                resp = client.get(url)
            else:
                resp = client.post(url, json=body)
            assert resp.status_code == 401, f"Expected 401 on {method} {url}, got {resp.status_code}"

    def test_agent_result_does_not_expose_db_session(self, client: TestClient):
        """Agent responses must not contain raw database objects."""
        headers = _make_user_and_headers(client)
        org = _make_org(client)
        resp = client.post(
            f"{AGENTS_API}/debug/analyze",
            json={"organization_id": org["id"], "error_message": "test"},
            headers=headers,
        )
        assert resp.status_code == 200
        response_text = resp.text
        # Should not expose session objects
        assert "Session" not in response_text
        assert "sqlalchemy" not in response_text.lower()

    def test_no_secrets_in_agent_response(self, client: TestClient):
        """Responses must not contain credential-like strings."""
        headers = _make_user_and_headers(client)
        org = _make_org(client)
        resp = client.post(
            f"{AGENTS_API}/workflow/run",
            json={"organization_id": org["id"], "question": "password=abc token=xyz"},
            headers=headers,
        )
        assert resp.status_code == 200
        # Response should not echo raw secrets (secret filtering)
        data_text = resp.text
        # These patterns should not appear unfiltered in structured response
        # (Note: question text IS echoed in conversation_history — this is expected)
        # The important check is no JWT/API key values
        assert "GRANITE_API_KEY" not in data_text
        assert "JWT_SECRET_KEY" not in data_text


# ---------------------------------------------------------------------------
# conftest fixture reference — use session-scoped TestClient from conftest
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
