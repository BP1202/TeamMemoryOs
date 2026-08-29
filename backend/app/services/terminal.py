"""Terminal Memory Copilot service (Milestone 6.3).

Pipeline:
1. Parse raw terminal output to extract commands and errors.
2. Classify errors deterministically (regex + heuristics).
3. Ingest errors as MemoryEntry records.
4. Retrieve historical fixes via HybridRetriever.
5. Build resolution suggestions from retrieved context.
"""
from __future__ import annotations

import re
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.graph.hybrid_retriever import HybridRetriever
from app.memory.embedding_provider import StubEmbeddingProvider
from app.models.entity import MemoryEntity
from app.models.memory_entry import MemoryEntry, MemoryType
from app.models.terminal import ErrorSeverity, TerminalError, TerminalSession
from app.schemas.terminal import (
    TerminalFixResult,
    TerminalSearchResponse,
    TerminalSessionCreate,
    TerminalUploadResponse,
)
from app.services.entity import get_or_create_entity
from app.services.entity_extraction import extract_entities
from app.models.entity import EntityType


# ---------------------------------------------------------------------------
# Error classification patterns
# ---------------------------------------------------------------------------

_ERROR_CLASSIFIERS: list[tuple[re.Pattern, str, ErrorSeverity]] = [
    (re.compile(r"\bTraceback \(most recent call last\)", re.IGNORECASE), "PythonException", ErrorSeverity.high),
    (re.compile(r"\bImportError\b|\bModuleNotFoundError\b", re.IGNORECASE), "ImportError", ErrorSeverity.medium),
    (re.compile(r"\bConnectionRefusedError\b|\bconnection refused\b", re.IGNORECASE), "ConnectionRefused", ErrorSeverity.high),
    (re.compile(r"\bPermissionError\b|\bpermission denied\b", re.IGNORECASE), "PermissionError", ErrorSeverity.medium),
    (re.compile(r"\bFileNotFoundError\b|\bNo such file or directory\b", re.IGNORECASE), "FileNotFound", ErrorSeverity.low),
    (re.compile(r"\bSyntaxError\b", re.IGNORECASE), "SyntaxError", ErrorSeverity.medium),
    (re.compile(r"\bTypeError\b", re.IGNORECASE), "TypeError", ErrorSeverity.medium),
    (re.compile(r"\bValueError\b", re.IGNORECASE), "ValueError", ErrorSeverity.low),
    (re.compile(r"\bKeyError\b", re.IGNORECASE), "KeyError", ErrorSeverity.low),
    (re.compile(r"\bAttributeError\b", re.IGNORECASE), "AttributeError", ErrorSeverity.low),
    (re.compile(r"\bAssertionError\b|\bAssertionFailed\b", re.IGNORECASE), "AssertionError", ErrorSeverity.medium),
    (re.compile(r"\bOOM\b|\bout of memory\b", re.IGNORECASE), "OutOfMemory", ErrorSeverity.critical),
    (re.compile(r"\bsegmentation fault\b|\bsigsegv\b", re.IGNORECASE), "SegFault", ErrorSeverity.critical),
    (re.compile(r"\berror\b.*\bECONNREFUSED\b", re.IGNORECASE), "NetworkError", ErrorSeverity.high),
    (re.compile(r"\bnpm ERR\b|\byarn error\b", re.IGNORECASE), "PackageError", ErrorSeverity.medium),
    (re.compile(r"\bfatal:\s", re.IGNORECASE), "GitFatal", ErrorSeverity.high),
    (re.compile(r"\bcompilation failed\b|\bbuild failed\b", re.IGNORECASE), "BuildError", ErrorSeverity.high),
    (re.compile(r"\btest.*failed\b|\bfailure.*test\b", re.IGNORECASE), "TestFailure", ErrorSeverity.medium),
    (re.compile(r"\berror\b", re.IGNORECASE), "GenericError", ErrorSeverity.low),
]


def _extract_error_message(raw_output: str, pattern: re.Pattern) -> str:
    """Extract the line containing the error message from raw output."""
    match = pattern.search(raw_output)
    if match:
        start = raw_output.rfind("\n", 0, match.start()) + 1
        end = raw_output.find("\n", match.end())
        if end == -1:
            end = len(raw_output)
        return raw_output[start:end].strip()[:500]
    return ""


def _parse_command(raw_output: str) -> str | None:
    """Try to extract the first shell command from terminal output."""
    # Look for common shell prompt patterns
    prompt_pattern = re.compile(r"(?:^|\n)\s*(?:\$|#|>)\s+(.+)")
    match = prompt_pattern.search(raw_output)
    if match:
        return match.group(1).strip()[:500]
    # Fallback: first non-empty line
    for line in raw_output.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped[:500]
    return None


