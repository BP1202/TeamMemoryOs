---
name: backend-development
description: Build, debug, test, and maintain the TeamMemoryOS FastAPI backend following its architecture, Git workflow, configuration standards, and production engineering practices.
---

# TeamMemoryOS Backend Development Skill

You are working as a senior backend engineer on TeamMemoryOS.

## Mission

Implement backend functionality safely while preserving the project's
architecture, testability, maintainability, and future AI/RAG requirements.

## Before Coding

1. Inspect the relevant backend files.
2. Identify the current architecture.
3. Check existing patterns before introducing new ones.
4. Identify dependencies and side effects.
5. Determine whether tests already exist.

Do not immediately rewrite code.

## Implementation

Use:

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- pgvector
- Alembic

Prefer:

- small modules
- explicit dependencies
- typed functions
- clear service boundaries
- testable business logic
- structured error handling

Avoid unnecessary abstractions.

## Configuration

Use Pydantic Settings for application configuration.

Environment-specific values must come from environment variables or local
environment files.

Never hardcode secrets.

When adding configuration:

1. Add the setting.
2. Update `.env.example`.
3. Provide a safe default when appropriate.
4. Validate startup behavior.
5. Add tests for required configuration.

## API Development

For every new API endpoint:

1. Define request schema.
2. Define response schema.
3. Validate input.
4. Implement business logic in an appropriate service.
5. Handle expected errors.
6. Add tests.
7. Verify OpenAPI generation.

Do not place complex business logic directly inside route handlers.

## Database

Use SQLAlchemy models and Alembic migrations.

Before modifying schema:

1. Inspect existing models.
2. Determine relationships.
3. Consider indexes and constraints.
4. Create a migration.
5. Test the migration.

Never silently reset the database.

## AI / RAG Integration

Use an LLM only when it provides meaningful value.

Prefer:

deterministic processing
→ retrieval
→ ranking
→ LLM reasoning

rather than sending all available information directly to an LLM.

Keep AI providers behind service interfaces so providers can be replaced.

## Debugging

When debugging:

1. Reproduce the failure.
2. Read the complete error.
3. Identify the first meaningful exception.
4. Trace the failure to its source.
5. Inspect surrounding configuration/code.
6. Make the smallest fix.
7. Re-run the failing command.
8. Run relevant regression tests.

Do not mask errors with broad exception handling.

## Validation

Before declaring success:

- application starts
- imports succeed
- relevant tests pass
- changed functionality works
- no unrelated behavior is broken

Report:

### Changed
- files modified
- behavior implemented

### Validation
- commands executed
- results

### Remaining
- known limitations
- unresolved issues

## Git

Do not commit or push unless explicitly requested.

Keep changes scoped to the current feature branch.

Use conventional commit messages when asked to create commits.

## Development Journal Rule

After completing any task, add a concise entry to the relevant development journal.

Use exactly this format:

- **Problem:** One sentence describing the issue/task.
- **Solution:** 1–2 sentences describing the key fix or implementation.
- **Branch:** The branch where the work was completed.

Do not copy the full AI conversation, terminal logs, reasoning, or verbose explanations into the journal.

Example:

- **Problem:** Backend startup failed because `PROJECT_NAME` was missing and `FastAPI` was incorrectly referenced.
- **Solution:** Added a safe `PROJECT_NAME` default, corrected `FASTAPI` to `FastAPI`, and verified application startup.
- **Branch:** `feat/back-setup`