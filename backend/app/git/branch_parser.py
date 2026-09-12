"""Git Branch and Tag Parser (AI-004)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.git.git_models import GitBranchInfo, GitTagInfo


def parse_git_branch(branch: Any, active_branch_name: str | None = None) -> GitBranchInfo:
    """Parse a GitPython Head / RemoteReference into GitBranchInfo."""
    name = str(branch.name)
    sha = branch.commit.hexsha if hasattr(branch, "commit") and branch.commit else ""
    is_active = (name == active_branch_name)
    
    is_remote = False
    try:
        if hasattr(branch, "is_remote") and callable(branch.is_remote):
            is_remote = branch.is_remote()
    except Exception:
        pass
    if not is_remote and (name.startswith("origin/") or name.startswith("remotes/")):
        is_remote = True

    tracking = None
    try:
        if hasattr(branch, "tracking_branch") and callable(branch.tracking_branch):
            tb = branch.tracking_branch()
            if tb is not None:
                tracking = str(tb.name)
    except Exception:
        pass

    return GitBranchInfo(
        name=name,
        commit_sha=sha,
        is_active=is_active,
        is_remote=is_remote,
        tracking_branch=tracking,
    )


def parse_git_tag(tag: Any) -> GitTagInfo:
    """Parse a GitPython TagReference into GitTagInfo."""
    name = str(tag.name)
    tagger_name = None
    tagger_email = None
    tagged_at = None
    message = None
    
    # Check if tag is annotated or lightweight
    if hasattr(tag, "tag") and tag.tag is not None:
        tag_obj = tag.tag
        if hasattr(tag_obj, "tagger") and tag_obj.tagger:
            tagger_name = str(tag_obj.tagger.name)
            tagger_email = str(tag_obj.tagger.email)
        if hasattr(tag_obj, "tagged_date") and tag_obj.tagged_date:
            try:
                tagged_at = datetime.fromtimestamp(tag_obj.tagged_date, tz=timezone.utc)
            except Exception:
                pass
        if hasattr(tag_obj, "message") and tag_obj.message:
            message = str(tag_obj.message).strip()
        commit_sha = tag_obj.object.hexsha if hasattr(tag_obj, "object") else tag.commit.hexsha
    else:
        commit_sha = tag.commit.hexsha if hasattr(tag, "commit") else ""

    return GitTagInfo(
        name=name,
        commit_sha=commit_sha,
        tagger_name=tagger_name,
        tagger_email=tagger_email,
        tagged_at=tagged_at,
        message=message,
    )