def _classify_errors(raw_output: str) -> list[tuple[str, str, ErrorSeverity]]:
    """Return list of (error_type, error_message, severity) found in output."""
    found: list[tuple[str, str, ErrorSeverity]] = []
    seen_types: set[str] = set()
    for pattern, error_type, severity in _ERROR_CLASSIFIERS:
        if error_type in seen_types:
            continue
        if pattern.search(raw_output):
            msg = _extract_error_message(raw_output, pattern)
            if msg:
                found.append((error_type, msg, severity))
                seen_types.add(error_type)
    return found


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def create_terminal_session(
    db: Session,
    session_in: TerminalSessionCreate,
    user_id: UUID | None = None,
) -> TerminalSession:
    session = TerminalSession(
        organization_id=session_in.organization_id,
        submitted_by_user_id=user_id,
        raw_output=session_in.raw_output,
        command=session_in.command or _parse_command(session_in.raw_output),
        working_directory=session_in.working_directory,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def ingest_terminal_session(
    db: Session,
    session: TerminalSession,
) -> TerminalUploadResponse:
    """Parse errors from a session, ingest them as MemoryEntries."""
    errors = _classify_errors(session.raw_output)
    ingested = 0
    memory_entries_created = 0

    for error_type, error_message, severity in errors:
        # Create MemoryEntry for the error
        content = (
            f"Terminal error [{error_type}]: {error_message}\n"
            f"Command: {session.command or 'unknown'}\n"
            f"Severity: {severity.value}"
        )
        entry = MemoryEntry(
            organization_id=session.organization_id,
            memory_type=MemoryType.context,
            title=f"Error: {error_type} — {error_message[:60]}",
            content=content,
            meta={
                "source": "terminal",
                "error_type": error_type,
                "severity": severity.value,
                "session_id": str(session.id),
                "command": session.command,
            },
        )
        db.add(entry)
        db.flush()
        memory_entries_created += 1

        # Retrieve historical fixes
        retriever = HybridRetriever(
            db=db,
            organization_id=session.organization_id,
            embedding_provider=StubEmbeddingProvider(),
            top_k=3,
        )
        hybrid_results = retriever.retrieve(f"{error_type}: {error_message}")
        suggested_fixes = [
            {
                "memory_id": str(r.memory.id),
                "title": r.memory.title or "",
                "content": r.memory.content[:300],
                "score": r.score,
            }
            for r in hybrid_results
        ]

        terminal_error = TerminalError(
            organization_id=session.organization_id,
            session_id=session.id,
            memory_entry_id=entry.id,
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            suggested_fixes=suggested_fixes,
        )
        db.add(terminal_error)

        # Entity extraction
        raw_entities = extract_entities(f"{error_type} {error_message} {session.command or ''}")
        for raw_entity in raw_entities:
            entity = get_or_create_entity(
                db,
                organization_id=session.organization_id,
                entity_type=raw_entity.entity_type,
                name=raw_entity.name,
            )
            try:
                db.add(MemoryEntity(memory_entry_id=entry.id, entity_id=entity.id))
                db.flush()
            except IntegrityError:
                db.rollback()

        ingested += 1

    db.commit()

    return TerminalUploadResponse(
        session_id=session.id,
        errors_found=len(errors),
        errors_ingested=ingested,
        memory_entries_created=memory_entries_created,
    )


def search_similar_failures(
    db: Session,
    organization_id: UUID,
    error_message: str,
    top_k: int = 5,
) -> TerminalSearchResponse:
    """Search organizational memory for similar terminal failures."""
    retriever = HybridRetriever(
        db=db,
        organization_id=organization_id,
        embedding_provider=StubEmbeddingProvider(),
        top_k=top_k,
    )
    hybrid_results = retriever.retrieve(error_message)

    fixes: list[TerminalFixResult] = []
    for result in hybrid_results:
        meta = result.memory.meta or {}
        if meta.get("source") == "terminal":
            fixes.append(
                TerminalFixResult(
                    error_type=meta.get("error_type", "Unknown"),
                    error_message=result.memory.title or "",
                    fix_description=result.memory.content[:500],
                    confidence=result.score,
                    source_session_id=None,
                )
            )

    explanation = (
        f"Found {len(fixes)} historical terminal error fix(es) matching '{error_message[:100]}'."
        if fixes
        else "No matching historical fixes found."
    )
    return TerminalSearchResponse(
        query=error_message,
        organization_id=organization_id,
        fixes=fixes,
        explanation=explanation,
    )


def get_sessions_by_org(
    db: Session,
    organization_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[TerminalSession]:
    return db.scalars(
        select(TerminalSession)
        .where(TerminalSession.organization_id == organization_id)
        .order_by(TerminalSession.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()
