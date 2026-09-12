# Sprint Journal: AI-005 — LangChain Production RAG Pipeline

**Sprint ID:** AI-005  
**Module:** LangChain Retrieval Pipeline & LCEL Orchestration  
**Status:** Completed  
**Branch:** `feature/langchain-production-rag`  
**Date:** September 12, 2026  
**Engineer:** Senior AI/ML Engineer & Production LLMOps Architect  

---

## 1. Goal

The objective of Sprint AI-005 was to replace custom RAG orchestration in TeamMemoryOS with a **production-grade LangChain Retrieval Pipeline** utilizing local Ollama models (`llama3.1:8b`, `nomic-embed-text`) and the existing PostgreSQL 17 + pgvector memory engine.

This implementation transitions TeamMemoryOS from procedural function orchestration to modular, composable, and observable **LangChain Expression Language (LCEL)** pipelines with full streaming, structured parsing, organization isolation, and comprehensive metadata preservation.

---

## 2. Architecture & Pipeline Design

The LangChain RAG pipeline is built using a modern LCEL `RunnableSequence` architecture:

```
[User Question]
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ TeamMemoryPGVectorRetriever (BaseRetriever)                 │
│  - Organization Isolation (organization_id)                 │
│  - Cosine Similarity Search (pgvector <=> distance)         │
│  - Scenario / Namespace Filters                             │
│  - Metadata: chunk_hash, source, file_path, lines, symbols  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                      [List[Document]]
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Prompt Assembly (ChatPromptTemplate)                        │
│  - Specialized Engineering Chat / Incident / Repo / PR      │
│  - Strict Grounding Rules & Anti-Hallucination Constraints   │
│  - Formatted Context & Numbered Citations ([1], [2])        │
└──────────────────────────────┬──────────────────────────────┘
                               │
                       [PromptValue]
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Chat Model Layer (ChatOllama / StubChatModel Fallback)      │
│  - Configurable Temperature, Max Tokens, Timeout            │
│  - Sync (.invoke), Async (.ainvoke), Stream (.stream)       │
│  - Resilient Fallback to Stub in Offline Test Environments  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                        [AIMessage]
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ TeamMemoryOutputParser (BaseOutputParser)                   │
│  - Structured TeamMemoryRAGOutput                           │
│  - Extracted Citation Markers & Rich Memory Metadata        │
│  - Confidence Scoring & Participating Agents Attribution    │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. LangChain Components Used

1. **`ChatOllama` (`langchain_ollama` / `langchain_core.language_models.chat_models`)**:
   - Manages communication with local Ollama daemon.
   - Provides native token streaming, prompt grounding, and configurable hyperparameters.
2. **`BaseRetriever` (`langchain_core.retrievers.BaseRetriever`)**:
   - `TeamMemoryPGVectorRetriever` encapsulates pgvector similarity search, multi-tenant isolation, and `Document` transformation.
3. **`ChatPromptTemplate` (`langchain_core.prompts`)**:
   - 4 specialized production prompt templates:
     - `ENGINEERING_CHAT_PROMPT`: Architecture and general engineering decisions.
     - `INCIDENT_INVESTIGATION_PROMPT`: Root cause analysis, post-mortems, and runbook triage.
     - `REPOSITORY_ANALYSIS_PROMPT`: Code navigation, AST hierarchies, and module boundaries.
     - `PULL_REQUEST_REVIEW_PROMPT`: Code diff evaluation against architectural and security standards.
4. **`RunnableSequence` & LCEL (`langchain_core.runnables`)**:
   - `RunnableLambda`, `RunnablePassthrough`, and pipe syntax (`|`) create fully typed and composable pipelines.
5. **`BaseOutputParser` (`langchain_core.output_parsers`)**:
   - `TeamMemoryOutputParser` parses LLM generation, pairs it with retrieved documents, extracts citation tags, and computes grounding confidence.
6. **Streaming Protocol (`langchain_core.messages.AIMessageChunk`)**:
   - Server-Sent Events (SSE) streaming engine yielding `metadata`, `citation`, `token`, and `done` events.

---

## 4. File Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `backend/requirements.txt` | Modified | Added `langchain`, `langchain-core`, `langchain-community`, `langchain-ollama`, `langchain-postgres`. |
| `backend/app/langchain/__init__.py` | Created | Package initialization exposing public interfaces and factories. |
| `backend/app/langchain/chat_model.py` | Created | ChatOllama factory with configuration and `StubChatModel` fallback. |
| `backend/app/langchain/retriever.py` | Created | `TeamMemoryPGVectorRetriever` for pgvector semantic search. |
| `backend/app/langchain/prompt_templates.py` | Created | ChatPromptTemplates for Engineering, Incident, Repo, and PR review workflows. |
| `backend/app/langchain/output_parser.py` | Created | `TeamMemoryOutputParser` and `TeamMemoryRAGOutput` schema. |
| `backend/app/langchain/chains.py` | Created | `build_rag_chain`, `run_rag_chain`, `arun_rag_chain` LCEL pipelines. |
| `backend/app/langchain/streaming.py` | Created | `stream_rag_chain` and `astream_rag_chain` SSE generators. |
| `backend/app/memory/rag_generation.py` | Modified | Replaced procedural generation with LangChain pipeline while preserving backward compatibility. |
| `backend/app/memory/prompt_builder.py` | Modified | Integrated with LangChain prompt template utilities. |
| `backend/app/schemas/chat.py` | Modified | Added `scenario_type` field to `ChatAskRequest`. |
| `backend/app/api/v1/chat.py` | Modified | Added `POST /api/v1/chat` root route alongside `/ask` and `/stream`. |
| `backend/tests/test_langchain_rag.py` | Created | Comprehensive 19-test suite for all LangChain RAG capabilities. |

---

## 5. API Changes

### `POST /api/v1/chat` & `POST /api/v1/chat/ask`
- **Request Body (`ChatAskRequest`)**:
  ```json
  {
    "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "question": "What database architecture did we decide on?",
    "top_k": 5,
    "scenario_id": null,
    "scenario_type": "engineering",
    "use_hybrid": false
  }
  ```
- **Response Body (`ChatAskResponse`)**:
  ```json
  {
    "answer": "Based on team memory, PostgreSQL 17 with pgvector was selected [1]...",
    "citations": [
      "[1] decision — Adopt PostgreSQL 17 (id: 0b12d7b5-577b-480d-84b0-7fd5490a9a31)"
    ],
    "retrieved_memory_count": 1,
    "provider_used": "ollama",
    "retrieval_mode": "semantic",
    "explanation": null
  }
  ```

### `POST /api/v1/chat/stream`
- Yields standard SSE events:
  - `data: {"type": "metadata", "citations": [...], "retrieved_memory_count": 2, "provider_used": "ollama", "retrieval_mode": "semantic"}`
  - `data: {"type": "citation", "citation": "[1] decision — Adopt PostgreSQL 17 (id: ...)"}`
  - `data: {"type": "token", "token": "Based "}`
  - `data: {"type": "token", "token": "on "}`
  - `data: {"type": "done", "answer": "...", "citations": [...]}`

---

## 6. Test Results

### Dedicated Test Suite (`tests/test_langchain_rag.py`):
- `TestLangChainChatModel`:
  - `test_stub_chat_model_sync_invoke`: PASSED
  - `test_stub_chat_model_async_invoke`: PASSED
  - `test_stub_chat_model_stream`: PASSED
  - `test_get_chat_model_factory`: PASSED
- `TestPGVectorRetriever`:
  - `test_retriever_returns_top_k_with_metadata`: PASSED
  - `test_retriever_ainvoke`: PASSED
- `TestPromptTemplates`:
  - `test_prompt_template_selector`: PASSED
  - `test_format_documents_helpers`: PASSED
  - `test_empty_documents_formatting`: PASSED
- `TestRunnablePipeline`:
  - `test_run_rag_chain_sync`: PASSED
  - `test_arun_rag_chain_async`: PASSED
- `TestStreamingEngine`:
  - `test_stream_rag_chain_events`: PASSED
  - `test_astream_rag_chain_events`: PASSED
- `TestOutputParser`:
  - `test_output_parser_structure`: PASSED
- `TestOrganizationIsolationAndFallback`:
  - `test_organization_isolation`: PASSED
  - `test_empty_retrieval_fallback`: PASSED
- `TestChatEndpoints`:
  - `test_post_chat_root`: PASSED
  - `test_post_chat_ask_alias`: PASSED
  - `test_post_chat_stream`: PASSED

**Result:** 19/19 Passed (100%).

### Full Regression Suite:
- `tests/test_langchain_rag.py`: 19 passed
- `tests/test_chunking.py`: 19 passed
- `tests/test_embedding_provider.py`: 13 passed
- `tests/test_git_indexer.py`: 16 passed
- `tests/test_ollama_provider.py`: 15 passed
- `tests/test_chat.py`: 29 passed
- Total: **111/111 Passed (100%)**.

---

## 7. Interview Knowledge: LangChain in Production

1. **Why LCEL (LangChain Expression Language)?**
   - LCEL provides unified sync, async, and streaming APIs over the `Runnable` protocol without changing application code.
   - Declarative composition allows declarative retry logic, fallbacks, parallel retrieval branches, and automatic tracing.
2. **Deterministic Fallbacks in Production LLMOps:**
   - Production systems cannot crash when downstream model daemons temporarily restart or drop connections. Using `.with_fallbacks([StubChatModel(...)])` ensures continuous uptime and graceful error mitigation.
3. **Multi-Tenant Retrieval Isolation:**
   - In B2B SaaS, security isolation is enforced at the database query level inside the custom `BaseRetriever` by mandating `organization_id` filters in the pgvector WHERE clause before computing or ordering similarities.
4. **Metadata Preservation & Citations:**
   - High-precision RAG applications must carry AST symbols, line numbers, file paths, and chunk hashes throughout the pipeline so the final output parser can construct rich citations and audit trails.

---

## 8. Future Improvements

1. **LangGraph StateGraph Integration:** Expand the single Runnable sequence into a multi-step agentic graph supporting query rewriting, self-correction, and tool routing.
2. **Context Compression / Re-ranking:** Integrate a local Cross-Encoder re-ranker (e.g., `bge-reranker-base`) as a LangChain `ContextualCompressionRetriever`.
3. **OpenTelemetry / LangSmith Tracing:** Connect production tracing hooks for latency profiling and hallucination evaluation.
