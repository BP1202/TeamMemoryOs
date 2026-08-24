# Sprint 03 — Team Identity & Security Foundation

**Branch:** feat/team-identity

## Sprint Goal

Build the identity layer for TeamMemoryOS including Users, Organization Membership, RBAC foundation, and authentication-ready APIs.

## Planned Tasks

* [x] Task 3.1 — User Model
* [x] Task 3.2 — Organization Membership Model
* [x] Task 3.3 — User & Member Schemas
* [x] Task 3.4 — User & Member CRUD APIs
* [x] Task 3.5 — Authentication Foundation

## Engineering Log

Task entries will be appended after successful validation.

---

### Task 3.1.1 — User Model

**Branch:** feat/team-identity
**Problem:** No `User` model existed; the identity layer had no persistence target for user records.
**Solution:** Created `backend/app/models/user.py` with `User(Base)` mirroring the `Organization` pattern — UUID primary key, `full_name`, `email` (unique, 320-char), `password_hash`, `is_active`, and timezone-aware `created_at`/`updated_at` timestamps using `server_default=text("now()")` and `onupdate` UTC lambda. Exported `User` (alongside `Organization`) from `backend/app/models/__init__.py`.
**Validation:** Imported `User` from `app.models`; confirmed `['organizations', 'users']` registered in `Base.metadata.tables`. All assertions passed.
**Status:** ✅ Complete

---

### Task 3.1.2 — Organization Membership Model

**Branch:** feat/team-identity
**Problem:** No model existed to associate users with organizations or carry role information.
**Solution:** Created `backend/app/models/organization_member.py` with `OrganizationMember(Base)` — UUID primary key; `organization_id` and `user_id` as `ForeignKey` columns (both `CASCADE` on delete); `MemberRole` string enum (`owner`, `admin`, `member`, `viewer`) stored as a PostgreSQL `Enum` type; `is_active` boolean defaulting `True`; `joined_at` timezone-aware timestamp with `server_default=text("now()")`. Composite `UniqueConstraint` on `(organization_id, user_id)` named `uq_organization_members_organization_id_user_id` following the project naming convention. Exported `OrganizationMember` and `MemberRole` from `backend/app/models/__init__.py`.
**Validation:** Imported `OrganizationMember` and `MemberRole`; confirmed `['organizations', 'organization_members', 'users']` in `Base.metadata.tables`; asserted all columns present; confirmed composite unique constraint `uq_organization_members_organization_id_user_id`. All assertions passed.
**Status:** ✅ Complete

---

### Task 3.1.3 — Alembic Migration: users & organization_members

**Branch:** feat/team-identity
**Problem:** `users` and `organization_members` tables existed only in SQLAlchemy metadata; the database had no corresponding schema. `alembic/env.py` only imported `Organization`, so autogenerate was blind to the two new models.
**Solution:** Replaced the single-model import in `alembic/env.py` with `import app.models` so all three models register with `Base.metadata` before autogenerate runs. Generated migration `24d27086e1c5` (revises `e512c1bbda6f`): creates `users` (7 columns, PK, unique email) then `organization_members` (6 columns, PK, `memberrole` enum, FKs to `organizations.id` and `users.id` both with `ondelete=CASCADE`, composite unique `(organization_id, user_id)`). All constraint names use `op.f()` for portability.
**Validation:** `alembic upgrade head` applied cleanly. Live database inspection confirmed `['organizations', 'users', 'organization_members']` present; all columns, both FKs, composite unique constraint, and `alembic_version = 24d27086e1c5` verified. All assertions passed.
**Status:** ✅ Complete

---

### Task 3.3 — User & OrganizationMember Pydantic Schemas

**Branch:** feat/team-identity
**Problem:** No Pydantic schemas existed for `User` or `OrganizationMember`; API layer had no validated I/O contracts for the identity resources.
**Solution:** Created `backend/app/schemas/user.py` with `UserBase`, `UserCreate` (adds `password` field, 8–128 chars), and `UserRead` (excludes `password_hash`, includes timestamps). Created `backend/app/schemas/organization_member.py` with `OrganizationMemberBase`, `OrganizationMemberCreate`, and `OrganizationMemberRead`. Used `EmailStr` for email validation. Updated `backend/app/schemas/__init__.py` to export all six new schema classes.
**Files Updated:** `backend/app/schemas/user.py`, `backend/app/schemas/organization_member.py`, `backend/app/schemas/__init__.py`
**Validation:** Import validation passed; all schemas importable from `app.schemas`.
**Status:** ✅ Complete

