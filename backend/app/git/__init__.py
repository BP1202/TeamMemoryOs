"""Git Repository Intelligence and Incremental Indexing Engine (AI-004)."""
from app.git.branch_parser import parse_git_branch, parse_git_tag
from app.git.commit_parser import (
    extract_conventional_type,
    extract_issue_references,
    filter_secrets,
    parse_gitpython_commit,
)
from app.git.diff_detector import detect_diff, detect_working_tree_diff
from app.git.git_models import (
    FileChangeType,
    GitBranchInfo,
    GitCommitInfo,
    GitDiffEntry,
    GitDiffSummary,
    GitTagInfo,
    IncrementalIndexResult,
    RepositoryHealth,
)
from app.git.git_repository import GitRepositoryWrapper
from app.git.repository_indexer import GitRepositoryIndexer

__all__ = [
    "FileChangeType",
    "GitBranchInfo",
    "GitCommitInfo",
    "GitDiffEntry",
    "GitDiffSummary",
    "GitTagInfo",
    "IncrementalIndexResult",
    "RepositoryHealth",
    "GitRepositoryWrapper",
    "GitRepositoryIndexer",
    "parse_git_branch",
    "parse_git_tag",
    "parse_gitpython_commit",
    "filter_secrets",
    "extract_conventional_type",
    "extract_issue_references",
    "detect_diff",
    "detect_working_tree_diff",
]
