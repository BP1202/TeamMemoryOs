"""
Repository Agent — Milestone 7.2.

Autonomous agent responsible for:
* Repository search (commit + file history via GraphRAG).
* Commit history lookup scoped to organisation.
* Branch name lookup from repository metadata.
* File history retrieval (commits that changed a specific file).
* GraphRAG retrieval for repository context.
* Explainable commit history with citations.

Reuses:
* HybridRetriever (Sprint 6 GraphRAG pipeline).
* ExplanationBuilder (Sprint 6 citation/confidence/graph-path builder).
* RepositoryService (Sprint 6 commit ingestion).

LangGraph compatibility: ``run()`` maps to a LangGraph node function.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.base import (
    AgentCapability,
    AgentResult,
    AgentState,
    AgentStatus,
)
from app.graph.explanation_builder import build_retrieval_explanation
from app.graph.hybrid_retriever import HybridRetriever
from app.memory.embedding_provider import StubEmbeddingProvider
from app.models.repository import CommitMemory, Repository
from app.services.repository import get_commits_by_repository, get_repositories_by_org


class RepositoryAgent:
    """GraphRAG-powered repository intelligence agent."""

    @property
    def name(self) -> str:
        return "repository_agent"

    @property
    def description(self) -> str:
        return (
            "Searches commit history, branches, and file history using GraphRAG "
            "retrieval. Returns explainable citations from organisational memory."
        )

    @property
    def capabilities(self) -> list[AgentCapability]:
        return [
            AgentCapability.REPOSITORY_SEARCH,
            AgentCapability.COMMIT_HISTORY,
            AgentCapability.BRANCH_LOOKUP,
            AgentCapability.FILE_HISTORY,
            AgentCapability.GRAPHRAG_RETRIEVAL,
            AgentCapability.EXPLANATION_BUILD,
        ]

    def run(self, state: AgentState) -> AgentResult:
        """Execute repository intelligence against the current state.

        Reads from state.context:
            question, organization_id, metadata.get("db"), metadata.get("repo_id")
        """
        state.record_agent(self.name)
        db: Session | None = state.context.metadata.get("db")
        if db is None:
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                answer="No database session provided to RepositoryAgent.",
                participating_agents=[self.name],
                metadata={"error": "missing_db"},
            )

        org_id: UUID = state.context.organization_id
        question: str = state.context.question
        repo_id: UUID | None = state.context.metadata.get("repo_id")

        try:
            # 1. GraphRAG retrieval for repository-related memories
            retriever = HybridRetriever(
                db=db,
                organization_id=org_id,
                embedding_provider=StubEmbeddingProvider(),
                top_k=5,
            )
            hybrid_results = retriever.retrieve(question)

            # 2. Build explanation
            explanation = build_retrieval_explanation(
                question=question,
                hybrid_results=hybrid_results,
                db=db,
                organization_id=org_id,
                retrieval_mode="hybrid",
            )

            # 3. Collect commit history (optional — when repo_id supplied)
            commit_summaries: list[dict[str, Any]] = []
            if repo_id:
                commits = get_commits_by_repository(
                    db, repository_id=repo_id, organization_id=org_id, limit=10
                )
                commit_summaries = [
                    {
                        "sha": c.commit_sha[:7],
                        "message": c.commit_message[:120],
                        "author": c.author_name,
                        "committed_at": c.committed_at.isoformat() if c.committed_at else None,
                        "files_changed": c.files_changed,
                    }
                    for c in commits
                ]

            # 4. Serialize citations
            citations = _serialize_citations(explanation.citations)
            graph_path = _serialize_graph_path(explanation.graph_path)

            # 5. Build answer
            answer_parts = [explanation.summary]
            if commit_summaries:
                answer_parts.append(
                    f"\nRecent commits ({len(commit_summaries)}):\n"
                    + "\n".join(
                        f"  [{c['sha']}] {c['author'] or 'unknown'}: {c['message']}"
                        for c in commit_summaries
                    )
                )
            answer = "\n".join(answer_parts)

            # 6. Update shared state
            state.citations.extend(citations)
            state.graph_path.extend(graph_path)
            state.memory_hits.extend(
                [{"memory_id": str(r.memory.id), "score": r.score} for r in hybrid_results]
            )
            state.confidence = max(state.confidence, explanation.confidence)
            state.suggested_actions.extend([
                "Review commit history for the affected component.",
                "Search file history for recent changes.",
                "Check branch state against organizational memory.",
            ])
            state.intermediate_results["repository_agent"] = {
                "commit_summaries": commit_summaries,
                "result_count": explanation.result_count,
            }
            state.add_message(role="agent", content=answer, agent=self.name)
            state.status = AgentStatus.COMPLETED

            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                answer=answer,
                citations=citations,
                graph_path=graph_path,
                confidence=explanation.confidence,
                suggested_actions=[
                    "Review commit history for the affected component.",
                    "Search file history for recent changes.",
                    "Check branch state against organizational memory.",
                ],
                participating_agents=[self.name],
                metadata={"commit_summaries": commit_summaries},
            )

        except Exception as exc:
            error_msg = f"RepositoryAgent failed: {type(exc).__name__}: {exc}"
            state.add_message(role="error", content=error_msg, agent=self.name)
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                answer=error_msg,
                participating_agents=[self.name],
                metadata={"error": str(exc)},
            )


# ---------------------------------------------------------------------------
# Branch + file history helpers (deterministic — no LLM)
# ---------------------------------------------------------------------------

def get_branches_for_org(db: Session, organization_id: UUID) -> list[str]:
    """Return unique branch names across all repositories for an organisation."""
    repos = get_repositories_by_org(db, organization_id=organization_id)
    branches = []
    for repo in repos:
        if repo.default_branch and repo.default_branch not in branches:
            branches.append(repo.default_branch)
    return branches


def get_file_history(
    db: Session,
    organization_id: UUID,
    file_path: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Return commits that mention *file_path* in their changed_files list."""
    stmt = (
        select(CommitMemory)
        .where(CommitMemory.organization_id == organization_id)
        .order_by(CommitMemory.committed_at.desc())
        .limit(limit * 5)  # over-fetch; we filter below
    )
    all_commits = db.scalars(stmt).all()
    hits = [
        {
            "sha": c.commit_sha[:7],
            "message": c.commit_message[:120],
            "author": c.author_name,
            "committed_at": c.committed_at.isoformat() if c.committed_at else None,
        }
        for c in all_commits
        if c.changed_files and any(file_path in f for f in c.changed_files)
    ]
    return hits[:limit]


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def _serialize_citations(citations) -> list[dict[str, Any]]:
    return [
        {
            "memory_id": str(c.memory_id),
            "memory_title": c.memory_title,
            "memory_type": c.memory_type,
            "retrieval_reason": c.retrieval_reason,
            "semantic_score": c.semantic_score,
            "graph_score": c.graph_score,
            "link_score": c.link_score,
            "final_score": c.final_score,
            "graph_distance": c.graph_distance,
            "matched_entities": c.matched_entities,
            "rank": c.rank,
        }
        for c in citations
    ]


def _serialize_graph_path(graph_path) -> list[dict[str, Any]]:
    return [
        {
            "source_entity_id": str(s.source_entity_id),
            "source_entity_name": s.source_entity_name,
            "relationship_type": s.relationship_type,
            "target_entity_id": str(s.target_entity_id),
            "target_entity_name": s.target_entity_name,
        }
        for s in graph_path
    ]
