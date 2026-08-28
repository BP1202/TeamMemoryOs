"""Engineering Conversation Engine API — Milestone 6.5.

Routes:
* POST /engineering/chat    — Engineering assistant chat
* POST /engineering/debug   — Debug mode
* POST /engineering/review  — PR review mode
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.engineering import (
    DebugRequest,
    EngineeringChatRequest,
    EngineeringResponse,
    ReviewRequest,
)
from app.services.engineering import (
    run_engineering_chat,
    run_engineering_debug,
    run_engineering_review,
)

router = APIRouter()


@router.post("/chat", response_model=EngineeringResponse)
def engineering_chat(
    body: EngineeringChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI Engineering Copilot — unified engineering assistant chat.

    Routes the question through the appropriate prompt mode and returns a
    structured response with citations, graph path, confidence, and suggested actions.
    """
    return run_engineering_chat(db, body)


@router.post("/debug", response_model=EngineeringResponse)
def engineering_debug(
    body: DebugRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Debug mode — analyse terminal errors and stack traces using organizational memory."""
    return run_engineering_debug(db, body)


@router.post("/review", response_model=EngineeringResponse)
def engineering_review(
    body: ReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """PR Review mode — review pull request diffs using historical engineering context."""
    return run_engineering_review(db, body)
