"""
Task 3.4 — Organization Member API validation tests.

Covers:
* POST /api/v1/members/                                    — create membership
* GET  /api/v1/members/organization/{org_id}               — list by org
* GET  /api/v1/members/user/{user_id}                      — list by user
* GET  /api/v1/members/{member_id}                         — get single
* Duplicate membership rejection (IntegrityError → 400)
"""
import uuid

import pytest
from fastapi.testclient import TestClient


USERS_API = "/api/v1/users"
ORGS_API = "/api/v1/organizations"
MEMBERS_API = "/api/v1/members"


@pytest.fixture()
def org(client: TestClient):
    slug = f"test-org-{uuid.uuid4().hex[:8]}"
    resp = client.post(f"{ORGS_API}/", json={"name": "Test Org", "slug": slug})
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def user(client: TestClient):
    resp = client.post(
        f"{USERS_API}/",
        json={
            "full_name": "Member User",
            "email": f"member_{uuid.uuid4().hex[:8]}@example.com",
            "password": "securepassword1",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture()
def membership(client: TestClient, org, user):
    resp = client.post(
        f"{MEMBERS_API}/",
        json={
            "organization_id": org["id"],
            "user_id": user["id"],
            "role": "member",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestCreateMember:
    def test_create_returns_201(self, membership):
        assert "id" in membership
        assert "joined_at" in membership
        assert membership["role"] == "member"

    def test_create_with_role_owner(self, client: TestClient, org, user):
        # Use a fresh user for this test
        resp_user = client.post(
            f"{USERS_API}/",
            json={
                "full_name": "Owner User",
                "email": f"owner_{uuid.uuid4().hex[:8]}@example.com",
                "password": "securepassword1",
            },
        )
        new_user = resp_user.json()
        resp = client.post(
            f"{MEMBERS_API}/",
            json={
                "organization_id": org["id"],
                "user_id": new_user["id"],
                "role": "owner",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["role"] == "owner"

    def test_duplicate_membership_rejected(self, client: TestClient, membership):
        resp = client.post(
            f"{MEMBERS_API}/",
            json={
                "organization_id": membership["organization_id"],
                "user_id": membership["user_id"],
                "role": "admin",
            },
        )
        assert resp.status_code == 400

    def test_invalid_org_rejected(self, client: TestClient, user):
        resp = client.post(
            f"{MEMBERS_API}/",
            json={
                "organization_id": str(uuid.uuid4()),
                "user_id": user["id"],
                "role": "member",
            },
        )
        assert resp.status_code == 400

    def test_invalid_role_rejected(self, client: TestClient, org, user):
        resp = client.post(
            f"{MEMBERS_API}/",
            json={
                "organization_id": org["id"],
                "user_id": user["id"],
                "role": "superadmin",
            },
        )
        assert resp.status_code == 422


class TestListMembers:
    def test_list_by_org_returns_200(self, client: TestClient, membership):
        resp = client.get(f"{MEMBERS_API}/organization/{membership['organization_id']}")
        assert resp.status_code == 200
        ids = [m["id"] for m in resp.json()]
        assert membership["id"] in ids

    def test_list_by_user_returns_200(self, client: TestClient, membership):
        resp = client.get(f"{MEMBERS_API}/user/{membership['user_id']}")
        assert resp.status_code == 200
        ids = [m["id"] for m in resp.json()]
        assert membership["id"] in ids

    def test_list_by_unknown_org_returns_empty(self, client: TestClient):
        resp = client.get(f"{MEMBERS_API}/organization/{uuid.uuid4()}")
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetMember:
    def test_get_by_id_returns_200(self, client: TestClient, membership):
        resp = client.get(f"{MEMBERS_API}/{membership['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == membership["id"]

    def test_unknown_id_returns_404(self, client: TestClient):
        resp = client.get(f"{MEMBERS_API}/{uuid.uuid4()}")
        assert resp.status_code == 404
