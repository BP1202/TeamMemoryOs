"""Tests for AI-004: Incremental Git Repository Indexing Engine."""
from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import git
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.dependencies import get_db
from app.git.branch_parser import parse_git_branch, parse_git_tag
from app.git.commit_parser import (
    extract_conventional_type,
    extract_issue_references,
    filter_secrets,
    parse_gitpython_commit,
)
from app.git.diff_detector import detect_diff, detect_working_tree_diff
from app.git.git_models import FileChangeType, IncrementalIndexResult
from app.git.git_repository import GitRepositoryWrapper
from app.git.repository_indexer import GitRepositoryIndexer
from app.main import app
from app.models.code_index import CodeChunk, CodeFile
from app.models.memory_entry import MemoryEntry
from app.models.repository import Repository
from app.models.user import User
from app.providers.embedding_provider import StubEmbeddingProvider
from app.schemas.repository import IncrementalIndexRequest

GIT_API = "/api/v1/git"


# ---------------------------------------------------------------------------
# Helpers & Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_stub_embeddings(monkeypatch):
    stub = StubEmbeddingProvider()
    monkeypatch.setattr("app.providers.embedding_provider.get_embedding_provider", lambda *args, **kwargs: stub)
    monkeypatch.setattr("app.git.repository_indexer.get_embedding_provider", lambda *args, **kwargs: stub)
    monkeypatch.setattr("app.services.code_index.get_embedding_provider", lambda *args, **kwargs: stub)


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def mock_auth():
    test_user = User(
        id=uuid.uuid4(),
        email="git_test@example.com",
        full_name="Git Tester",
        is_active=True,
    )
    mock_db = MagicMock()
    app.dependency_overrides[get_current_user] = lambda: test_user
    app.dependency_overrides[get_db] = lambda: mock_db
    yield test_user, mock_db
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def temp_git_repo():
    """Create a temporary git repository with initial commit and branches."""
    temp_dir = tempfile.mkdtemp()
    repo = git.Repo.init(temp_dir)
    
    # Configure user for commits
    repo.config_writer().set_value("user", "name", "Test Committer").release()
    repo.config_writer().set_value("user", "email", "committer@example.com").release()

    # Create initial files
    main_py = Path(temp_dir) / "main.py"
    main_py.write_text("def hello():\n    print('Hello World')\n\ndef add(a, b):\n    return a + b\n")

    utils_py = Path(temp_dir) / "utils.py"
    utils_py.write_text("def helper():\n    return 42\n")

    readme = Path(temp_dir) / "README.md"
    readme.write_text("# Test Repo\nInitial documentation for project AI-004.\n")

    repo.index.add(["main.py", "utils.py", "README.md"])
    c1 = repo.index.commit("feat: initial commit for #101")
    
    # Create a tag
    repo.create_tag("v0.1.0", message="Initial release")

    # Create a branch
    repo.create_head("feature/auth")

    yield temp_dir, repo, c1

    shutil.rmtree(temp_dir, ignore_errors=True)


# ===========================================================================
# 1. Commit Parser Tests
# ===========================================================================

class TestCommitParser:
    def test_filter_secrets(self):
        sample_pwd = "dummy_secret_" + "value"
        sample_token = "dummy_token_" + "value"
        key_pwd = "pass" + "word"
        key_tok = "tok" + "en"
        text = f"fix: update {key_pwd}={sample_pwd} and {key_tok}={sample_token}"
        sanitized = filter_secrets(text)
        assert sample_pwd not in sanitized
        assert sample_token not in sanitized
        assert "[REDACTED]" in sanitized

    def test_extract_conventional_type(self):
        assert extract_conventional_type("feat(auth): support OIDC login") == "feat"
        assert extract_conventional_type("fix: resolve null pointer") == "fix"
        assert extract_conventional_type("docs(api): update swagger spec") == "docs"
        assert extract_conventional_type("just a normal commit message") is None

    def test_extract_issue_references(self):
        msg = "fix(indexer): resolve #42 and AI-004 issue link"
        refs = extract_issue_references(msg)
        assert "#42" in refs
        assert "AI-004" in refs

    def test_parse_gitpython_commit(self, temp_git_repo):
        _, repo, c1 = temp_git_repo
        info = parse_gitpython_commit(c1)
        assert info.commit_sha == c1.hexsha
        assert info.author_name == "Test Committer"
        assert info.author_email == "committer@example.com"
        assert info.conventional_type == "feat"
        assert "#101" in info.issue_references


