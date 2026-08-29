"""AI Codebase Search service (Milestone 6.4).

Pipeline:
1. Walk repository directory and index files.
2. Chunk files using AST parsing (Python) or fixed-size windows.
3. Store CodeFile and CodeChunk records.
4. Embed chunks via EmbeddingProvider.
5. Search chunks via cosine similarity + entity extraction.
"""
from __future__ import annotations

import ast
import os
import re
from pathlib import Path
from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.memory.embedding_provider import StubEmbeddingProvider
from app.models.code_index import CodeChunk, CodeFile
from app.models.entity import MemoryEntity
from app.models.memory_entry import EMBEDDING_DIM, MemoryEntry, MemoryType
from app.models.repository import Repository
from app.schemas.code_index import (
    CodeIndexRequest,
    CodeIndexResponse,
    CodeSearchRequest,
    CodeSearchResponse,
    CodeSearchResult,
)
from app.services.entity import get_or_create_entity
from app.services.entity_extraction import extract_entities

_CHUNK_SIZE = 40  # lines per fixed-size chunk


def _detect_language(file_path: str) -> str | None:
    """Map file extension to language name."""
    ext_map = {
        ".py": "python",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".go": "go",
        ".java": "java",
        ".rs": "rust",
        ".rb": "ruby",
        ".cs": "csharp",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".sql": "sql",
        ".sh": "bash",
    }
    return ext_map.get(Path(file_path).suffix.lower())


