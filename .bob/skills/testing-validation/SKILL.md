# Testing & Validation Skill

## Purpose

Validate TeamMemoryOS features before they are considered complete.

## Development Standard

Follow:

Design → Test Plan → Implement → Validate

## Validation Types

Choose only the validations relevant to the task.

Examples:

* Import validation.
* Alembic validation.
* Database session validation.
* FastAPI TestClient validation.
* Pytest unit test.
* Integration/API validation.

## Failure Workflow

1. Reproduce the issue.
2. Identify the root cause.
3. Apply the smallest fix.
4. Re-run validation.
5. Report the result.

## Completion Rule

Never mark a task complete unless validation succeeds.