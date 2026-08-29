"""PR Guardian API — Milestone 6.2.

Routes:
* POST /git/pull-requests/              — Create PR
* GET  /git/pull-requests/              — List PRs
* POST /git/pull-requests/{id}/review   — Review PR
* GET  /git/pull-requests/{id}/risk     — Explain PR risks
* GET  /git/pull-requests/{id}/reviews  — List reviews
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.pull_request import (
    PRReviewRequest,
    PRRiskResponse,
    PullRequestCreate,
    PullRequestRead,
    PullRequestReviewRead,
)
from app.services.pull_request import (
    create_pull_request,
    get_pr_risk,
    get_pull_request_by_id,
    get_pull_requests_by_org,
    get_reviews_for_pr,
    review_pull_request,
)

router = APIRouter()


@router.post("/pull-requests/", response_model=PullRequestRead, status_code=status.HTTP_201_CREATED)
def create_pr(
    body: PullRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create and ingest a pull request into organizational memory."""
    try:
        return create_pull_request(db, body)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pull request with this number already exists for this repository.",
        )


@router.get("/pull-requests/", response_model=list[PullRequestRead])
def list_prs(
    organization_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List pull requests for an organisation."""
    return get_pull_requests_by_org(db, organization_id, skip=skip, limit=limit)


@router.post("/pull-requests/{pr_id}/review", response_model=PullRequestReviewRead, status_code=status.HTTP_201_CREATED)
def review_pr(
    pr_id: UUID,
    body: PRReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate an AI-assisted review for a pull request."""
    pr = get_pull_request_by_id(db, pr_id)
    if pr is None:
        raise HTTPException(status_code=404, detail="Pull request not found.")
    try:
        return review_pull_request(
            db,
            pr_id=pr_id,
            organization_id=pr.organization_id,
            top_k=body.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/pull-requests/{pr_id}/risk", response_model=PRRiskResponse)
def explain_pr_risks(
    pr_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a deterministic risk analysis for a pull request."""
    pr = get_pull_request_by_id(db, pr_id)
    if pr is None:
        raise HTTPException(status_code=404, detail="Pull request not found.")
    try:
        return get_pr_risk(db, pr_id=pr_id, organization_id=pr.organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/pull-requests/{pr_id}/reviews", response_model=list[PullRequestReviewRead])
def list_reviews(
    pr_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all reviews for a pull request."""
    pr = get_pull_request_by_id(db, pr_id)
    if pr is None:
        raise HTTPException(status_code=404, detail="Pull request not found.")
    return get_reviews_for_pr(db, pr_id)