def _chunk_python(content: str) -> list[tuple[str, int, int, str, str | None]]:
    """Return list of (content, start_line, end_line, chunk_type, symbol_name)
    from Python source using AST parsing.

    Falls back to fixed-size chunks on parse errors.
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return _chunk_fixed(content)

    lines = content.splitlines()
    chunks: list[tuple[str, int, int, str, str | None]] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not hasattr(node, "lineno"):
                continue
            start = node.lineno
            end = node.end_lineno or start
            chunk_content = "\n".join(lines[start - 1:end])
            chunk_type = "class" if isinstance(node, ast.ClassDef) else "function"
            chunks.append((chunk_content, start, end, chunk_type, node.name))

    if not chunks:
        return _chunk_fixed(content)
    return chunks


def _chunk_fixed(
    content: str,
    chunk_size: int = _CHUNK_SIZE,
) -> list[tuple[str, int, int, str, str | None]]:
    """Split content into fixed-size line chunks."""
    lines = content.splitlines()
    chunks: list[tuple[str, int, int, str, str | None]] = []
    for i in range(0, len(lines), chunk_size):
        segment = lines[i: i + chunk_size]
        if segment:
            start = i + 1
            end = i + len(segment)
            chunks.append(("\n".join(segment), start, end, "block", None))
    return chunks


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

def index_repository(
    db: Session,
    repository_id: UUID,
    organization_id: UUID,
    request: CodeIndexRequest,
) -> CodeIndexResponse:
    """Index source files in a repository directory.

    When the local path is unavailable (remote URL), returns zero files indexed.
    """
    repo = db.scalar(
        select(Repository).where(Repository.id == repository_id)
    )
    if repo is None or repo.organization_id != organization_id:
        return CodeIndexResponse(
            repository_id=repository_id,
            files_indexed=0,
            chunks_created=0,
            files_skipped=0,
        )

    # Only index when remote_url is a local path
    base_path = Path(repo.remote_url)
    if not base_path.exists() or not base_path.is_dir():
        return CodeIndexResponse(
            repository_id=repository_id,
            files_indexed=0,
            chunks_created=0,
            files_skipped=0,
        )

    extensions = {ext if ext.startswith(".") else f".{ext}" for ext in request.file_extensions}
    emb_provider = StubEmbeddingProvider()

    files_indexed = 0
    chunks_created = 0
    files_skipped = 0

    for file_path in base_path.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in extensions:
            continue
        if files_indexed >= request.max_files:
            break

        rel_path = str(file_path.relative_to(base_path))
        language = _detect_language(rel_path)

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            files_skipped += 1
            continue

        # Upsert CodeFile
        code_file = db.scalar(
            select(CodeFile).where(
                CodeFile.repository_id == repository_id,
                CodeFile.file_path == rel_path,
            )
        )
        if code_file is None:
            code_file = CodeFile(
                organization_id=organization_id,
                repository_id=repository_id,
                file_path=rel_path,
                language=language,
                size_bytes=len(content.encode("utf-8")),
            )
            db.add(code_file)
            try:
                db.flush()
            except IntegrityError:
                db.rollback()
                files_skipped += 1
                continue

        # Chunk
        if language == "python":
            raw_chunks = _chunk_python(content)
        else:
            raw_chunks = _chunk_fixed(content)

        for chunk_content, start_line, end_line, chunk_type, symbol_name in raw_chunks:
            # Create MemoryEntry for the chunk
            mem_entry = MemoryEntry(
                organization_id=organization_id,
                memory_type=MemoryType.artifact,
                title=f"{rel_path}:{start_line} [{symbol_name or chunk_type}]",
                content=chunk_content[:3000],
                meta={
                    "source": "code",
                    "file_path": rel_path,
                    "language": language,
                    "chunk_type": chunk_type,
                    "symbol_name": symbol_name,
                    "start_line": start_line,
                    "end_line": end_line,
                },
            )
            db.add(mem_entry)
            db.flush()

            # Store embedding
            embedding = emb_provider.embed(chunk_content[:2000])
            mem_entry.embedding = embedding
            db.flush()

            chunk = CodeChunk(
                organization_id=organization_id,
                code_file_id=code_file.id,
                memory_entry_id=mem_entry.id,
                chunk_type=chunk_type,
                symbol_name=symbol_name,
                content=chunk_content[:3000],
                start_line=start_line,
                end_line=end_line,
                embedding=embedding,
            )
            db.add(chunk)
            chunks_created += 1

            # Entity extraction from code
            raw_entities = extract_entities(chunk_content)
            for raw_entity in raw_entities:
                entity = get_or_create_entity(
                    db,
                    organization_id=organization_id,
                    entity_type=raw_entity.entity_type,
                    name=raw_entity.name,
                )
                try:
                    db.add(MemoryEntity(memory_entry_id=mem_entry.id, entity_id=entity.id))
                    db.flush()
                except IntegrityError:
                    db.rollback()

        db.commit()
        files_indexed += 1

    return CodeIndexResponse(
        repository_id=repository_id,
        files_indexed=files_indexed,
        chunks_created=chunks_created,
        files_skipped=files_skipped,
    )


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search_code(
    db: Session,
    request: CodeSearchRequest,
) -> CodeSearchResponse:
    """Search code chunks using embedding similarity."""
    emb_provider = StubEmbeddingProvider()
    query_embedding = emb_provider.embed(request.query)

    stmt = (
        select(CodeChunk)
        .where(
            CodeChunk.organization_id == request.organization_id,
            CodeChunk.embedding.isnot(None),
        )
        .order_by(CodeChunk.embedding.op("<=>")(query_embedding))
        .limit(request.top_k)
    )
    if request.repository_id is not None:
        stmt = stmt.where(CodeChunk.code_file_id.in_(
            select(CodeFile.id).where(CodeFile.repository_id == request.repository_id)
        ))

    chunks = db.scalars(stmt).all()

    results: list[CodeSearchResult] = []
    for chunk in chunks:
        code_file = db.scalar(select(CodeFile).where(CodeFile.id == chunk.code_file_id))
        file_path = code_file.file_path if code_file else "unknown"
        language = code_file.language if code_file else None

        results.append(
            CodeSearchResult(
                chunk_id=chunk.id,
                file_path=file_path,
                language=language,
                symbol_name=chunk.symbol_name,
                chunk_type=chunk.chunk_type,
                content=chunk.content,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                score=0.5,  # stub score; real score requires distance computation
                explanation=f"Found in {file_path}:{chunk.start_line}-{chunk.end_line}",
            )
        )

    return CodeSearchResponse(
        query=request.query,
        organization_id=request.organization_id,
        results=results,
        result_count=len(results),
    )


def get_chunks_for_file(
    db: Session,
    code_file_id: UUID,
    organization_id: UUID,
) -> Sequence[CodeChunk]:
    return db.scalars(
        select(CodeChunk)
        .where(
            CodeChunk.code_file_id == code_file_id,
            CodeChunk.organization_id == organization_id,
        )
        .order_by(CodeChunk.start_line)
    ).all()
