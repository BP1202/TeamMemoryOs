# AI Engineering Copilot Skill

## Purpose

Build the TeamMemoryOS engineering assistant using GraphRAG, deterministic engineering tooling, and IBM Granite.

The copilot understands repositories, commits, pull requests, debugging sessions, codebase knowledge, and engineering conversations.

---

## Scope

Sprint 6 implements:

* Git Repository Intelligence
* Pull Request Guardian
* Terminal Memory Copilot
* AI Codebase Search
* Engineering Conversation Engine

---

## Engineering Rules

1. Parse engineering artifacts deterministically before invoking Granite.
2. Reuse HybridRetriever for every retrieval workflow.
3. Every repository artifact becomes MemoryEntry + Entity + Graph relationships.
4. Preserve organization isolation on every query.
5. Keep AI explainable using citations, graph paths, and confidence scores.

---

## Architecture Rules

Never duplicate retrieval logic.

Always reuse:

* HybridRetriever
* ExplanationBuilder
* PromptBuilder
* GraniteProvider interface

Keep services independent from API routes.

---

## Validation Rules

Every milestone must include:

* Alembic validation (if schema changes).
* API validation.
* Pytest coverage.
* Security review.
* Journal update.

Never mark a milestone complete without validation.