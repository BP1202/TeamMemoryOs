"""Comprehensive tests for Intelligent Chunking Engine and Preview API."""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.chunking import (
    CodeChunker,
    MarkdownChunker,
    RecursiveChunker,
    chunk_text,
    chunk_to_memory_meta,
    get_chunker,
)
from app.chunking.chunk_models import (
    Chunk,
    ChunkingConfig,
    ChunkingStrategy,
    ChunkMetadata,
    ChunkResult,
)
from app.db.dependencies import get_db
from app.main import app
from app.models.memory_entry import MemoryType
from app.models.user import User
from app.schemas.memory_entry import MemoryEntryCreate
from app.services.memory_entry import create_memory_entries_chunked


# ---------------------------------------------------------------------------
# Recursive Chunker Tests
# ---------------------------------------------------------------------------

class TestRecursiveChunker:
    def test_basic_recursive_splitting(self):
        chunker = RecursiveChunker()
        text = "Paragraph 1 is here.\n\nParagraph 2 is here.\n\nParagraph 3 is here."
        config = ChunkingConfig(chunk_size=30, chunk_overlap=0, strategy=ChunkingStrategy.RECURSIVE)
        res = chunker.chunk(text, config=config)

        assert res.total_chunks >= 3
        assert res.strategy_used == "recursive"
        assert res.document_hash is not None
        assert all(len(c.content) <= 45 for c in res.chunks)
        assert all(c.chunk_hash for c in res.chunks)

    def test_sliding_window_overlap(self):
        chunker = RecursiveChunker()
        text = "WordA WordB WordC WordD WordE WordF WordG WordH WordI WordJ WordK WordL WordM"
        config = ChunkingConfig(chunk_size=30, chunk_overlap=15, strategy=ChunkingStrategy.RECURSIVE)
        res = chunker.chunk(text, config=config)

        assert len(res.chunks) >= 2
        first_chunk_end = res.chunks[0].content[-10:]
        assert any(word in res.chunks[1].content for word in first_chunk_end.split())

    def test_span_and_line_numbers(self):
        chunker = RecursiveChunker()
        text = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5"
        config = ChunkingConfig(chunk_size=15, chunk_overlap=0, strategy=ChunkingStrategy.RECURSIVE)
        res = chunker.chunk(text, config=config)

        assert len(res.chunks) > 0
        for ch in res.chunks:
            assert ch.start_char >= 0
            assert ch.end_char > ch.start_char
            assert ch.start_line >= 1
            assert ch.end_line >= ch.start_line

    def test_hierarchical_parent_child_chunking(self):
        chunker = RecursiveChunker()
        text = ("Section One has detailed architecture points. " * 10) + "\n\n" + ("Section Two has database points. " * 10)
        config = ChunkingConfig(
            hierarchical=True,
            parent_chunk_size=250,
            parent_chunk_overlap=50,
            chunk_size=100,
            chunk_overlap=20,
            strategy=ChunkingStrategy.RECURSIVE,
        )
        res = chunker.chunk(text, config=config)

        parents = [c for c in res.chunks if c.metadata.is_parent]
        children = [c for c in res.chunks if not c.metadata.is_parent]

        assert len(parents) >= 1
        assert len(children) >= 2
        assert all(c.parent_chunk_hash is not None for c in children)
        assert any(c.parent_chunk_hash == parents[0].chunk_hash for c in children)

    def test_duplicate_chunk_skipping(self):
        chunker = RecursiveChunker()
        text = "Duplicate section content.\n\nDuplicate section content.\n\nDifferent section content."
        config = ChunkingConfig(chunk_size=35, chunk_overlap=0, strategy=ChunkingStrategy.RECURSIVE)
        res = chunker.chunk(text, config=config)

        assert res.duplicate_chunks_skipped == 1
        assert len(res.chunks) == 2


# ---------------------------------------------------------------------------
# Markdown Chunker Tests
# ---------------------------------------------------------------------------

