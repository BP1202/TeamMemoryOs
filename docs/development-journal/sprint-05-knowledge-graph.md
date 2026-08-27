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

---

### Milestone 5.2 — Knowledge Graph Relationship Engine

**Branch:** `feat/knowledge-graph-intelligence`

**Objective:** Build the typed directed relationship layer of the knowledge graph — connecting entity nodes with explainable, organisation-scoped edges.

**Problem:** Entities from Milestone 5.1 existed as isolated nodes with no connections. The knowledge graph required a relationship layer to express how engineering entities interact (e.g. a PR *fixes* an incident, a service *depends on* a technology).

**Solution:** Introduced `RelationshipType` enum (7 types) and `EntityRelationship` model with a unique constraint on (org, src, tgt, type), plus a full service layer including bidirectional neighbor traversal and an authenticated API layer with 4 endpoints.

**Files Changed:**
- `backend/app/models/entity.py` — added `RelationshipType` enum and `EntityRelationship` model
- `backend/app/models/__init__.py` — exported `EntityRelationship`, `RelationshipType`
- `backend/app/schemas/relationship.py` — `RelationshipCreate` (with self-loop validator), `RelationshipRead`, `NeighborRead`
- `backend/app/services/relationship.py` — `create_relationship`, `get_relationship_by_id`, `list_relationships_for_entity`, `list_neighbors` (bidirectional, org-scoped)
- `backend/app/api/v1/relationships.py` — 4 authenticated endpoints
- `backend/app/api/router.py` — registered relationships router under `/relationships`
- `backend/alembic/versions/f275a098249d_add_entity_relationships_table.py` — migration
- `backend/tests/test_relationships.py` — 25 tests

**Validation:**
- `alembic upgrade head` applied cleanly
- All imports resolved
- `pytest tests/test_relationships.py` — **25/25 passed**
- Full suite — **173/174 passed** (same pre-existing pagination flake in `test_users.py`)

**Security Review:**
- UUID primary key on `entity_relationships`
- `organization_id` FK with CASCADE delete enforces tenant isolation
- `UniqueConstraint(org, src, tgt, type)` prevents duplicate edges
- Self-loop validation at both Pydantic schema level and service layer
- All endpoints require `get_current_user` JWT auth
- `list_neighbors` scopes results to `organization_id` query param — cross-org entity IDs return empty
- ORM-only queries — no raw SQL
- Invalid entity FKs produce 409, not leaking entity existence

**Engineering Decisions:**
- Relationships are directed: `source → target` with explicit `direction` field in `NeighborRead`
- `list_neighbors` returns both incoming and outgoing in a single call for efficient graph display
- Stable sort on (direction, type, name) gives deterministic, human-readable ordering
- No graph traversal algorithms introduced — neighbor lookup is single-hop only (reserved for Milestone 5.4)
- HNSW index autogenerate artefact removed again — permanent fix should be added to `env.py` exclude list in a future migration housekeeping task

**Status:** ✅ Complete
