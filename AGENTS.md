# TeamMemoryOS — AI Engineering Handbook

## Project Mission

TeamMemoryOS is an AI Operating System for Engineering Teams.

The platform provides persistent engineering memory, AI coworkers, workflow orchestration, and organization-aware intelligence using FastAPI, PostgreSQL, pgvector, Alembic, Docker, and IBM Granite.

---

## AI Development Philosophy

AI is used as an engineering assistant, not as an autonomous developer.

Every feature follows:

1. Understand the existing architecture.
2. Design before implementation.
3. Implement the smallest correct change.
4. Validate functionality.
5. Run a security review.
6. Record engineering journal entry.

---

## Technology Stack

* FastAPI
* SQLAlchemy 2.x
* PostgreSQL 17
* pgvector
* Alembic
* Docker Compose
* Pydantic Settings
* IBM Granite
* IBM Bob

---

## Backend Architecture

backend/
app/
api/
core/
db/
models/
schemas/
services/
memory/
agents/
security/
workflows/

---

## Branch Strategy

* `main` → Stable releases.
* `dev` → Integration branch.
* `feat/<feature-name>` → Individual sprint feature development.

Examples:

* feat/backend-foundation
* feat/database-schema
* feat/team-identity

---

## Engineering Workflow

Every task follows:

Design → Test Plan → Implement → Validate → Security Review → Journal

No task is considered complete without successful validation.

---

## Security Principles

* UUID primary keys.
* Passwords stored only as hashes.
* Environment variables for secrets.
* ORM only (no raw SQL unless justified).
* Organization-scoped authorization.
* Timezone-aware timestamps.
* Audit-friendly database models.

---

## AI Optimization Principles

IBM Bob is configured using reusable project skills and rules.

Avoid repeating prompts by using `.bob/skills`.

Engineering decisions are documented under `docs/architecture` and `docs/ai-decisions`.

---

## Documentation Standards

* `docs/development-journal/` → Sprint logs.
* `docs/architecture/` → Architecture decisions.
* `docs/security/` → Security standards.
* `docs/ai-decisions/` → IBM AI usage and optimization decisions.

---

## Validation Standard

Every completed task must include:

* Functional validation.
* Database/API validation (when applicable).
* Security review summary.
* Engineering journal entry.