class TestMarkdownChunker:
    def test_markdown_header_hierarchy_and_breadcrumbs(self):
        markdown_text = """# Architecture Overview
This is the root system architecture.

## Database Layer
We utilize PostgreSQL with pgvector for high-performance vector storage.

### Indexing Strategy
HNSW indexing is configured for cosine distance queries.

## AI Coworkers
Granite models orchestrate engineering workflows.
"""
        chunker = MarkdownChunker()
        config = ChunkingConfig(chunk_size=500, preserve_headers=True, strategy=ChunkingStrategy.MARKDOWN)
        res = chunker.chunk(markdown_text, config=config)

        assert res.total_chunks >= 3
        indexing_chunk = next((c for c in res.chunks if "Indexing Strategy" in c.content or "HNSW" in c.content), None)
        assert indexing_chunk is not None
        assert indexing_chunk.metadata.header_hierarchy == ["# Architecture Overview", "## Database Layer", "### Indexing Strategy"]
        assert indexing_chunk.metadata.section_header == "### Indexing Strategy"

    def test_markdown_code_block_fence_safety(self):
        markdown_text = """# Code Examples
Here is some code:

```python
# This comment inside code fence is NOT a markdown header
def test_fn():
    return 42
```

## Next Section
Follow-up notes.
"""
        chunker = MarkdownChunker()
        res = chunker.chunk(markdown_text)

        headers = [c.metadata.section_header for c in res.chunks]
        assert "# This comment inside" not in headers
        assert "## Next Section" in headers

    def test_markdown_large_section_recursive_subchunking(self):
        markdown_text = f"## Big Section\n" + ("Important engineering note with details. " * 50)
        chunker = MarkdownChunker()
        config = ChunkingConfig(chunk_size=200, chunk_overlap=30, strategy=ChunkingStrategy.MARKDOWN)
        res = chunker.chunk(markdown_text, config=config)

        assert res.total_chunks > 1
        for ch in res.chunks:
            assert ch.metadata.section_header == "## Big Section"


# ---------------------------------------------------------------------------
# Code Chunker Tests
# ---------------------------------------------------------------------------

