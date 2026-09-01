"""PR Guardian service (Milestone 6.2).

Deterministic parsing + GraphRAG retrieval + Granite summarisation.

Pipeline:
1. Parse diff text → extract changed files, detect risk patterns.
2. Extract entities from title, description, diff.
3. Retrieve similar historical PRs and decisions via HybridRetriever.
4. Score risk deterministically.
5. Build review suggestions from retrieved context.
6. Optionally summarize via Granite.
"""
from __future__ import annotations

import re
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.graph.explanation_builder import build_retrieval_explanation
from app.graph.hybrid_retriever import HybridRetriever
from app.memory.embedding_provider import StubEmbeddingProvider
from app.memory.generation_provider import get_generation_provider
from app.memory.prompt_builder import build_prompt
from app.memory.rag_context import _format_context
from app.models.entity import EntityType, MemoryEntity
from app.models.memory_entry import MemoryEntry, MemoryType
from app.models.pull_request import PullRequest, PullRequestReview, PRStatus
from app.schemas.pull_request import (
    PRReviewRequest,
    PRRiskResponse,
    PullRequestCreate,
    PullRequestReviewRead,
)
from app.services.entity import get_or_create_entity
from app.services.entity_extraction import extract_entities


# ---------------------------------------------------------------------------
# Risk pattern detection
# ---------------------------------------------------------------------------

_HIGH_RISK_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(migration|migrate|schema change)\b",
        r"\b(drop table|delete from|truncate)\b",
        r"\b(secret|password|credential|api.?key)\b",
        r"\b(production|prod)\b",
        r"\b(breaking change|breaking api)\b",
    ]
]

_MEDIUM_RISK_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(auth|authentication|authorization|permission)\b",
        r"\b(security|vulnerability|cve)\b",
        r"\b(database|db|sql)\b",
        r"\b(config|configuration|env|environment)\b",
    ]
]


def _compute_risk_score(
    title: str,
    description: str | None,
    diff_text: str | None,
    files_changed: int,
) -> tuple[float, list[str]]:
    """Deterministic risk scoring — no LLM required.

    Returns (score in [0.0, 1.0], list of risk factor strings).
    """
    text = " ".join(filter(None, [title, description, diff_text or ""]))
    factors: list[str] = []
    score = 0.0

    for pattern in _HIGH_RISK_PATTERNS:
        if pattern.search(text):
            factors.append(f"High-risk pattern detected: {pattern.pattern}")
            score += 0.25

    for pattern in _MEDIUM_RISK_PATTERNS:
        if pattern.search(text):
            factors.append(f"Medium-risk pattern detected: {pattern.pattern}")
            score += 0.1

    # Large PRs are inherently riskier
    if files_changed > 20:
        factors.append(f"Large PR: {files_changed} files changed")
        score += 0.15
    elif files_changed > 10:
        factors.append(f"Medium-sized PR: {files_changed} files changed")
        score += 0.05

    return min(1.0, score), factors


def _parse_changed_files_from_diff(diff_text: str) -> list[str]:
    """Extract changed file paths from a unified diff."""
    files: set[str] = set()
    for line in diff_text.splitlines():
        if line.startswith("--- a/") or line.startswith("+++ b/"):
            path = line[6:]
            if path and path != "/dev/null":
                files.add(path)
        elif line.startswith("diff --git"):
            parts = line.split()
            if len(parts) >= 4:
                files.add(parts[3][2:])  # strip "b/"
    return sorted(files)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def create_pull_request(db: Session, pr_in: PullRequestCreate) -> PullRequest:
    """Create a PullRequest and its associated MemoryEntry."""
    # Derive changed files from diff if not supplied
    changed_files = pr_in.changed_files
    if changed_files is None and pr_in.diff_text:
        changed_files = _parse_changed_files_from_diff(pr_in.diff_text)

    safe_desc = (pr_in.description or "")[:5000]

    # Build MemoryEntry content
    content_parts = [
        f"PR #{pr_in.pr_number}: {pr_in.title}",
        f"Author: {pr_in.author or 'unknown'}",
        f"Branch: {pr_in.source_branch or '?'} → {pr_in.target_branch or '?'}",
    ]
    if safe_desc:
        content_parts.append(f"Description: {safe_desc[:500]}")
    if changed_files:
        content_parts.append(f"Files: {', '.join((changed_files or [])[:10])}")

    entry = MemoryEntry(
        organization_id=pr_in.organization_id,
        memory_type=MemoryType.artifact,
        title=f"PR #{pr_in.pr_number}: {pr_in.title}",
        content="\n".join(content_parts),
        meta={
            "source": "pull_request",
            "pr_number": pr_in.pr_number,
            "author": pr_in.author,
            "source_branch": pr_in.source_branch,
            "target_branch": pr_in.target_branch,
        },
    )
    db.add(entry)
    db.flush()

    pr = PullRequest(
        organization_id=pr_in.organization_id,
        repository_id=pr_in.repository_id,
        memory_entry_id=entry.id,
        pr_number=pr_in.pr_number,
        title=pr_in.title,
        description=pr_in.description,
        author=pr_in.author,
        source_branch=pr_in.source_branch,
        target_branch=pr_in.target_branch,
        status=pr_in.status,
        diff_text=pr_in.diff_text,
        changed_files=changed_files,
        files_changed=pr_in.files_changed or len(changed_files or []),
    )
    db.add(pr)
    db.commit()
    db.refresh(pr)

    # Entity extraction
    entity_text = " ".join(filter(None, [pr_in.title, pr_in.description or "", pr_in.diff_text or ""]))
    raw_entities = extract_entities(entity_text)
    for raw_entity in raw_entities:
        entity = get_or_create_entity(
            db,
            organization_id=pr_in.organization_id,
            entity_type=raw_entity.entity_type,
            name=raw_entity.name,
        )
        try:
            db.add(MemoryEntity(memory_entry_id=entry.id, entity_id=entity.id))
            db.commit()
        except IntegrityError:
            db.rollback()

    return pr