---

### Task 3.4 — User & Member Service Layer

**Branch:** feat/team-identity
**Problem:** No service functions existed to create or query `User` and `OrganizationMember` records.
**Solution:** Created `backend/app/services/user.py` with `create_user` (SHA-256 + random salt password hashing stub), `get_user_by_id`, `get_user_by_email`, `get_users`. Created `backend/app/services/organization_member.py` with `create_member`, `get_member_by_id`, `get_members_by_organization`, `get_members_by_user`. All functions use SQLAlchemy ORM `select` — no raw SQL.
**Files Updated:** `backend/app/services/user.py`, `backend/app/services/organization_member.py`
**Validation:** Services exercised through full API test suite — all 19 tests passed.
**Status:** ✅ Complete

---

### Task 3.4 — User & Member REST API Routes

**Branch:** feat/team-identity
**Problem:** No API endpoints existed for User or OrganizationMember resources.
**Solution:** Created `backend/app/api/v1/users.py` (POST `/users/`, GET `/users/`, GET `/users/{user_id}`) and `backend/app/api/v1/members.py` (POST `/members/`, GET `/members/organization/{org_id}`, GET `/members/user/{user_id}`, GET `/members/{member_id}`). Duplicate detection returns HTTP 400; missing records return 404; `IntegrityError` (FK violation or composite unique) caught and rolled back at route level. Registered both routers in `backend/app/api/router.py` under `/users` and `/members` tags.
**Files Updated:** `backend/app/api/v1/users.py`, `backend/app/api/v1/members.py`, `backend/app/api/router.py`
**Validation:** `pytest tests/ -v` — 19/19 tests passed (10 member tests, 9 user tests). Routes confirmed in Swagger at `/api/v1/users` and `/api/v1/members`.
**Security:** Input validated via Pydantic; `password_hash` excluded from responses; no secrets logged; ORM only; risk level **Low**.
**Status:** ✅ Complete

---

### Task 3.5 — Authentication Foundation

**Branch:** feat/team-identity
**Objective:** Implement full JWT authentication: password hashing, token issuance, protected endpoint, and `get_current_user` dependency.
**Problem:** User passwords were stored using an insecure SHA-256 + salt stub; no login endpoint or token-based access control existed.
**Solution:**
- Created `backend/app/core/security.py` — bcrypt `hash_password` / `verify_password` (direct `bcrypt` library, no passlib) and `create_access_token` / `decode_access_token` via `python-jose`.
- Created `backend/app/schemas/auth.py` — `Token` and `TokenPayload` Pydantic schemas.
- Created `backend/app/services/auth.py` — `authenticate_user` and `login` service functions; business logic kept out of routes.
- Updated `backend/app/services/user.py` — replaced SHA-256 stub with `hash_password` from `security.py`.
- Created `backend/app/api/v1/auth.py` — `POST /api/v1/auth/login` OAuth2 password flow endpoint.
- Created `backend/app/api/deps.py` — `get_current_user` dependency using `OAuth2PasswordBearer`.
- Updated `backend/app/api/v1/users.py` — added `GET /api/v1/users/me` protected endpoint.
- Updated `backend/app/api/router.py` — registered auth router under `/auth`.
- Updated `backend/app/core/settings.py` — added `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`.
- Updated `backend/.env.example` — documented new JWT env variables.
**Files Updated:** `app/core/security.py`, `app/core/settings.py`, `app/schemas/auth.py`, `app/services/auth.py`, `app/services/user.py`, `app/api/v1/auth.py`, `app/api/v1/users.py`, `app/api/deps.py`, `app/api/router.py`, `.env.example`, `requirements.txt`, `tests/test_auth.py`
**Validation:** `pytest tests/ -v` — 28/28 passed (9 auth, 10 member, 9 user). Login returns signed JWT; `GET /users/me` returns 200 with valid token and 401 without.
**Security Audit:**
- Input Validation: ✅ Pydantic on all endpoints
- Secrets Exposure: None — `password_hash` never returned; JWT secret loaded from env
- Authorization Impact: High — authentication layer introduced; all future protected routes depend on this
- Risk Level: **Medium** (new auth surface; mitigated by bcrypt, JWT expiry, and 401 on all failure paths)
**Status:** ✅ Complete
