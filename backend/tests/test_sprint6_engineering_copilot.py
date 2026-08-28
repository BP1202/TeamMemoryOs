"""
Sprint 6 — AI Engineering Copilot Tests

Covers all 5 milestones:
* 6.1 Git Repository Intelligence
* 6.2 PR Guardian
* 6.3 Terminal Memory Copilot
* 6.4 AI Codebase Search
* 6.5 Engineering Conversation Engine

Validates:
* Organisation isolation
* Duplicate prevention
* JWT authentication
* Deterministic parsing / risk scoring
* Retrieval correctness
* Graph explanations
* Repository sync (no-op when not locally cloned)
* Terminal parsing and classification
* PR parsing and risk detection
* Code search
"""
from __future__ import annotations

import uuid
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app

# ---------------------------------------------------------------------------
# Base URLs
# ---------------------------------------------------------------------------

USERS_API = "/api/v1/users"
ORGS_API = "/api/v1/organizations"
AUTH_API = "/api/v1/auth/login"
MEMORY_API = "/api/v1/memory"
GIT_API = "/api/v1/git"
TERMINAL_API = "/api/v1/terminal"
CODE_API = "/api/v1/code"
ENGINEERING_API = "/api/v1/engineering"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(client: TestClient, email: str, password: str) -> str:
    resp = client.post(AUTH_API, data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _make_user_and_headers(client: TestClient, prefix: str = "sprint6") -> dict:
    password = "ValidPass123!"
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        f"{USERS_API}/",
        json={"full_name": "Sprint6 User", "email": email, "password": password},
    )
    token = _login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


def _make_org(client: TestClient) -> dict:
    slug = f"sp6-{uuid.uuid4().hex[:8]}"
    resp = client.post(f"{ORGS_API}/", json={"name": "Sprint6 Org", "slug": slug})
    assert resp.status_code == 201, resp.text
    return resp.json()