class TestCodeChunker:
    def test_python_ast_parsing(self):
        py_code = '''"""Module docstring."""

class EngineService:
    """Service class."""
    def run(self):
        return True

async def async_worker(task_id: str):
    await do_work(task_id)

def helper_function(x: int) -> int:
    return x * 2
'''
        chunker = CodeChunker()
        config = ChunkingConfig(chunk_size=1000, strategy=ChunkingStrategy.CODE, language="python")
        res = chunker.chunk(py_code, config=config)

        assert res.total_chunks >= 3
        symbols = [c.metadata.symbol_name for c in res.chunks if c.metadata.symbol_name]
        assert "EngineService" in symbols or "run" in symbols
        assert "async_worker" in symbols
        assert "helper_function" in symbols

        async_chunk = next(c for c in res.chunks if c.metadata.symbol_name == "async_worker")
        assert async_chunk.metadata.chunk_type == "async_function"
        assert async_chunk.start_line >= 8

    def test_typescript_code_chunking(self):
        ts_code = """export async function fetchUser(userId: string): Promise<User> {
    const res = await api.get(`/users/${userId}`);
    return res.data;
}

export class OrganizationClient {
    private apiKey: string;
    constructor(key: string) {
        this.apiKey = key;
    }
}
"""
        chunker = CodeChunker()
        metadata = ChunkMetadata(file_path="src/api/client.ts")
        res = chunker.chunk(ts_code, metadata=metadata)

        assert res.total_chunks >= 2
        symbols = [c.metadata.symbol_name for c in res.chunks]
        assert "fetchUser" in symbols
        assert "OrganizationClient" in symbols

    def test_sql_code_chunking(self):
        sql_code = """CREATE TABLE memory_entries (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL,
    content TEXT NOT NULL
);

CREATE FUNCTION update_timestamp() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""
        chunker = CodeChunker()
        metadata = ChunkMetadata(file_path="migrations/001.sql")
        res = chunker.chunk(sql_code, metadata=metadata)

        assert res.total_chunks >= 2
        symbols = [c.metadata.symbol_name for c in res.chunks]
        assert any("memory_entries" in str(s) for s in symbols)
        assert any("update_timestamp" in str(s) for s in symbols)

    def test_code_fallback_for_syntax_error(self):
        broken_code = "def incomplete_func(\n    for x in:\n        print('invalid python')"
        chunker = CodeChunker()
        config = ChunkingConfig(language="python")
        res = chunker.chunk(broken_code, config=config)

        assert res.total_chunks >= 1
        assert res.chunks[0].metadata.chunk_type == "code_block"


# ---------------------------------------------------------------------------
# Auto-Detection & Main Entrypoint Tests
# ---------------------------------------------------------------------------

class TestAutoDetectionAndEntrypoint:
    def test_auto_detect_markdown(self):
        md = "# Technical Specification\n\nContent goes here."
        res = chunk_text(md)
        assert res.strategy_used == "markdown"

    def test_auto_detect_python(self):
        code = "import os\n\ndef run():\n    return os.getcwd()"
        res = chunk_text(code)
        assert res.strategy_used == "code"

    def test_factory_get_chunker(self):
        assert isinstance(get_chunker(ChunkingStrategy.MARKDOWN), MarkdownChunker)
        assert isinstance(get_chunker(ChunkingStrategy.CODE), CodeChunker)
        assert isinstance(get_chunker(ChunkingStrategy.RECURSIVE), RecursiveChunker)


# ---------------------------------------------------------------------------
# Service Integration Tests
# ---------------------------------------------------------------------------

class TestMemoryEntryChunkedService:
    def test_create_memory_entries_chunked(self):
        mock_db = MagicMock()
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()

        long_content = (
            "# Incident Postmortem 2026-09\n\n"
            "## Summary\n" + ("Database connection pool was saturated. " * 10) + "\n\n"
            "## Root Cause\n" + ("Missing index on memory_entries caused slow scans. " * 10) + "\n\n"
            "## Action Items\n" + ("Add HNSW vector index and alert on pool capacity. " * 10)
        )
        entry_in = MemoryEntryCreate(
            organization_id=org_id,
            created_by_user_id=user_id,
            memory_type=MemoryType.decision,
            title="Incident Postmortem: DB Pool Saturation",
            content=long_content,
            meta={"severity": "P1"},
        )
        config = ChunkingConfig(chunk_size=300, strategy=ChunkingStrategy.MARKDOWN)

        entries = create_memory_entries_chunked(
            db=mock_db,
            entry_in=entry_in,
            chunking_config=config,
            auto_embed=False,
        )

        assert len(entries) >= 3
        assert mock_db.add.call_count == len(entries)
        assert mock_db.commit.called
        for e in entries:
            assert e.organization_id == org_id
            assert e.meta["severity"] == "P1"
            assert "chunk_hash" in e.meta
            assert "chunk_index" in e.meta


# ---------------------------------------------------------------------------
# API Preview Endpoint Tests
# ---------------------------------------------------------------------------

class TestChunkingPreviewAPI:
    @pytest.fixture(autouse=True)
    def setup_mock_auth(self):
        mock_user = User(
            id=uuid.uuid4(),
            email="test_chunk@example.com",
            full_name="Chunk Tester",
            is_active=True,
        )
        mock_db = MagicMock()
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = lambda: mock_db
        yield
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)

    def test_preview_endpoint_markdown(self, client: TestClient):
        payload = {
            "content": "# Design Doc\n\n## Section 1\nOverview text.\n\n## Section 2\nDetails text.",
            "strategy": "markdown",
            "chunk_size": 200,
            "chunk_overlap": 20,
        }
        resp = client.post("/api/v1/chunking/preview", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["strategy_used"] == "markdown"
        assert data["total_chunks"] >= 2
        assert len(data["chunks"]) >= 2
        assert "document_hash" in data
        assert all("chunk_hash" in c for c in data["chunks"])
        assert all("start_line" in c and "end_line" in c for c in data["chunks"])

    def test_preview_endpoint_code(self, client: TestClient):
        payload = {
            "content": "def calculate_score(val):\n    return val * 10\n\ndef format_output(score):\n    return f'Score: {score}'\n",
            "strategy": "code",
            "language": "python",
            "chunk_size": 500,
        }
        resp = client.post("/api/v1/chunking/preview", json=payload)
        assert resp.status_code == 200
        data = resp.json()

        assert data["strategy_used"] == "code"
        assert len(data["chunks"]) >= 2
        symbols = [c["symbol_name"] for c in data["chunks"]]
        assert "calculate_score" in symbols
        assert "format_output" in symbols

    def test_preview_endpoint_requires_auth(self, client: TestClient):
        app.dependency_overrides.pop(get_current_user, None)
        resp = client.post("/api/v1/chunking/preview", json={"content": "test text"})
        assert resp.status_code in (401, 403)
