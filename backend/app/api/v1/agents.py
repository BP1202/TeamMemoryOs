"""
Multi-Agent Platform API — Sprint 7.

Routes:
* GET  /agents/                      — List registered agents.
* GET  /agents/{name}                — Inspect agent capabilities.
* POST /agents/workflow/run          — Run a multi-agent workflow.
* POST /agents/workflow/plan         — Dry-run planner (no execution).
* POST /agents/repository/search     — Repository Agent.
* GET  /agents/repository/branches   — List branches for an org.
* POST /agents/repository/file-history — File history lookup.
* POST /agents/debug/analyze         — Debug Agent.
"""
from __future__ import annotations

import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.agents.base import AgentContext, AgentState
from app.agents.debug_agent import DebugAgent, parse_stack_trace
from app.agents.memory_store import (
    ConversationHistory,
    MultiAgentExplanationBuilder,
    memory_handoff,
)
from app.agents.orchestrator import WorkflowExecutor, WorkflowPlanner
from app.agents.registry import registry
from app.agents.repository_agent import (
    RepositoryAgent,
    get_branches_for_org,
    get_file_history,
)
from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.agents import (
    AgentListResponse,
    AgentRead,
    AgentWorkflowRequest,
    AgentWorkflowResponse,
    BranchListResponse,
    CommitSummary,
    ConversationTurnRead,
    DebugAgentRequest,
    DebugAgentResponse,
    FileHistoryRequest,
    FileHistoryResponse,
    ParsedTraceRead,
    RepoAgentRequest,
    RepoAgentResponse,
    WorkflowInspectRequest,
    WorkflowPlanRead,
)
from app.schemas.retrieval import CitationRead, GraphPathStepRead

router = APIRouter()

# ---------------------------------------------------------------------------
# Bootstrap registry — agents self-register at import time
# ---------------------------------------------------------------------------

def _ensure_registered() -> None:
    """Register built-in agents if not already in the registry."""
    if "repository_agent" not in registry:
        registry.register(RepositoryAgent())
    if "debug_agent" not in registry:
        registry.register(DebugAgent())


# ---------------------------------------------------------------------------
# Helper: serialise agent result fields to Pydantic schemas
# ---------------------------------------------------------------------------

def _to_citation_reads(citations: list[dict]) -> list[CitationRead]:
    out = []
    for c in citations:
        try:
            out.append(CitationRead(**c))
        except Exception:
            pass
    return out


def _to_graph_path_reads(graph_path: list[dict]) -> list[GraphPathStepRead]:
    out = []
    for p in graph_path:
        try:
            out.append(GraphPathStepRead(**p))
        except Exception:
            pass
    return out


# ---------------------------------------------------------------------------
# Agent registry endpoints
# ---------------------------------------------------------------------------

@router.get("/", response_model=AgentListResponse)
def list_agents(
    current_user: User = Depends(get_current_user),
):
    """List all registered agents and their capabilities."""
    _ensure_registered()
    agents = [
        AgentRead(
            name=a["name"],
            description=a["description"],
            capabilities=a["capabilities"],
        )
        for a in registry.list_agents()
    ]
    return AgentListResponse(agents=agents, total=len(agents))


@router.get("/{agent_name}", response_model=AgentRead)
def get_agent(
    agent_name: str,
    current_user: User = Depends(get_current_user),
):
    """Inspect a specific agent's capabilities by name."""
    _ensure_registered()
    agent = registry.get(agent_name)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found.",
        )
    return AgentRead(
        name=agent.name,
        description=agent.description,
        capabilities=[c.value for c in agent.capabilities],
    )


# ---------------------------------------------------------------------------
# Workflow endpoints
# ---------------------------------------------------------------------------

@router.post("/workflow/plan", response_model=WorkflowPlanRead)
def inspect_workflow_plan(
    body: WorkflowInspectRequest,
    current_user: User = Depends(get_current_user),
):
    """Dry-run the workflow planner — returns what agents would be used."""
    planner = WorkflowPlanner()
    plan = planner.plan(body.question, body.metadata)
    return WorkflowPlanRead(
        steps=plan.steps,
        mode=plan.mode,
        rationale=plan.rationale,
    )


