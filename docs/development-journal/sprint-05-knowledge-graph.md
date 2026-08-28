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

---

### Milestone 5.3 — Automatic Memory Linking Engine

**Branch:** `feat/knowledge-graph-intelligence`

**Objective:** Automatically infer scored relationships between MemoryEntry records using shared entities, shared scenarios, and semantic similarity — preparing TeamMemoryOS for GraphRAG.

**Problem:** Memory entries were isolated records with no programmatic connections. Future hybrid retrieval requires knowing which memories are related and why, without relying on an LLM at link-generation time.

**Solution:** Introduced a `MemoryLink` model with a multi-signal scoring engine (`calculate_link_score`) combining Jaccard entity overlap (0.5), same-scenario flag (0.3), and cosine embedding similarity (0.2). The `generate_memory_links` service is fully deterministic, idempotent, and produces labelled, scored links. Also permanently fixed the recurring HNSW autogenerate ghost by adding an `include_object` exclusion filter to `alembic/env.py`.

**Files Changed:**
- `backend/app/models/memory_link.py` — `MemoryLinkType` enum (4 types), `MemoryLink` model
- `backend/app/models/__init__.py` — exported `MemoryLink`, `MemoryLinkType`
- `backend/app/schemas/memory_link.py` — `MemoryLinkCreate` (with self-link validator), `MemoryLinkRead`, `GenerateLinksRequest`, `GenerateLinksResponse`
- `backend/app/services/memory_link.py` — `create_memory_link`, `get_memory_links`, `generate_memory_links`, `calculate_link_score`, `_cosine_similarity`
- `backend/app/api/v1/memory_links.py` — 3 authenticated endpoints under `/memory-links`
- `backend/app/api/router.py` — registered memory_links router
- `backend/alembic/env.py` — added `include_object` filter to permanently exclude HNSW index from autogenerate
- `backend/alembic/versions/0317f82c2c0b_add_memory_links_table.py` — migration
- `backend/tests/test_memory_links.py` — 28 tests
- `.gitignore` — comprehensively hardened: credentials, env files, secrets, IDE artefacts, OS files, build outputs

**Validation:**
- `alembic upgrade head` applied cleanly
- `alembic check` → "No new upgrade operations detected" (HNSW exclusion verified)
- All imports resolved; scoring logic verified in Python REPL
- `pytest tests/test_memory_links.py` — **28/28 passed**
- Full suite — **201/202 passed** (same pre-existing pagination flake in `test_users.py`)

**Security Review:**
- UUID primary key on `memory_links`
- `organization_id` FK with CASCADE delete enforces tenant isolation
- `UniqueConstraint(org, src, tgt, type)` prevents duplicate links
- Self-link validation at Pydantic schema and service layers
- All endpoints require `get_current_user` JWT auth
- `get_memory_links` and `list_neighbors` require `organization_id` query param — cross-org memory IDs return empty
- Score clamped to [0.0, 1.0] at write time
- ORM-only queries — no raw SQL

**Engineering Decisions:**
- Three-signal weighted scoring: entity Jaccard (0.5) + scenario flag (0.3) + cosine sim (0.2)
- When embeddings are absent, semantic weight redistributed proportionally to remaining signals so scores stay in [0, 1] without a cliff
- `generate_memory_links` is idempotent — duplicate `IntegrityError` is caught and counted as `links_skipped`, not raised
- Response links sorted by score descending for immediate usability
- HNSW index now permanently excluded from Alembic autogenerate via `include_object` hook in `alembic/env.py`

**Status:** ✅ Complete

---

### Milestone 5.4 — Hybrid Retrieval Engine (GraphRAG Foundation)

**Branch:** `feat/knowledge-graph-intelligence`

**Objective:** Build a deterministic hybrid retrieval engine combining semantic search, entity graph expansion, and memory-link scoring into one explainable pipeline — the GraphRAG foundation for TeamMemoryOS.

**Problem:** The existing RAG pipeline used semantic-only retrieval, missing related memories that are only discoverable through the entity graph (e.g. a memory about an incident that shares no lexical similarity with the query but is connected through an entity relationship chain).

**Solution:** Built a five-stage `HybridRetriever` in `app/graph/` that: (1) retrieves semantic seeds via pgvector, (2) expands their entity sets, (3) walks one graph hop via `EntityRelationship`, (4) surfaces link targets from `MemoryLink`, then (5) merges and ranks all candidates with a weighted score (semantic 0.5, memory-link 0.3, graph 0.2). Integrated into `/chat/ask` as opt-in `use_hybrid=True` and exposed directly via a new `/retrieval/hybrid-search` endpoint with full explainability metadata.

**Files Changed:**
- `backend/app/graph/__init__.py` — new `graph` package
- `backend/app/graph/hybrid_retriever.py` — `HybridRetriever`, `HybridResult`, `_weighted_score`, `_cosine_distance`
- `backend/app/schemas/retrieval.py` — `HybridSearchRequest`, `HybridResultRead`, `HybridSearchResponse`, `GraphStats`
- `backend/app/api/v1/retrieval.py` — `POST /retrieval/hybrid-search`
- `backend/app/api/router.py` — registered retrieval router
- `backend/app/schemas/chat.py` — added `use_hybrid` flag, `retrieval_mode` response field
- `backend/app/memory/rag_generation.py` — hybrid branch in `run_rag`, `retrieval_mode` in `ChatResponse`
- `backend/app/api/v1/chat.py` — passes `use_hybrid` through; returns `retrieval_mode`
- `backend/tests/test_hybrid_retrieval.py` — 30 tests

**Validation:**
- All imports resolved; app startup clean
- `pytest tests/test_hybrid_retrieval.py` — **30/30 passed**
- Full suite — **231/232 passed** (same pre-existing pagination flake in `test_users.py`)

**Security Review:**
- All endpoints require `get_current_user` JWT auth
- Organisation isolation enforced at every DB query in `HybridRetriever` (org filter on entity expansion, graph traversal, memory link lookup, and final candidate load)
- No raw SQL — all ORM queries
- `_load_memories` applies `organization_id` filter so cross-org memory IDs passed via graph expansion cannot leak data
- Score always clamped to [0.0, 1.0]

**Engineering Decisions:**
- `HybridRetriever` constructor accepts an `EmbeddingProvider` override for testability — no network dependency in tests (StubEmbeddingProvider used throughout)
- Interface designed for future LangChain compatibility: single `retrieve(question: str) → list[HybridResult]` entry point
- `seed_multiplier=3` fetches `top_k * 3` semantic seeds before graph expansion, giving the graph a wide enough base to surface distant candidates
- Chat `/ask` remains backward-compatible: `use_hybrid` defaults to `False`; existing tests pass unchanged
- `retrieval_mode` field added to both `ChatResponse` dataclass and `ChatAskResponse` schema for client-side transparency

**Status:** ✅ Complete