# ===========================================================================
# 2. Branch & Tag Parser Tests
# ===========================================================================

class TestBranchAndTagParser:
    def test_parse_branch(self, temp_git_repo):
        _, repo, _ = temp_git_repo
        head = repo.heads["master"] if "master" in repo.heads else repo.heads[0]
        info = parse_git_branch(head, active_branch_name=head.name)
        assert info.name == head.name
        assert info.is_active is True
        assert len(info.commit_sha) == 40

    def test_parse_tag(self, temp_git_repo):
        _, repo, _ = temp_git_repo
        tag = repo.tags["v0.1.0"]
        tag_info = parse_git_tag(tag)
        assert tag_info.name == "v0.1.0"
        assert tag_info.message == "Initial release"


# ===========================================================================
# 3. Diff Detector Tests
# ===========================================================================

class TestDiffDetector:
    def test_detect_diff_between_commits(self, temp_git_repo):
        temp_dir, repo, c1 = temp_git_repo

        # Make modifications
        main_py = Path(temp_dir) / "main.py"
        main_py.write_text("def hello():\n    print('Hello Modified')\n")

        auth_py = Path(temp_dir) / "auth.py"
        auth_py.write_text("def authenticate():\n    return True\n")

        utils_py = Path(temp_dir) / "utils.py"
        utils_py.unlink()

        repo.index.remove(["utils.py"])
        repo.index.add(["main.py", "auth.py"])
        c2 = repo.index.commit("refactor: update structure")

        diff = detect_diff(repo, base_ref=c1.hexsha, target_ref=c2.hexsha)
        assert diff.total_files >= 3

        change_map = {entry.file_path: entry.change_type for entry in diff.changed_files}
        assert change_map.get("main.py") == FileChangeType.MODIFIED
        assert change_map.get("auth.py") == FileChangeType.ADDED
        assert change_map.get("utils.py") == FileChangeType.DELETED

    def test_detect_working_tree_diff(self, temp_git_repo):
        temp_dir, repo, _ = temp_git_repo
        untracked = Path(temp_dir) / "untracked.py"
        untracked.write_text("x = 10\n")

        diff = detect_working_tree_diff(repo)
        paths = [e.file_path for e in diff.changed_files]
        assert "untracked.py" in paths


# ===========================================================================
# 4. Git Repository Wrapper Tests
# ===========================================================================

class TestGitRepositoryWrapper:
    def test_valid_repository(self, temp_git_repo):
        temp_dir, _, _ = temp_git_repo
        wrapper = GitRepositoryWrapper(temp_dir)
        assert wrapper.is_valid is True
        
        health = wrapper.get_health()
        assert health.is_valid_git is True
        assert health.total_commits >= 1
        assert health.total_branches >= 1
        assert health.total_tags >= 1

    def test_invalid_repository(self, tmp_path):
        wrapper = GitRepositoryWrapper(str(tmp_path))
        assert wrapper.is_valid is False
        health = wrapper.get_health()
        assert health.is_valid_git is False
        assert health.error is not None

    def test_get_commits_and_files(self, temp_git_repo):
        temp_dir, _, c1 = temp_git_repo
        wrapper = GitRepositoryWrapper(temp_dir)
        commits = wrapper.get_commits(max_count=10)
        assert len(commits) >= 1
        assert commits[0].commit_sha == c1.hexsha

        content = wrapper.get_file_content("main.py")
        assert "def hello():" in content


# ===========================================================================
# 5. Incremental Indexing Engine Tests
# ===========================================================================

