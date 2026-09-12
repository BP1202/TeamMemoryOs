"""Git Commit Parser and Metadata Extractor (AI-004)."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.git.git_models import GitCommitInfo

# Secret filter patterns — prevent credentials from leaking into memory/embeddings
_SECRET_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"(?:password|passwd|pwd)\s*[:=]\s*\S+",
        r"(?:secret|token|api_key|apikey|bearer)\s*[:=]\s*\S+",
        r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC )?PRIVATE KEY-----",
        r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----",
        r"(?:aws_access_key|aws_secret|aws_key)[^=]*=\s*\S+",
        r"ghp_[0-9a-zA-Z]{36}",
        r"glpat-[0-9a-zA-Z\-_]{20}",
    ]
]

# Conventional commit regex: e.g. "feat(auth): add login endpoint", "fix: resolve memory leak"
_CONVENTIONAL_REGEX = re.compile(
    r"^(?P<type>feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(?:\((?P<scope>[^\)]+)\))?!?:",
    re.IGNORECASE,
)

# Issue / ticket references: e.g. "#123", "AI-004", "PROJ-982"
_ISSUE_REGEX = re.compile(r"(?:#\d+|[A-Z]{2,10}-\d+)")


def filter_secrets(text: str) -> str:
    """Replace likely secret values and credentials with [REDACTED]."""
    if not text:
        return text
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def extract_conventional_type(message: str) -> str | None:
    """Extract conventional commit type if present."""
    if not message:
        return None
    first_line = message.strip().splitlines()[0]
    match = _CONVENTIONAL_REGEX.match(first_line)
    if match:
        return match.group("type").lower()
    return None


def extract_issue_references(text: str) -> list[str]:
    """Extract issue or ticket IDs from text."""
    if not text:
        return []
    matches = _ISSUE_REGEX.findall(text)
    # Deduplicate preserving order
    seen = set()
    result = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            result.append(m)
    return result


def parse_gitpython_commit(commit: Any) -> GitCommitInfo:
    """Parse a GitPython Commit object into GitCommitInfo with sanitized content."""
    sha = commit.hexsha
    author_name = str(commit.author.name) if commit.author else "unknown"
    author_email = str(commit.author.email) if commit.author else ""
    
    # Handle timestamp timezone safely
    try:
        committed_at = datetime.fromtimestamp(commit.committed_date, tz=timezone.utc)
    except Exception:
        committed_at = datetime.now(timezone.utc)

    raw_message = (commit.message or "").strip()
    safe_message = filter_secrets(raw_message)
    summary = safe_message.splitlines()[0] if safe_message else ""

    parents = [p.hexsha for p in commit.parents] if hasattr(commit, "parents") else []

    # Get stats safely
    files_changed = 0
    insertions = 0
    deletions = 0
    changed_files: list[str] = []

    try:
        stats = commit.stats
        files_changed = stats.total.get("files", 0)
        insertions = stats.total.get("insertions", 0)
        deletions = stats.total.get("deletions", 0)
        changed_files = list(stats.files.keys())
    except Exception:
        pass

    conv_type = extract_conventional_type(raw_message)
    issues = extract_issue_references(raw_message)

    return GitCommitInfo(
        commit_sha=sha,
        author_name=author_name,
        author_email=author_email,
        committed_at=committed_at,
        message=safe_message,
        summary=summary,
        parent_shas=parents,
        files_changed=files_changed,
        insertions=insertions,
        deletions=deletions,
        changed_files=changed_files,
        conventional_type=conv_type,
        issue_references=issues,
    )