@router.post("/workflow/run", response_model=AgentWorkflowResponse)
def run_workflow(
    body: AgentWorkflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute a multi-agent workflow.

    When ``agent_names`` is empty, the planner auto-selects agents.
    When ``mode`` is 'auto', sequential execution is used.
    The shared AgentState is threaded through all selected agents.
    """
    _ensure_registered()

    # Inject db session and user into context metadata
    metadata = dict(body.metadata)
    metadata["db"] = db
    if body.metadata.get("repo_id"):
        try:
            metadata["repo_id"] = _uuid.UUID(str(body.metadata["repo_id"]))
        except ValueError:
            pass

    context = AgentContext(
        organization_id=body.organization_id,
        user_id=current_user.id,
        question=body.question,
        metadata=metadata,
    )

    executor = WorkflowExecutor(registry)
    conversation = ConversationHistory()

    if body.agent_names:
        state = executor.run_sequential(context=context, agent_names=body.agent_names)
    else:
        state = executor.run_conditional(context=context)

    # Build conversation history from state messages
    for msg in state.messages:
        conversation.add(
            agent=msg.get("agent", "system"),
            role=msg.get("role", "agent"),
            content=msg.get("content", ""),
        )

    # Build final explanation
    builder = MultiAgentExplanationBuilder()
    explanation = builder.build(state, conversation)

    return AgentWorkflowResponse(
        answer=explanation.answer,
        participating_agents=explanation.participating_agents,
        citations=_to_citation_reads(explanation.citations),
        graph_path=_to_graph_path_reads(explanation.graph_path),
        confidence=explanation.confidence,
        suggested_actions=explanation.suggested_actions,
        conversation_history=[
            ConversationTurnRead(
                agent=t["agent"],
                role=t["role"],
                content=t["content"],
                timestamp=t.get("timestamp", ""),
            )
            for t in explanation.conversation_history
        ],
        retrieval_mode=explanation.retrieval_mode,
        status=explanation.status,
    )


# ---------------------------------------------------------------------------
# Repository Agent endpoints
# ---------------------------------------------------------------------------

@router.post("/repository/search", response_model=RepoAgentResponse)
def repository_search(
    body: RepoAgentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Repository Agent: search commits and memory using GraphRAG."""
    _ensure_registered()

    metadata: dict = {"db": db}
    if body.repo_id:
        metadata["repo_id"] = body.repo_id

    context = AgentContext(
        organization_id=body.organization_id,
        user_id=current_user.id,
        question=body.question,
        metadata=metadata,
    )
    state = AgentState(context=context)

    agent = registry.get("repository_agent")
    if agent is None:
        raise HTTPException(status_code=500, detail="repository_agent not registered.")

    result = agent.run(state)

    commit_summaries = [
        CommitSummary(**c)
        for c in result.metadata.get("commit_summaries", [])
    ]

    return RepoAgentResponse(
        answer=result.answer,
        participating_agents=result.participating_agents,
        citations=_to_citation_reads(result.citations),
        graph_path=_to_graph_path_reads(result.graph_path),
        confidence=result.confidence,
        suggested_actions=result.suggested_actions,
        commit_summaries=commit_summaries,
        status=result.status.value,
    )


@router.get("/repository/branches", response_model=BranchListResponse)
def list_branches(
    organization_id: _uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all known branches for an organisation."""
    branches = get_branches_for_org(db, organization_id=organization_id)
    return BranchListResponse(
        organization_id=organization_id,
        branches=branches,
    )


@router.post("/repository/file-history", response_model=FileHistoryResponse)
def file_history(
    body: FileHistoryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return commit history for a specific file path."""
    commits = get_file_history(
        db,
        organization_id=body.organization_id,
        file_path=body.file_path,
        limit=body.limit,
    )
    return FileHistoryResponse(
        file_path=body.file_path,
        organization_id=body.organization_id,
        commits=commits,
    )


# ---------------------------------------------------------------------------
# Debug Agent endpoints
# ---------------------------------------------------------------------------

@router.post("/debug/analyze", response_model=DebugAgentResponse)
def debug_analyze(
    body: DebugAgentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Debug Agent: parse stack trace and retrieve similar historical incidents."""
    _ensure_registered()

    context = AgentContext(
        organization_id=body.organization_id,
        user_id=current_user.id,
        question=body.error_message,
        metadata={
            "db": db,
            "stack_trace": body.stack_trace,
            "command": body.command,
        },
    )
    state = AgentState(context=context)

    agent = registry.get("debug_agent")
    if agent is None:
        raise HTTPException(status_code=500, detail="debug_agent not registered.")

    result = agent.run(state)
    parsed_raw = result.metadata.get("parsed_trace")
    parsed_read: ParsedTraceRead | None = None
    if parsed_raw:
        parsed_read = ParsedTraceRead(
            has_traceback=parsed_raw.get("has_traceback", False),
            exception_type=parsed_raw.get("exception_type"),
            exception_message=parsed_raw.get("exception_message"),
            frames=parsed_raw.get("frames", []),
            raw_excerpt=parsed_raw.get("raw_excerpt", ""),
        )

    return DebugAgentResponse(
        answer=result.answer,
        participating_agents=result.participating_agents,
        citations=_to_citation_reads(result.citations),
        graph_path=_to_graph_path_reads(result.graph_path),
        confidence=result.confidence,
        suggested_actions=result.suggested_actions,
        parsed_trace=parsed_read,
        incidents_found=result.metadata.get("incidents_found", 0),
        status=result.status.value,
    )