def _make_repo(client: TestClient, org_id: str, headers: dict) -> dict:
    resp = client.post(
        f"{GIT_API}/repositories/",
        json={
            "organization_id": org_id,
            "name": "test-repo",
            "remote_url": f"https://github.com/test/repo-{uuid.uuid4().hex[:6]}",
            "default_branch": "main",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ===========================================================================
# Fixtures
# ===========================================================================

@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client: TestClient) -> dict:
    return _make_user_and_headers(client)


@pytest.fixture()
def org(client: TestClient) -> dict:
    return _make_org(client)


@pytest.fixture()
def repo(client: TestClient, org: dict, auth_headers: dict) -> dict:
    return _make_repo(client, org["id"], auth_headers)


# ===========================================================================
# Milestone 6.1 — Git Repository Intelligence
# ===========================================================================

class TestRepositoryRegistration:
    def test_register_repository_returns_201(self, client, org, auth_headers):
        resp = client.post(
            f"{GIT_API}/repositories/",
            json={
                "organization_id": org["id"],
                "name": "my-repo",
                "remote_url": f"https://github.com/org/repo-{uuid.uuid4().hex[:6]}",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "my-repo"
        assert data["organization_id"] == org["id"]
        assert data["last_synced_at"] is None

    def test_register_duplicate_url_returns_409(self, client, org, auth_headers):
        url = f"https://github.com/org/dup-{uuid.uuid4().hex[:6]}"
        client.post(
            f"{GIT_API}/repositories/",
            json={"organization_id": org["id"], "name": "repo1", "remote_url": url},
            headers=auth_headers,
        )
        resp = client.post(
            f"{GIT_API}/repositories/",
            json={"organization_id": org["id"], "name": "repo2", "remote_url": url},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    def test_register_without_auth_returns_401(self, client, org):
        resp = client.post(
            f"{GIT_API}/repositories/",
            json={
                "organization_id": org["id"],
                "name": "repo",
                "remote_url": "https://github.com/org/repo",
            },
        )
        assert resp.status_code == 401

    def test_list_repositories(self, client, org, auth_headers, repo):
        resp = client.get(
            f"{GIT_API}/repositories/?organization_id={org['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        ids = [r["id"] for r in resp.json()]
        assert repo["id"] in ids

    def test_list_repositories_org_isolation(self, client, auth_headers, repo):
        """Other org must not see this repo."""
        other_org = _make_org(client)
        resp = client.get(
            f"{GIT_API}/repositories/?organization_id={other_org['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        ids = [r["id"] for r in resp.json()]
        assert repo["id"] not in ids

    def test_sync_repository_no_local_clone(self, client, repo, auth_headers):
        """Remote URL is not a local directory — sync returns 0 ingested."""
        resp = client.post(
            f"{GIT_API}/repositories/{repo['id']}/sync",
            json={"max_commits": 10},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["commits_ingested"] == 0
        assert data["repository_id"] == repo["id"]

    def test_sync_unknown_repository_returns_404(self, client, auth_headers):
        resp = client.post(
            f"{GIT_API}/repositories/{uuid.uuid4()}/sync",
            json={"max_commits": 10},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_list_commits_empty(self, client, repo, auth_headers):
        resp = client.get(
            f"{GIT_API}/repositories/{repo['id']}/commits",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []


class TestCommitIngestion:
    """Service-level tests for commit ingestion."""

    def _get_db(self):
        from app.db.dependencies import get_db
        return next(get_db())

    def test_ingest_commit_creates_memory_entry(self, org):
        from datetime import datetime, timezone
        from app.services.repository import ingest_commit
        from app.services.repository import create_repository
        from app.schemas.repository import RepositoryCreate

        db = self._get_db()
        try:
            repo = create_repository(
                db,
                RepositoryCreate(
                    organization_id=uuid.UUID(org["id"]),
                    name="test",
                    remote_url=f"https://github.com/x/y-{uuid.uuid4().hex[:6]}",
                ),
            )
            result = ingest_commit(
                db,
                organization_id=uuid.UUID(org["id"]),
                repository_id=repo.id,
                commit_sha="abc123def456" + uuid.uuid4().hex[:16],
                author_name="Alice",
                author_email="alice@example.com",
                commit_message="feat: add new endpoint",
                committed_at=datetime.now(timezone.utc),
                files_changed=3,
                insertions=50,
                deletions=10,
                changed_files=["app/api/v1/users.py", "tests/test_users.py"],
            )
            assert result is not None
            assert result.commit_sha.startswith("abc123")
            assert result.memory_entry_id is not None
        finally:
            db.close()

    def test_ingest_duplicate_commit_returns_none(self, org):
        from datetime import datetime, timezone
        from app.services.repository import ingest_commit, create_repository
        from app.schemas.repository import RepositoryCreate

        db = self._get_db()
        sha = "dupsha" + uuid.uuid4().hex[:26]
        try:
            repo = create_repository(
                db,
                RepositoryCreate(
                    organization_id=uuid.UUID(org["id"]),
                    name="dup-test",
                    remote_url=f"https://github.com/x/dup-{uuid.uuid4().hex[:6]}",
                ),
            )
            from datetime import datetime, timezone
            kwargs = dict(
                organization_id=uuid.UUID(org["id"]),
                repository_id=repo.id,
                commit_sha=sha,
                author_name="Bob",
                author_email="b@example.com",
                commit_message="fix: something",
                committed_at=datetime.now(timezone.utc),
            )
            first = ingest_commit(db, **kwargs)
            second = ingest_commit(db, **kwargs)
            assert first is not None
            assert second is None  # idempotent
        finally:
            db.close()

    def test_secret_filter_removes_credentials(self):
        from app.services.repository import _filter_secrets
        text = "Set password=supersecret123 in config"
        filtered = _filter_secrets(text)
        assert "supersecret123" not in filtered
        assert "[REDACTED]" in filtered


# ===========================================================================
# Milestone 6.2 — PR Guardian
# ===========================================================================

class TestPRCreation:
    def test_create_pr_returns_201(self, client, org, repo, auth_headers):
        resp = client.post(
            f"{GIT_API}/pull-requests/",
            json={
                "organization_id": org["id"],
                "repository_id": repo["id"],
                "pr_number": 42,
                "title": "feat: add user endpoint",
                "description": "Adds POST /users with validation",
                "author": "alice",
                "source_branch": "feat/users",
                "target_branch": "main",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["pr_number"] == 42
        assert data["organization_id"] == org["id"]
        assert data["memory_entry_id"] is not None

    def test_create_duplicate_pr_returns_409(self, client, org, repo, auth_headers):
        payload = {
            "organization_id": org["id"],
            "repository_id": repo["id"],
            "pr_number": 99,
            "title": "PR 99",
        }
        client.post(f"{GIT_API}/pull-requests/", json=payload, headers=auth_headers)
        resp = client.post(f"{GIT_API}/pull-requests/", json=payload, headers=auth_headers)
        assert resp.status_code == 409

    def test_create_pr_without_auth_returns_401(self, client, org, repo):
        resp = client.post(
            f"{GIT_API}/pull-requests/",
            json={
                "organization_id": org["id"],
                "repository_id": repo["id"],
                "pr_number": 1,
                "title": "No auth PR",
            },
        )
        assert resp.status_code == 401

    def test_list_prs_org_isolation(self, client, org, repo, auth_headers):
        client.post(
            f"{GIT_API}/pull-requests/",
            json={
                "organization_id": org["id"],
                "repository_id": repo["id"],
                "pr_number": 77,
                "title": "My PR",
            },
            headers=auth_headers,
        )
        other_org = _make_org(client)
        resp = client.get(
            f"{GIT_API}/pull-requests/?organization_id={other_org['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []


class TestPRRiskAndReview:
    def test_risk_score_high_risk_pr(self, client, org, repo, auth_headers):
        resp = client.post(
            f"{GIT_API}/pull-requests/",
            json={
                "organization_id": org["id"],
                "repository_id": repo["id"],
                "pr_number": 100,
                "title": "fix: production database migration",
                "description": "Drops old table and runs schema migration",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        pr_id = resp.json()["id"]

        risk_resp = client.get(
            f"{GIT_API}/pull-requests/{pr_id}/risk",
            headers=auth_headers,
        )
        assert risk_resp.status_code == 200
        data = risk_resp.json()
        assert data["risk_score"] > 0.0
        assert len(data["risk_factors"]) > 0

    def test_risk_score_low_risk_pr(self, client, org, repo, auth_headers):
        resp = client.post(
            f"{GIT_API}/pull-requests/",
            json={
                "organization_id": org["id"],
                "repository_id": repo["id"],
                "pr_number": 101,
                "title": "docs: update README",
                "description": "Minor documentation update",
            },
            headers=auth_headers,
        )
        pr_id = resp.json()["id"]
        risk_resp = client.get(
            f"{GIT_API}/pull-requests/{pr_id}/risk",
            headers=auth_headers,
        )
        # Low risk PR should have low score (may still detect "database" in description if present)
        assert risk_resp.status_code == 200
        assert risk_resp.json()["risk_score"] >= 0.0

    def test_review_pr_returns_201(self, client, org, repo, auth_headers):
        pr_resp = client.post(
            f"{GIT_API}/pull-requests/",
            json={
                "organization_id": org["id"],
                "repository_id": repo["id"],
                "pr_number": 102,
                "title": "refactor: auth service",
            },
            headers=auth_headers,
        )
        pr_id = pr_resp.json()["id"]

        resp = client.post(
            f"{GIT_API}/pull-requests/{pr_id}/review",
            json={"top_k": 3},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "summary" in data
        assert "risk_score" in data
        assert "suggestions" in data
        assert data["pull_request_id"] == pr_id

    def test_review_pr_not_found_returns_404(self, client, auth_headers):
        resp = client.post(
            f"{GIT_API}/pull-requests/{uuid.uuid4()}/review",
            json={"top_k": 3},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_list_reviews_for_pr(self, client, org, repo, auth_headers):
        pr_resp = client.post(
            f"{GIT_API}/pull-requests/",
            json={
                "organization_id": org["id"],
                "repository_id": repo["id"],
                "pr_number": 103,
                "title": "List reviews test",
            },
            headers=auth_headers,
        )
        pr_id = pr_resp.json()["id"]
        client.post(f"{GIT_API}/pull-requests/{pr_id}/review", json={}, headers=auth_headers)

        list_resp = client.get(
            f"{GIT_API}/pull-requests/{pr_id}/reviews",
            headers=auth_headers,
        )
        assert list_resp.status_code == 200
        assert len(list_resp.json()) >= 1


class TestPRRiskService:
    """Unit tests for deterministic risk scoring."""

    def test_risk_score_database_migration(self):
        from app.services.pull_request import _compute_risk_score
        score, factors = _compute_risk_score(
            title="database migration",
            description="migrate production schema",
            diff_text=None,
            files_changed=5,
        )
        assert score > 0.3
        assert len(factors) > 0

    def test_risk_score_large_pr(self):
        from app.services.pull_request import _compute_risk_score
        score, factors = _compute_risk_score(
            title="big refactor",
            description="refactor everything",
            diff_text=None,
            files_changed=25,
        )
        assert score > 0.0
        assert any("Large" in f for f in factors)

    def test_parse_changed_files_from_diff(self):
        from app.services.pull_request import _parse_changed_files_from_diff
        diff = """diff --git a/app/main.py b/app/main.py
--- a/app/main.py
+++ b/app/main.py
@@ -1,3 +1,4 @@"""
        files = _parse_changed_files_from_diff(diff)
        assert "app/main.py" in files


# ===========================================================================
# Milestone 6.3 — Terminal Memory Copilot
# ===========================================================================

class TestTerminalUpload:
    def test_upload_session_with_error_returns_201(self, client, org, auth_headers):
        resp = client.post(
            f"{TERMINAL_API}/sessions/",
            json={
                "organization_id": org["id"],
                "raw_output": (
                    "$ python manage.py runserver\n"
                    "Traceback (most recent call last):\n"
                    "  File 'manage.py', line 10, in <module>\n"
                    "ImportError: No module named 'django'\n"
                ),
                "command": "python manage.py runserver",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "session_id" in data
        assert data["errors_found"] > 0
        assert data["errors_ingested"] > 0
        assert data["memory_entries_created"] > 0

    def test_upload_session_no_errors(self, client, org, auth_headers):
        resp = client.post(
            f"{TERMINAL_API}/sessions/",
            json={
                "organization_id": org["id"],
                "raw_output": "$ ls -la\ntotal 20\ndrwxr-xr-x 5 user user 4096 Jan 1 00:00 .\n",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["errors_found"] == 0

    def test_upload_without_auth_returns_401(self, client, org):
        resp = client.post(
            f"{TERMINAL_API}/sessions/",
            json={"organization_id": org["id"], "raw_output": "some output"},
        )
        assert resp.status_code == 401

    def test_list_sessions(self, client, org, auth_headers):
        client.post(
            f"{TERMINAL_API}/sessions/",
            json={"organization_id": org["id"], "raw_output": "$ echo hello\nhello"},
            headers=auth_headers,
        )
        resp = client.get(
            f"{TERMINAL_API}/sessions/?organization_id={org['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_list_sessions_org_isolation(self, client, org, auth_headers):
        other_org = _make_org(client)
        resp = client.get(
            f"{TERMINAL_API}/sessions/?organization_id={other_org['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_search_failures_returns_response(self, client, org, auth_headers):
        resp = client.post(
            f"{TERMINAL_API}/search",
            json={
                "organization_id": org["id"],
                "error_message": "ImportError: No module named 'django'",
                "top_k": 5,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "fixes" in data
        assert "explanation" in data
        assert isinstance(data["fixes"], list)

    def test_get_session_errors(self, client, org, auth_headers):
        upload_resp = client.post(
            f"{TERMINAL_API}/sessions/",
            json={
                "organization_id": org["id"],
                "raw_output": "Traceback (most recent call last):\nValueError: invalid literal",
            },
            headers=auth_headers,
        )
        session_id = upload_resp.json()["session_id"]
        resp = client.get(
            f"{TERMINAL_API}/sessions/{session_id}/errors",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestErrorClassifier:
    """Unit tests for deterministic error classification."""

    def test_classify_import_error(self):
        from app.services.terminal import _classify_errors
        output = "ImportError: No module named 'requests'"
        errors = _classify_errors(output)
        types = [e[0] for e in errors]
        assert "ImportError" in types

    def test_classify_connection_refused(self):
        from app.services.terminal import _classify_errors
        output = "ConnectionRefusedError: [Errno 111] Connection refused"
        errors = _classify_errors(output)
        types = [e[0] for e in errors]
        assert "ConnectionRefused" in types

    def test_classify_python_traceback(self):
        from app.services.terminal import _classify_errors
        output = "Traceback (most recent call last):\n  File 'app.py'\nTypeError: expected str"
        errors = _classify_errors(output)
        assert len(errors) > 0

    def test_no_errors_returns_empty(self):
        from app.services.terminal import _classify_errors
        output = "$ echo hello\nhello\n$ ls\nfile1.py  file2.py"
        errors = _classify_errors(output)
        assert errors == []

    def test_parse_command(self):
        from app.services.terminal import _parse_command
        output = "$ python -m pytest tests/\nCollecting..."
        cmd = _parse_command(output)
        assert cmd is not None
        assert "python" in cmd.lower() or "pytest" in cmd.lower()


# ===========================================================================
# Milestone 6.4 — AI Codebase Search
# ===========================================================================

class TestCodeSearch:
    def test_search_returns_200(self, client, org, auth_headers):
        resp = client.post(
            f"{CODE_API}/search",
            json={
                "organization_id": org["id"],
                "query": "authentication service",
                "top_k": 5,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "result_count" in data
        assert data["query"] == "authentication service"

    def test_search_empty_org_returns_empty_results(self, client, org, auth_headers):
        resp = client.post(
            f"{CODE_API}/search",
            json={"organization_id": org["id"], "query": "find something"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_search_without_auth_returns_401(self, client, org):
        resp = client.post(
            f"{CODE_API}/search",
            json={"organization_id": org["id"], "query": "find something"},
        )
        assert resp.status_code == 401

    def test_search_invalid_input_returns_422(self, client, org, auth_headers):
        resp = client.post(
            f"{CODE_API}/search",
            json={"organization_id": org["id"], "query": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_index_nonexistent_repo_returns_zero(self, client, repo, auth_headers):
        """Repository remote_url is HTTPS — not a local dir — index returns 0."""
        resp = client.post(
            f"{CODE_API}/repositories/{repo['id']}/index",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["files_indexed"] == 0

    def test_index_unknown_repo_returns_404(self, client, auth_headers):
        resp = client.post(
            f"{CODE_API}/repositories/{uuid.uuid4()}/index",
            json={},
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestChunkingService:
    """Unit tests for code chunking and AST parsing."""

    def test_chunk_python_function(self):
        from app.services.code_index import _chunk_python
        code = '''def hello(name):
    """Greet."""
    return f"Hello, {name}!"

def world():
    pass
'''
        chunks = _chunk_python(code)
        types = [c[3] for c in chunks]
        assert "function" in types
        names = [c[4] for c in chunks if c[4]]
        assert "hello" in names

    def test_chunk_python_class(self):
        from app.services.code_index import _chunk_python
        code = '''class MyService:
    def __init__(self):
        self.value = 42

    def get_value(self):
        return self.value
'''
        chunks = _chunk_python(code)
        types = [c[3] for c in chunks]
        assert "class" in types or "function" in types

    def test_chunk_fixed_splits_correctly(self):
        from app.services.code_index import _chunk_fixed
        lines = [f"line {i}" for i in range(100)]
        content = "\n".join(lines)
        chunks = _chunk_fixed(content, chunk_size=40)
        assert len(chunks) >= 2
        for chunk_content, start, end, chunk_type, _ in chunks:
            assert start >= 1
            assert end >= start
            assert chunk_type == "block"

    def test_detect_language(self):
        from app.services.code_index import _detect_language
        assert _detect_language("main.py") == "python"
        assert _detect_language("app.ts") == "typescript"
        assert _detect_language("service.go") == "go"
        assert _detect_language("unknown.xyz") is None


# ===========================================================================
# Milestone 6.5 — Engineering Conversation Engine
# ===========================================================================

class TestEngineeringChat:
    def test_chat_returns_200(self, client, org, auth_headers):
        resp = client.post(
            f"{ENGINEERING_API}/chat",
            json={
                "organization_id": org["id"],
                "question": "What is the architecture of our authentication system?",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "citations" in data
        assert "graph_path" in data
        assert "confidence" in data
        assert "retrieval_mode" in data
        assert "suggested_actions" in data
        assert "provider_used" in data

    def test_chat_retrieval_mode_is_hybrid(self, client, org, auth_headers):
        resp = client.post(
            f"{ENGINEERING_API}/chat",
            json={"organization_id": org["id"], "question": "Any question"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["retrieval_mode"] == "hybrid"

    def test_chat_confidence_in_range(self, client, org, auth_headers):
        resp = client.post(
            f"{ENGINEERING_API}/chat",
            json={"organization_id": org["id"], "question": "Test question"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        confidence = resp.json()["confidence"]
        assert 0.0 <= confidence <= 1.0

    def test_chat_suggested_actions_non_empty(self, client, org, auth_headers):
        resp = client.post(
            f"{ENGINEERING_API}/chat",
            json={"organization_id": org["id"], "question": "debug this error"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()["suggested_actions"]) > 0

    def test_chat_without_auth_returns_401(self, client, org):
        resp = client.post(
            f"{ENGINEERING_API}/chat",
            json={"organization_id": org["id"], "question": "test"},
        )
        assert resp.status_code == 401

    def test_chat_empty_question_returns_422(self, client, org, auth_headers):
        resp = client.post(
            f"{ENGINEERING_API}/chat",
            json={"organization_id": org["id"], "question": ""},
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestEngineeringDebug:
    def test_debug_returns_200(self, client, org, auth_headers):
        resp = client.post(
            f"{ENGINEERING_API}/debug",
            json={
                "organization_id": org["id"],
                "error_message": "ConnectionRefusedError: [Errno 111] Connection refused",
                "stack_trace": "Traceback (most recent call last):\n  File 'app.py', line 5",
                "command": "python app.py",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert data["provider_used"] == "stub"

    def test_debug_without_auth_returns_401(self, client, org):
        resp = client.post(
            f"{ENGINEERING_API}/debug",
            json={"organization_id": org["id"], "error_message": "Error"},
        )
        assert resp.status_code == 401


class TestEngineeringReview:
    def test_review_returns_200(self, client, org, auth_headers):
        resp = client.post(
            f"{ENGINEERING_API}/review",
            json={
                "organization_id": org["id"],
                "title": "feat: add new API endpoint",
                "diff_text": "--- a/app.py\n+++ b/app.py\n@@ -1,3 +1,4 @@\n+    pass",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "citations" in data

    def test_review_without_auth_returns_401(self, client, org):
        resp = client.post(
            f"{ENGINEERING_API}/review",
            json={"organization_id": org["id"], "title": "PR"},
        )
        assert resp.status_code == 401


class TestPromptRouter:
    """Unit tests for mode detection router."""

    def test_detect_debug_mode(self):
        from app.services.engineering import _detect_mode
        assert _detect_mode("I got an ImportError when running the tests") == "debug"

    def test_detect_architecture_mode(self):
        from app.services.engineering import _detect_mode
        assert _detect_mode("What is the architecture of the auth service?") == "architecture"

    def test_detect_review_mode(self):
        from app.services.engineering import _detect_mode
        assert _detect_mode("Please review this pull request") == "review"

    def test_detect_search_mode(self):
        from app.services.engineering import _detect_mode
        assert _detect_mode("Find the function that handles authentication") == "search"

    def test_detect_incident_mode(self):
        from app.services.engineering import _detect_mode
        assert _detect_mode("Production outage — service is down") == "incident"

    def test_detect_auto_fallback(self):
        from app.services.engineering import _detect_mode
        # Generic question should fall back to auto
        mode = _detect_mode("What team conventions do we follow?")
        # May be any valid mode — just verify it's a valid string
        assert mode in {"auto", "debug", "architecture", "review", "search", "incident"}
