"""Pydantic schemas for Sprint 7 — Multi-Agent Intelligence Platform."""
from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.retrieval import CitationRead, GraphPathStepRead


# ---------------------------------------------------------------------------
# Agent Registry schemas
# ---------------------------------------------------------------------------

class AgentCapabilityRead(BaseModel):
    """One capability exposed by an agent."""
    value: str
    label: str


class AgentRead(BaseModel):
    """Metadata for a registered agent (GET /agents/)."""
    name: str
    description: str
    capabilities: list[str]


class AgentListResponse(BaseModel):
    """Response for GET /agents/."""
    agents: list[AgentRead]
    total: int


# ---------------------------------------------------------------------------
# Workflow request/response
# ---------------------------------------------------------------------------

class AgentWorkflowRequest(BaseModel):
    """Request body for POST /agents/workflow/run."""
    organization_id: uuid.UUID
    question: str = Field(..., min_length=1, max_length=4000)
    # Explicit agent selection — if empty, planner decides
    agent_names: list[str] = Field(default_factory=list)
    # Extra context metadata for agents
    metadata: dict[str, Any] = Field(default_factory=dict)
    top_k: int = Field(default=5, ge=1, le=20)
    mode: Literal["auto", "sequential", "conditional"] = "auto"


class ConversationTurnRead(BaseModel):
    """One turn in the multi-agent conversation history."""
    agent: str
    role: str
    content: str
    timestamp: str = ""


class AgentWorkflowResponse(BaseModel):
    """Response from POST /agents/workflow/run.

    Includes all sprint-required fields:
    * participating_agents
    * citations
    * graph_path
    * confidence
    * suggested_actions
    * conversation history
    """
    answer: str
    participating_agents: list[str]
    citations: list[CitationRead]
    graph_path: list[GraphPathStepRead]
    confidence: float = Field(..., ge=0.0, le=1.0)
    suggested_actions: list[str]
    conversation_history: list[ConversationTurnRead]
    retrieval_mode: str = "hybrid"
    status: str


# ---------------------------------------------------------------------------
# Repository agent schemas
# ---------------------------------------------------------------------------

class RepoAgentRequest(BaseModel):
    """Request body for POST /agents/repository/search."""
    organization_id: uuid.UUID
    question: str = Field(..., min_length=1, max_length=4000)
    repo_id: uuid.UUID | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class CommitSummary(BaseModel):
    """Compact commit summary in agent responses."""
    sha: str
    message: str
    author: str | None
    committed_at: str | None
    files_changed: int = 0


class RepoAgentResponse(BaseModel):
    """Response from POST /agents/repository/search."""
    answer: str
    participating_agents: list[str]
    citations: list[CitationRead]
    graph_path: list[GraphPathStepRead]
    confidence: float = Field(..., ge=0.0, le=1.0)
    suggested_actions: list[str]
    commit_summaries: list[CommitSummary] = Field(default_factory=list)
    status: str


class BranchListResponse(BaseModel):
    """Response from GET /agents/repository/branches."""
    organization_id: uuid.UUID
    branches: list[str]


class FileHistoryRequest(BaseModel):
    """Request body for POST /agents/repository/file-history."""
    organization_id: uuid.UUID
    file_path: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=20, ge=1, le=100)


class FileHistoryResponse(BaseModel):
    """Response from POST /agents/repository/file-history."""
    file_path: str
    organization_id: uuid.UUID
    commits: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Debug agent schemas
# ---------------------------------------------------------------------------

class DebugAgentRequest(BaseModel):
    """Request body for POST /agents/debug/analyze."""
    organization_id: uuid.UUID
    error_message: str = Field(..., min_length=1, max_length=4000)
    stack_trace: str | None = None
    command: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class ParsedTraceRead(BaseModel):
    """Parsed stack trace summary included in debug responses."""
    has_traceback: bool
    exception_type: str | None
    exception_message: str | None
    frames: list[dict[str, Any]]
    raw_excerpt: str


class DebugAgentResponse(BaseModel):
    """Response from POST /agents/debug/analyze."""
    answer: str
    participating_agents: list[str]
    citations: list[CitationRead]
    graph_path: list[GraphPathStepRead]
    confidence: float = Field(..., ge=0.0, le=1.0)
    suggested_actions: list[str]
    parsed_trace: ParsedTraceRead | None = None
    incidents_found: int = 0
    status: str


# ---------------------------------------------------------------------------
# Workflow plan inspection
# ---------------------------------------------------------------------------

class WorkflowPlanRead(BaseModel):
    """Inspection view of what the planner decided."""
    steps: list[str]
    mode: str
    rationale: str


class WorkflowInspectRequest(BaseModel):
    """Request body for POST /agents/workflow/plan (dry-run)."""
    question: str = Field(..., min_length=1, max_length=4000)
    metadata: dict[str, Any] = Field(default_factory=dict)