def get_pull_request_by_id(db: Session, pr_id: UUID) -> PullRequest | None:
    return db.scalar(select(PullRequest).where(PullRequest.id == pr_id))


def get_pull_requests_by_org(
    db: Session, organization_id: UUID, skip: int = 0, limit: int = 100
) -> Sequence[PullRequest]:
    stmt = (
        select(PullRequest)
        .where(PullRequest.organization_id == organization_id)
        .order_by(PullRequest.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return db.scalars(stmt).all()


def get_reviews_for_pr(
    db: Session, pull_request_id: UUID
) -> Sequence[PullRequestReview]:
    return db.scalars(
        select(PullRequestReview)
        .where(PullRequestReview.pull_request_id == pull_request_id)
        .order_by(PullRequestReview.created_at.desc())
    ).all()


def review_pull_request(
    db: Session,
    pr_id: UUID,
    organization_id: UUID,
    top_k: int = 5,
) -> PullRequestReview:
    """Generate an AI-assisted review for a PullRequest.

    1. Compute deterministic risk score.
    2. Retrieve related memories via HybridRetriever.
    3. Build suggestions from context.
    4. Optionally call Granite for a summary.
    """
    pr = get_pull_request_by_id(db, pr_id)
    if pr is None or pr.organization_id != organization_id:
        raise ValueError(f"PullRequest {pr_id} not found in org {organization_id}")

    risk_score, risk_factors = _compute_risk_score(
        title=pr.title,
        description=pr.description,
        diff_text=pr.diff_text,
        files_changed=pr.files_changed,
    )

    # Retrieve historical context
    query = f"PR review: {pr.title} {pr.description or ''}"
    retriever = HybridRetriever(
        db=db,
        organization_id=organization_id,
        embedding_provider=StubEmbeddingProvider(),
        top_k=top_k,
    )
    hybrid_results = retriever.retrieve(query)
    retrieved_entries = [r.memory for r in hybrid_results]

    # Build suggestions from risk factors and retrieved context
    suggestions: list[str] = []
    for factor in risk_factors:
        suggestions.append(f"Review carefully: {factor}")

    if retrieved_entries:
        suggestions.append(
            f"Found {len(retrieved_entries)} related historical memories — "
            "check for prior decisions affecting this change."
        )

    # Build citations
    citations = [
        {"memory_id": str(r.memory.id), "title": r.memory.title, "score": r.score}
        for r in hybrid_results
    ]

    # Generate summary via Granite (safe fallback)
    summary = None
    try:
        context_text = _format_context(query, retrieved_entries)
        prompt = build_prompt(
            question=f"Summarise this pull request and identify key risks:\n{pr.title}\n{pr.description or ''}",
            context_text=context_text,
            entries=retrieved_entries,
        )
        gen_provider = get_generation_provider()
        summary = gen_provider.generate(prompt)
    except Exception:
        summary = f"PR #{pr.pr_number}: {pr.title}. Risk score: {risk_score:.2f}."

    review = PullRequestReview(
        organization_id=organization_id,
        pull_request_id=pr_id,
        summary=summary,
        risk_score=risk_score,
        risk_factors=risk_factors,
        suggestions=suggestions,
        citations=citations,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_pr_risk(
    db: Session,
    pr_id: UUID,
    organization_id: UUID,
) -> PRRiskResponse:
    """Return a deterministic risk analysis for a PR without calling Granite."""
    pr = get_pull_request_by_id(db, pr_id)
    if pr is None or pr.organization_id != organization_id:
        raise ValueError(f"PullRequest {pr_id} not found")

    risk_score, risk_factors = _compute_risk_score(
        title=pr.title,
        description=pr.description,
        diff_text=pr.diff_text,
        files_changed=pr.files_changed,
    )

    if risk_score >= 0.6:
        level = "HIGH"
    elif risk_score >= 0.3:
        level = "MEDIUM"
    else:
        level = "LOW"

    explanation = (
        f"Risk level: {level} ({risk_score:.2f}). "
        f"Detected {len(risk_factors)} risk factor(s)."
    )
    return PRRiskResponse(
        pull_request_id=pr_id,
        risk_score=risk_score,
        risk_factors=risk_factors,
        explanation=explanation,
    )
