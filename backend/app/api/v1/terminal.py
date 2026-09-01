"""Terminal Memory Copilot API — Milestone 6.3.

Routes:
* POST /terminal/sessions/          — Upload terminal session
* GET  /terminal/sessions/          — List sessions
* POST /terminal/search             — Search similar failures
* GET  /terminal/sessions/{id}/errors — Get errors for a session
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.terminal import (
    TerminalSearchRequest,
    TerminalSearchResponse,
    TerminalSessionCreate,
    TerminalSessionRead,
    TerminalUploadResponse,
    TerminalErrorRead,
)
from app.services.terminal import (
    create_terminal_session,
    get_sessions_by_org,
    ingest_terminal_session,
    search_similar_failures,
)
from sqlalchemy import select
from app.models.terminal import TerminalError

router = APIRouter()


@router.post("/sessions/", response_model=TerminalUploadResponse, status_code=status.HTTP_201_CREATED)
def upload_session(
    body: TerminalSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a terminal session for error classification and memory ingestion."""
    session = create_terminal_session(db, body, user_id=current_user.id)
    return ingest_terminal_session(db, session)


@router.get("/sessions/", response_model=list[TerminalSessionRead])
def list_sessions(
    organization_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List terminal sessions for an organisation."""
    return get_sessions_by_org(db, organization_id, skip=skip, limit=limit)


@router.post("/search", response_model=TerminalSearchResponse)
def search_failures(
    body: TerminalSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search organizational memory for similar terminal failures."""
    return search_similar_failures(
        db,
        organization_id=body.organization_id,
        error_message=body.error_message,
        top_k=body.top_k,
    )


@router.get("/sessions/{session_id}/errors", response_model=list[TerminalErrorRead])
def get_session_errors(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all classified errors from a terminal session."""
    errors = db.scalars(
        select(TerminalError).where(TerminalError.session_id == session_id)
    ).all()
    return list(errors)
