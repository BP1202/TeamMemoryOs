# TeamMemoryOS Project Rules

## Project Identity

TeamMemoryOS is an AI-powered operating system for teams.

Its purpose is to capture organizational knowledge, understand team workflows,
preserve historical solutions and decisions, and provide intelligent
assistance to team members.

The system should evolve toward:

- Organizational memory
- Scenario-based knowledge retrieval
- AI-assisted workflows
- Decision intelligence
- Multi-agent collaboration
- Context-aware engineering assistance

---

## Engineering Principles

1. Prefer simple, maintainable solutions over unnecessary complexity.
2. Do not introduce technology only for demonstration purposes.
3. Every AI component must have a clear product purpose.
4. Prefer deterministic logic where an LLM is unnecessary.
5. Minimize external LLM/API usage and unnecessary token consumption.
6. Do not expose secrets, API keys, credentials, or private configuration.
7. Do not silently introduce breaking changes.
8. Preserve existing functionality when modifying code.
9. Keep modules focused and maintainable.
10. Production-quality code is preferred over hackathon shortcuts.

---

## Backend Standards

Backend technology:

- Python
- FastAPI
- PostgreSQL
- pgvector
- SQLAlchemy
- Alembic
- Pydantic / Pydantic Settings
- Docker

Follow clear separation between:

- API layer
- business logic
- data access
- AI/RAG services
- configuration
- models
- workflows

---

## AI Engineering Principles

AI systems should use:

- structured prompts
- deterministic preprocessing
- embeddings where semantic retrieval is required
- RAG when external organizational knowledge is required
- agents only when multi-step reasoning or tool execution is genuinely needed

Never use an LLM where a deterministic implementation is sufficient.

Every AI-generated result should have an explainable source or reasoning path
where practical.

---

## Git Workflow

Never work directly on main.

Development flow:

main
  ↓
dev
  ↓
feature/*
  ↓
Pull Request
  ↓
dev
  ↓
stable release
  ↓
main

Feature branches must be focused on one logical change.

Use meaningful conventional commit messages.

Examples:

feat: add scenario ingestion pipeline
fix: handle missing project configuration
test: add settings validation tests
refactor: separate embedding service
docs: update backend architecture

---

## Testing

Any meaningful backend behavior must have tests.

Before completing a task:

1. Run relevant tests.
2. Check application startup.
3. Check imports.
4. Check formatting/linting where configured.
5. Report failures instead of hiding them.

Never claim a task is complete when validation has not been performed.

---

## Database Safety

Database schema changes must use Alembic migrations.

Never manually modify production schema.

Never delete or reset databases without explicit approval.

---

## Configuration

Environment-specific secrets belong in environment configuration.

Never commit:

- API keys
- passwords
- tokens
- private credentials
- production secrets

Keep `.env.example` updated when configuration variables change.

---

## Bob Behavior

Before modifying code:

1. Inspect relevant existing files.
2. Understand the current architecture.
3. Identify affected components.
4. Make the smallest appropriate change.
5. Run relevant validation.
6. Report exactly what changed.

Do not rewrite unrelated files.

Do not create unnecessary abstractions.

Do not add dependencies without justification.

When uncertain about an architectural decision, explain the tradeoff before making
a large change.