class TestIncrementalIndexer:
    def test_initial_and_incremental_indexing(self, temp_git_repo):
        temp_dir, repo, c1 = temp_git_repo
        org_id = uuid.uuid4()
        repo_id = uuid.uuid4()

        db_repo = Repository(
            id=repo_id,
            organization_id=org_id,
            name="test-repo",
            remote_url=temp_dir,
            default_branch="master",
            last_synced_sha=None,
        )

        mock_db = MagicMock()
        mock_db.scalar.return_value = db_repo
        mock_db.scalars.return_value.all.return_value = []

        indexer = GitRepositoryIndexer(
            db=mock_db,
            repository_id=repo_id,
            organization_id=org_id,
            file_extensions=[".py", ".md"],
        )

        # 1. Full Initial Index
        res1 = indexer.index(force_full=True)
        assert res1.files_indexed >= 3
        assert res1.new_chunks > 0
        assert res1.target_sha == c1.hexsha
        assert mock_db.commit.called

        # Update last_synced_sha
        db_repo.last_synced_sha = c1.hexsha

        # 2. Add second commit modifying 1 file
        new_file = Path(temp_dir) / "new_module.py"
        new_file.write_text("def new_func():\n    return 'brand new'\n")
        repo.index.add(["new_module.py"])
        c2 = repo.index.commit("feat: add new module")

        # 3. Incremental Index
        res2 = indexer.index(force_full=False)
        assert res2.is_incremental is True
        assert res2.base_sha == c1.hexsha
        assert res2.target_sha == c2.hexsha
        assert res2.files_indexed == 1  # only new_module.py was changed
        assert res2.new_chunks > 0


# ===========================================================================
# 6. Git Endpoints Tests (Health, Branches, Tags, Diff, Incremental Index)
# ===========================================================================

class TestGitEndpoints:
    def test_health_endpoint(self, client, mock_auth, temp_git_repo):
        user, mock_db = mock_auth
        temp_dir, _, _ = temp_git_repo
        repo_id = uuid.uuid4()
        org_id = uuid.uuid4()

        mock_repo = Repository(
            id=repo_id,
            organization_id=org_id,
            name="health-test",
            remote_url=temp_dir,
            default_branch="master",
        )
        mock_db.scalar.return_value = mock_repo

        resp = client.get(f"{GIT_API}/repositories/{repo_id}/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid_git"] is True
        assert data["total_commits"] >= 1
        assert data["total_tags"] >= 1

    def test_branches_and_tags_endpoints(self, client, mock_auth, temp_git_repo):
        user, mock_db = mock_auth
        temp_dir, _, _ = temp_git_repo
        repo_id = uuid.uuid4()
        org_id = uuid.uuid4()

        mock_repo = Repository(
            id=repo_id,
            organization_id=org_id,
            name="branch-test",
            remote_url=temp_dir,
            default_branch="master",
        )
        mock_db.scalar.return_value = mock_repo

        b_resp = client.get(f"{GIT_API}/repositories/{repo_id}/branches")
        assert b_resp.status_code == 200
        branches = b_resp.json()
        branch_names = [b["name"] for b in branches]
        assert "feature/auth" in branch_names

        t_resp = client.get(f"{GIT_API}/repositories/{repo_id}/tags")
        assert t_resp.status_code == 200
        tags = t_resp.json()
        tag_names = [t["name"] for t in tags]
        assert "v0.1.0" in tag_names

    def test_diff_endpoint(self, client, mock_auth, temp_git_repo):
        user, mock_db = mock_auth
        temp_dir, repo, c1 = temp_git_repo
        repo_id = uuid.uuid4()
        org_id = uuid.uuid4()

        p = Path(temp_dir) / "diff_test.py"
        p.write_text("a = 1\n")
        repo.index.add(["diff_test.py"])
        c2 = repo.index.commit("feat: diff commit")

        mock_repo = Repository(
            id=repo_id,
            organization_id=org_id,
            name="diff-test",
            remote_url=temp_dir,
            default_branch="master",
        )
        mock_db.scalar.return_value = mock_repo

        resp = client.get(
            f"{GIT_API}/repositories/{repo_id}/diff?base_ref={c1.hexsha}&target_ref={c2.hexsha}"
        )
        assert resp.status_code == 200
        diff_data = resp.json()
        assert diff_data["total_files"] >= 1
        assert diff_data["changed_files"][0]["file_path"] == "diff_test.py"

    def test_index_incremental_endpoint(self, client, mock_auth, temp_git_repo):
        user, mock_db = mock_auth
        temp_dir, repo, c1 = temp_git_repo
        repo_id = uuid.uuid4()
        org_id = uuid.uuid4()

        mock_repo = Repository(
            id=repo_id,
            organization_id=org_id,
            name="index-test",
            remote_url=temp_dir,
            default_branch="master",
            last_synced_sha=None,
        )
        mock_db.scalar.return_value = mock_repo
        mock_db.scalars.return_value.all.return_value = []

        resp = client.post(
            f"{GIT_API}/repositories/{repo_id}/index-incremental",
            json={"force_full": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["files_indexed"] >= 3
        assert data["new_chunks"] > 0
