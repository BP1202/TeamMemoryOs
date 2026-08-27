# Sprint 5 — Knowledge Graph Intelligence

## Goal

Build the intelligence layer of TeamMemoryOS by introducing entity extraction, knowledge graph relationships, hybrid retrieval, and explainable memory reasoning.

## Milestones

* 5.1 Entity Extraction Foundation
* 5.2 Knowledge Graph Relationships
* 5.3 Automatic Memory Linking
* 5.4 Hybrid Retrieval Engine
* 5.5 Explainable Retrieval

## Engineering Journal

Append one concise entry after each completed milestone including objective, files changed, validation, security review, AI contribution, and engineering decisions.

---

### Milestone 5.1 — Entity Extraction Foundation

**Branch:** `feat/knowledge-graph-intelligence`

**Objective:** Build the entity extraction foundation — reusable engineering entities that become nodes in the future knowledge graph.

**Problem:** TeamMemoryOS had no structured representation of engineering entities (services, PRs, branches, files, technologies, etc.) — memories were unstructured free text with no node-level intelligence for future graph traversal.

**Solution:** Introduced `Entity` and `MemoryEntity` SQLAlchemy models scoped to organisations, a deterministic regex-based extraction service covering 7 entity types, full CRUD and attachment services, and a complete authenticated API layer with 5 endpoints.

**Files Changed:**
- `backend/app/models/entity.py` — `Entity`, `MemoryEntity` models, `EntityType` enum (9 types)
- `backend/app/models/__init__.py` — registered new models for Alembic autogenerate
- `backend/app/schemas/entity.py` — request/response schemas
- `backend/app/services/entity.py` — CRUD + `get_or_create_entity`, memory attachment
- `backend/app/services/entity_extraction.py` — deterministic extraction (PR, Branch, File, API endpoint, Technology, Service, Repository)
- `backend/app/api/v1/entities.py` — 6 authenticated endpoints including `/extract`
- `backend/app/api/router.py` — registered entities router under `/entities`
- `backend/alembic/versions/54199dae8911_add_entities_and_memory_entities_tables.py` — migration
- `backend/tests/test_entities.py` — 39 tests

**Validation:**
- `alembic upgrade head` applied cleanly
- All imports resolved
- `pytest tests/test_entities.py` — **39/39 passed**
- Full suite — **148/149 passed** (1 pre-existing pagination flake in `test_users.py`, unrelated)

**Security Review:**
- UUID primary keys on both tables
- `organization_id` FK with CASCADE delete enforces tenant isolation
- `UniqueConstraint(org, type, name)` prevents duplicate entity injection
- All endpoints require `get_current_user` JWT auth
- ORM-only queries — no raw SQL
- No secrets or credentials stored or returned
- Duplicate attachment returns 409, not a silent overwrite

**Engineering Decisions:**
- Extraction is fully deterministic — no Granite, no LangChain
- `get_or_create_entity` handles idempotent extraction pipelines
- `_normalise()` canonicalises PR numbers (PR-NNN), branch names (lowercase), and HTTP methods (uppercase) before storage
- HNSW index from migration `581c2cdd5ce2` preserved — autogenerate artefact manually removed from this migration

**Status:** ✅ Complete