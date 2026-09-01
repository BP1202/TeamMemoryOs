# TeamMemoryOS Project Rules

## Project Identity

TeamMemoryOS is an AI Operating System for Engineering Teams.

The platform captures organizational knowledge, preserves engineering decisions, enables intelligent memory retrieval, and powers AI-assisted workflows through secure, context-aware agents.

Core product pillars:

* Organizational Memory
* Knowledge Retrieval (RAG + pgvector)
* AI Workflow Automation
* Decision Intelligence
* Multi-Agent Collaboration
* Context-Aware Engineering Assistance

---

## Engineering Principles

1. Build production-quality software, not hackathon shortcuts.
2. Prefer simple, maintainable solutions over unnecessary complexity.
3. Every AI feature must solve a real product problem.
4. Use deterministic logic whenever an LLM is unnecessary.
5. Minimize token usage through reusable skills, rules, and context.
6. Preserve existing functionality unless the task explicitly changes it.
7. Do not modify unrelated files.
8. Security and validation are required for every completed feature.

---

## Backend Architecture

**Stack**

* FastAPI
* SQLAlchemy 2.x
* PostgreSQL 17 + pgvector
* Alembic
* Pydantic Settings
* Docker Compose

**Architecture Layers**

API → Schemas → Services → Models → Database

Keep business logic inside services, not routes. Keep configuration centralized in `app/core`.

---

## AI Engineering Standards

Use AI intentionally.

* Use structured prompts and reusable Bob skills.
* Use RAG only for organizational knowledge retrieval.
* Use embeddings only where semantic search is required.
* Use agents only for genuine multi-step reasoning or tool execution.
* Every AI output should have a traceable reasoning or retrieval path where practical.

Avoid using an LLM for deterministic tasks.

---

## Development Workflow (TDD)

Every feature follows:

**Design → Test Plan → Implement → Validate → Security Review → Journal**

Rules:

* Implement one logical task at a time.
* Make the smallest appropriate change.
* Validate before marking a task complete.
* Fix root causes, not symptoms.

---

## Validation Rules

Before completing a task, run only the relevant validations.

Examples:

* Application import/startup.
* Database session or Alembic validation.
* API/TestClient validation.
* Unit or integration tests.

Never report success without successful validation.

---

## Security Standards

* UUID primary keys for public entities.
* Hash passwords; never store plaintext credentials.
* Validate all external input with Pydantic.
* Never expose secrets, tokens, or passwords in logs or responses.
* Keep tenant (organization) data isolated.
* Store secrets only through environment configuration.

Update `.env.example` whenever configuration changes.

---

## Database Rules

* Schema changes must use Alembic migrations.
* Do not manually modify database schema.
* Do not delete or reset databases without explicit approval.
* Reuse existing SQLAlchemy `Base` and naming conventions.

---

## Git Workflow

Never develop directly on `main`.

`main → dev → feat/<feature> → Pull Request → dev → main`

Use one feature branch per logical feature.

Use conventional commits:

* `feat:`
* `fix:`
* `refactor:`
* `test:`
* `docs:`

---

## IBM Bob Behavior

Before modifying code, Bob must:

1. Inspect relevant files.
2. Understand the current architecture.
3. Identify affected components.
4. Make the smallest appropriate implementation.
5. Run relevant validation.
6. Report changed files, validation results, and security impact.

Bob must not rewrite unrelated code, introduce unnecessary dependencies, or invent architecture outside the requested scope.

---

## Development Journal Rule

Every completed task appends one concise entry to the active sprint journal.

Include only:

* Task
* Branch
* Problem
* Solution
* Validation
* Status

Keep entries short, chronological, and never edit previous completed logs.