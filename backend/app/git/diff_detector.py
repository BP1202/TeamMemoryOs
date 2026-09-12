"""Git Diff Detector for Incremental Change Tracking (AI-004)."""
from __future__ import annotations

import logging
from typing import Any

from app.git.git_models import FileChangeType, GitDiffEntry, GitDiffSummary

logger = logging.getLogger(__name__)


def _map_change_type(change_type_str: str) -> FileChangeType:
    """Map Git change code to FileChangeType enum."""
    mapping = {
        "A": FileChangeType.ADDED,
        "M": FileChangeType.MODIFIED,
        "D": FileChangeType.DELETED,
        "R": FileChangeType.RENAMED,
        "C": FileChangeType.COPIED,
        "U": FileChangeType.UNTRACKED,
    }
    return mapping.get(change_type_str.upper(), FileChangeType.UNKNOWN)


def detect_diff(
    repo_obj: Any,
    base_ref: str | None = None,
    target_ref: str | None = None,
) -> GitDiffSummary:
    """Detect diff entries between two commits/refs in a GitPython Repo object.
    
    If base_ref is None, compares target_ref (or HEAD) against its parent (or root if initial).
    If target_ref is None, compares base_ref to HEAD or working tree.
    """
    entries: list[GitDiffEntry] = []
    total_ins = 0
    total_del = 0

    try:
        if base_ref and target_ref:
            base_commit = repo_obj.commit(base_ref)
            target_commit = repo_obj.commit(target_ref)
            diff_index = base_commit.diff(target_commit)
        elif base_ref and not target_ref:
            # Diff base_commit against current HEAD or working directory
            base_commit = repo_obj.commit(base_ref)
            diff_index = base_commit.diff(None)  # compares against working tree
        elif target_ref:
            target_commit = repo_obj.commit(target_ref)
            if target_commit.parents:
                diff_index = target_commit.parents[0].diff(target_commit)
            else:
                # Root commit: diff against empty tree
                diff_index = target_commit.diff(repo_obj.tree("4b825dc642cb6eb9a060e54bf8d69288fbee4904"))
        else:
            # Working tree changes against HEAD
            diff_index = repo_obj.head.commit.diff(None)

        for d in diff_index:
            change_code = d.change_type
            change_enum = _map_change_type(change_code)
            
            # File paths
            file_path = d.b_path if d.b_path else (d.a_path or "")
            old_path = d.a_path if change_enum in (FileChangeType.RENAMED, FileChangeType.COPIED) else None
            
            # Blob SHAs
            old_blob_sha = d.a_blob.hexsha if d.a_blob else None
            new_blob_sha = d.b_blob.hexsha if d.b_blob else None

            # Calculate insertions / deletions if available
            ins = 0
            dels = 0
            is_bin = False
            try:
                # GitPython diff stats if diff text is readable
                if d.diff:
                    diff_text = d.diff.decode("utf-8", errors="replace")
                    for line in diff_text.splitlines():
                        if line.startswith("+") and not line.startswith("+++"):
                            ins += 1
                        elif line.startswith("-") and not line.startswith("---"):
                            dels += 1
            except Exception:
                pass

            entries.append(
                GitDiffEntry(
                    file_path=file_path,
                    old_path=old_path,
                    change_type=change_enum,
                    insertions=ins,
                    deletions=dels,
                    old_blob_sha=old_blob_sha,
                    new_blob_sha=new_blob_sha,
                    is_binary=is_bin,
                )
            )
            total_ins += ins
            total_del += dels

    except Exception as e:
        logger.warning(f"Error computing diff between {base_ref} and {target_ref}: {e}")

    return GitDiffSummary(
        base_ref=base_ref,
        target_ref=target_ref,
        changed_files=entries,
        total_files=len(entries),
        total_insertions=total_ins,
        total_deletions=total_del,
    )


def detect_working_tree_diff(repo_obj: Any) -> GitDiffSummary:
    """Detect uncommitted changes (staged, unstaged, untracked) in working directory."""
    entries: list[GitDiffEntry] = []
    total_ins = 0
    total_del = 0

    try:
        # 1. Staged & unstaged changes against HEAD
        if repo_obj.heads:
            head_commit = repo_obj.head.commit
            # Unstaged changes (working tree vs index)
            for d in repo_obj.index.diff(None):
                entries.append(
                    GitDiffEntry(
                        file_path=d.a_path or d.b_path or "",
                        change_type=_map_change_type(d.change_type),
                    )
                )
            # Staged changes (index vs HEAD)
            for d in head_commit.diff():
                entries.append(
                    GitDiffEntry(
                        file_path=d.b_path or d.a_path or "",
                        change_type=_map_change_type(d.change_type),
                    )
                )
        
        # 2. Untracked files
        for untracked in repo_obj.untracked_files:
            entries.append(
                GitDiffEntry(
                    file_path=untracked,
                    change_type=FileChangeType.UNTRACKED,
                )
            )

    except Exception as e:
        logger.warning(f"Error detecting working tree diff: {e}")

    # Deduplicate by file_path
    unique_entries = {}
    for entry in entries:
        unique_entries[entry.file_path] = entry

    final_entries = list(unique_entries.values())
    return GitDiffSummary(
        base_ref="HEAD",
        target_ref="WORKING_TREE",
        changed_files=final_entries,
        total_files=len(final_entries),
        total_insertions=total_ins,
        total_deletions=total_del,
    )
