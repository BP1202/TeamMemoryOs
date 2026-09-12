"""Git Repository Abstraction and Operations Wrapper (AI-004)."""
from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import git

from app.git.branch_parser import parse_git_branch, parse_git_tag
from app.git.commit_parser import parse_gitpython_commit
from app.git.diff_detector import detect_diff, detect_working_tree_diff
from app.git.git_models import (
    GitBranchInfo,
    GitCommitInfo,
    GitDiffSummary,
    GitTagInfo,
    RepositoryHealth,
)


class GitRepositoryWrapper:
    """High-level abstraction for interacting with local Git repositories."""

    def __init__(self, repo_path: str | Path):
        self.path = Path(repo_path).resolve()
        self._repo: git.Repo | None = None
        self._init_repo()

    def _init_repo(self) -> None:
        """Initialize GitPython Repo instance if path is a valid repository."""
        try:
            if self.path.exists():
                self._repo = git.Repo(self.path, search_parent_directories=True)
        except (git.InvalidGitRepositoryError, git.NoSuchPathError):
            self._repo = None
        except Exception:
            self._repo = None

    @property
    def is_valid(self) -> bool:
        """Check whether the repository is a valid Git repository."""
        return self._repo is not None

    @property
    def repo(self) -> git.Repo:
        """Access underlying GitPython Repo instance (raises if invalid)."""
        if self._repo is None:
            raise ValueError(f"Not a valid Git repository at {self.path}")
        return self._repo

    def get_default_branch(self) -> str:
        """Attempt to detect default branch ('main', 'master', or active)."""
        if not self.is_valid:
            return "main"
        try:
            if not self._repo.heads:
                return "main"
            for candidate in ("main", "master", "develop", "dev"):
                if candidate in self._repo.heads:
                    return candidate
            if self._repo.head.is_valid():
                return self._repo.active_branch.name
            return self._repo.heads[0].name
        except Exception:
            return "main"

    def get_current_branch(self) -> str | None:
        """Get currently active branch name (or None if detached)."""
        if not self.is_valid:
            return None
        try:
            if not self._repo.head.is_detached:
                return self._repo.active_branch.name
        except Exception:
            pass
        return None

    def get_branches(self) -> list[GitBranchInfo]:
        """List all local and remote branches."""
        if not self.is_valid:
            return []
        branches: list[GitBranchInfo] = []
        active_name = self.get_current_branch()
        try:
            for head in self._repo.heads:
                branches.append(parse_git_branch(head, active_branch_name=active_name))
            for remote in self._repo.remotes:
                for ref in remote.refs:
                    branches.append(parse_git_branch(ref, active_branch_name=active_name))
        except Exception:
            pass
        return branches

    def get_tags(self) -> list[GitTagInfo]:
        """List all tags in the repository."""
        if not self.is_valid:
            return []
        tags: list[GitTagInfo] = []
        try:
            for tag in self._repo.tags:
                tags.append(parse_git_tag(tag))
        except Exception:
            pass
        return tags

    def get_commits(
        self,
        branch_or_ref: str | None = None,
        since_sha: str | None = None,
        max_count: int = 100,
        skip: int = 0,
    ) -> list[GitCommitInfo]:
        """Get commit history starting from ref, stopping if since_sha is reached."""
        if not self.is_valid:
            return []
        ref = branch_or_ref or self.get_default_branch()
        results: list[GitCommitInfo] = []
        try:
            commits = list(self._repo.iter_commits(ref, max_count=max_count, skip=skip))
            for commit in commits:
                if since_sha and commit.hexsha == since_sha:
                    break
                results.append(parse_gitpython_commit(commit))
        except Exception:
            pass
        return results

    def get_commit_by_sha(self, sha: str) -> GitCommitInfo | None:
        """Fetch details for a specific commit SHA."""
        if not self.is_valid:
            return None
        try:
            commit = self._repo.commit(sha)
            return parse_gitpython_commit(commit)
        except Exception:
            return None

    def get_diff(
        self,
        base_ref: str | None = None,
        target_ref: str | None = None,
    ) -> GitDiffSummary:
        """Compute diff summary between two commits or against working tree."""
        if not self.is_valid:
            return GitDiffSummary()
        return detect_diff(self._repo, base_ref=base_ref, target_ref=target_ref)

    def get_working_tree_diff(self) -> GitDiffSummary:
        """Compute uncommitted working tree diff."""
        if not self.is_valid:
            return GitDiffSummary()
        return detect_working_tree_diff(self._repo)

    def get_file_content(self, file_path: str, ref: str | None = None) -> str | None:
        """Get file content at revision, or from disk if ref is None."""
        if ref and self.is_valid:
            try:
                commit = self._repo.commit(ref)
                blob = commit.tree / file_path
                return blob.data_stream.read().decode("utf-8", errors="replace")
            except Exception:
                return None

        # Read from disk
        target_file = self.path / file_path
        if target_file.is_file():
            try:
                return target_file.read_text(encoding="utf-8", errors="replace")
            except Exception:
                return None
        return None

    def get_health(self) -> RepositoryHealth:
        """Inspect and return repository health metrics."""
        if not self.is_valid:
            return RepositoryHealth(
                is_valid_git=False,
                path=str(self.path),
                default_branch="main",
                error=f"Directory '{self.path}' is not a valid Git repository.",
            )

        total_commits = 0
        last_sha = None
        last_date = None
        last_msg = None
        is_clean = True
        uncommitted = 0

        try:
            if self._repo.heads:
                head_commit = self._repo.head.commit
                last_sha = head_commit.hexsha
                last_date = datetime.fromtimestamp(head_commit.committed_date, tz=timezone.utc)
                last_msg = head_commit.message.strip().splitlines()[0] if head_commit.message else ""
                total_commits = sum(1 for _ in self._repo.iter_commits(max_count=1000))
                
                is_clean = not self._repo.is_dirty(untracked_files=True)
                wt_diff = self.get_working_tree_diff()
                uncommitted = wt_diff.total_files
        except Exception:
            pass

        # Calculate approximate repo storage size
        storage_size = 0
        try:
            dot_git = self.path / ".git"
            if dot_git.exists():
                for root, _, files in os.walk(dot_git):
                    for f in files:
                        storage_size += os.path.getsize(os.path.join(root, f))
        except Exception:
            pass

        return RepositoryHealth(
            is_valid_git=True,
            path=str(self.path),
            default_branch=self.get_default_branch(),
            current_branch=self.get_current_branch(),
            total_commits=total_commits,
            total_branches=len(self.get_branches()),
            total_tags=len(self.get_tags()),
            is_clean=is_clean,
            uncommitted_changes=uncommitted,
            last_commit_sha=last_sha,
            last_commit_date=last_date,
            last_commit_message=last_msg,
            storage_size_bytes=storage_size,
        )
