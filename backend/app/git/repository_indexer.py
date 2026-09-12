"""Incremental Git Repository Indexing Engine (AI-004)."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.cache.embedding_cache import EmbeddingCache
from app.chunking import chunk_text, chunk_to_memory_meta
from app.chunking.chunk_models import ChunkingConfig, ChunkingStrategy, ChunkMetadata
from app.git.diff_detector import detect_diff
from app.git.git_models import FileChangeType, IncrementalIndexResult
from app.git.git_repository import GitRepositoryWrapper
from app.models.code_index import CodeChunk, CodeFile
from app.models.entity import MemoryEntity
from app.models.memory_entry import MemoryEntry, MemoryType
from app.models.repository import CommitMemory, Repository
from app.providers.embedding_provider import get_embedding_provider
from app.services.entity import get_or_create_entity
from app.services.entity_extraction import extract_entities
from app.services.repository import ingest_commit


DEFAULT_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".rs", ".rb", ".cs", ".cpp", ".c", ".h", ".sql", ".sh", ".md"}


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
        ".md": "markdown",
    }
    return ext_map.get(Path(file_path).suffix.lower())


class GitRepositoryIndexer:
    """Orchestrates incremental Git repository indexing with hash-based chunk reuse."""

    def __init__(
        self,
        db: Session,
        repository_id: UUID,
        organization_id: UUID,
        file_extensions: list[str] | None = None,
        max_files: int = 500,
    ):
        self.db = db
        self.repository_id = repository_id
        self.organization_id = organization_id
        self.max_files = max_files
        self.extensions = {
            ext if ext.startswith(".") else f".{ext}"
            for ext in (file_extensions or list(DEFAULT_EXTENSIONS))
        }
        self.emb_provider = get_embedding_provider()
        self.embedding_cache = EmbeddingCache()

    def _cleanup_file_chunks(self, file_path: str) -> None:
        """Remove existing CodeFile, CodeChunks, and linked MemoryEntries for a file path."""
        code_file = self.db.scalar(
            select(CodeFile).where(
                CodeFile.repository_id == self.repository_id,
                CodeFile.file_path == file_path,
            )
        )
        if not code_file:
            return

        # Fetch chunks
        chunks = self.db.scalars(
            select(CodeChunk).where(CodeChunk.code_file_id == code_file.id)
        ).all()
        
        mem_entry_ids = [c.memory_entry_id for c in chunks if c.memory_entry_id]

        # Delete code chunks
        self.db.execute(delete(CodeChunk).where(CodeChunk.code_file_id == code_file.id))

        # Delete linked memory entries
        if mem_entry_ids:
            self.db.execute(
                delete(MemoryEntry).where(MemoryEntry.id.in_(mem_entry_ids))
            )

        # Delete code file record
        self.db.delete(code_file)
        self.db.flush()

    def _find_existing_embedding_by_hash(self, chunk_hash: str) -> list[float] | None:
        """Check if an embedding for this chunk hash is already cached or stored in DB."""
        # 1. Check in-memory EmbeddingCache
        cached = self.embedding_cache.get(chunk_hash)
        if cached:
            return cached

        # 2. Check MemoryEntry in database with matching chunk_hash meta
        try:
            entry = self.db.scalar(
                select(MemoryEntry).where(
                    MemoryEntry.organization_id == self.organization_id,
                    MemoryEntry.meta.op("->>")("chunk_hash") == chunk_hash,
                    MemoryEntry.embedding.isnot(None),
                ).limit(1)
            )
            if entry and entry.embedding is not None:
                emb = list(entry.embedding)
                self.embedding_cache.set(chunk_hash, emb)
                return emb
        except Exception:
            pass

        return None

    def index(self, force_full: bool = False) -> IncrementalIndexResult:
        """Run incremental or full indexing on the repository."""
        start_time = time.time()

        repo = self.db.scalar(
            select(Repository).where(Repository.id == self.repository_id)
        )
        if repo is None or repo.organization_id != self.organization_id:
            return IncrementalIndexResult(
                repository_id=self.repository_id,
                duration_seconds=0.0,
            )

        git_wrapper = GitRepositoryWrapper(repo.remote_url)
        if not git_wrapper.is_valid:
            return IncrementalIndexResult(
                repository_id=self.repository_id,
                duration_seconds=0.0,
            )

        base_path = git_wrapper.path
        current_head_sha = git_wrapper.repo.head.commit.hexsha if git_wrapper.repo.heads else None
        last_sha = repo.last_synced_sha

        is_incremental = bool(last_sha and not force_full and current_head_sha)
        files_to_process: set[str] = set()
        files_to_delete: set[str] = set()

        if is_incremental and last_sha != current_head_sha:
            # Incremental mode: compute diff between last_sha and current_head_sha
            diff_summary = detect_diff(git_wrapper.repo, base_ref=last_sha, target_ref=current_head_sha)
            for entry in diff_summary.changed_files:
                ext = Path(entry.file_path).suffix.lower()
                if ext not in self.extensions:
                    continue

                if entry.change_type in (FileChangeType.DELETED, FileChangeType.RENAMED):
                    path_to_del = entry.old_path or entry.file_path
                    files_to_delete.add(path_to_del)

                if entry.change_type in (FileChangeType.ADDED, FileChangeType.MODIFIED, FileChangeType.RENAMED):
                    files_to_process.add(entry.file_path)
        else:
            # Full indexing: scan all files under repo
            for fp in base_path.rglob("*"):
                if not fp.is_file():
                    continue
                if ".git" in fp.parts:
                    continue
                if fp.suffix.lower() in self.extensions:
                    rel_path = str(fp.relative_to(base_path)).replace("\\", "/")
                    files_to_process.add(rel_path)

        # 1. Process deletions
        files_deleted_count = 0
        for del_path in files_to_delete:
            self._cleanup_file_chunks(del_path)
            files_deleted_count += 1

        # 2. Process added and modified files
        files_indexed_count = 0
        files_skipped_count = 0
        total_chunks = 0
        new_chunks = 0
        reused_chunks = 0

        for rel_path in sorted(files_to_process):
            if files_indexed_count >= self.max_files:
                break

            file_disk_path = base_path / rel_path
            if not file_disk_path.is_file():
                continue

            try:
                content = file_disk_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                files_skipped_count += 1
                continue

            # Cleanup previous chunks for this file if reindexing
            self._cleanup_file_chunks(rel_path)

            language = _detect_language(rel_path)
            size_bytes = len(content.encode("utf-8"))

            # Create CodeFile
            code_file = CodeFile(
                organization_id=self.organization_id,
                repository_id=self.repository_id,
                file_path=rel_path,
                language=language,
                size_bytes=size_bytes,
            )
            self.db.add(code_file)
            self.db.flush()

            # Intelligent Chunking
            chunk_res = chunk_text(
                text=content,
                strategy=ChunkingStrategy.AUTO,
                metadata=ChunkMetadata(
                    file_path=rel_path,
                    language=language,
                    source="code",
                ),
                config=ChunkingConfig(
                    chunk_size=1500,
                    chunk_overlap=200,
                    language=language,
                ),
            )

            for ch in chunk_res.chunks:
                total_chunks += 1
                chunk_content = ch.content[:3000]
                start_line = ch.start_line
                end_line = ch.end_line
                chunk_type = ch.metadata.chunk_type or "block"
                symbol_name = ch.metadata.symbol_name
                chunk_hash = ch.chunk_hash

                # Check if embedding can be reused via SHA-256 chunk hash
                existing_embedding = self._find_existing_embedding_by_hash(chunk_hash)
                if existing_embedding is not None:
                    embedding = existing_embedding
                    reused_chunks += 1
                else:
                    embedding = self.emb_provider.embed(chunk_content[:2000])
                    self.embedding_cache.set(chunk_hash, embedding)
                    new_chunks += 1

                chunk_meta = chunk_to_memory_meta(
                    ch,
                    extra_fields={
                        "source": "code",
                        "file_path": rel_path,
                        "language": language,
                        "chunk_type": chunk_type,
                        "symbol_name": symbol_name,
                        "chunk_hash": chunk_hash,
                    },
                )

                # Create MemoryEntry for chunk
                mem_entry = MemoryEntry(
                    organization_id=self.organization_id,
                    memory_type=MemoryType.artifact,
                    title=f"{rel_path}:{start_line} [{symbol_name or chunk_type}]",
                    content=chunk_content,
                    meta=chunk_meta,
                    embedding=embedding,
                )
                self.db.add(mem_entry)
                self.db.flush()

                # Create CodeChunk
                chunk = CodeChunk(
                    organization_id=self.organization_id,
                    code_file_id=code_file.id,
                    memory_entry_id=mem_entry.id,
                    chunk_type=chunk_type,
                    symbol_name=symbol_name,
                    content=chunk_content,
                    start_line=start_line,
                    end_line=end_line,
                    embedding=embedding,
                )
                self.db.add(chunk)

                # Entity extraction from code
                raw_entities = extract_entities(chunk_content)
                for raw_entity in raw_entities:
                    entity = get_or_create_entity(
                        self.db,
                        organization_id=self.organization_id,
                        entity_type=raw_entity.entity_type,
                        name=raw_entity.name,
                    )
                    try:
                        self.db.add(MemoryEntity(memory_entry_id=mem_entry.id, entity_id=entity.id))
                        self.db.flush()
                    except IntegrityError:
                        self.db.rollback()

            self.db.commit()
            files_indexed_count += 1

        # 3. Synchronize commits into CommitMemory
        if current_head_sha:
            new_commits = git_wrapper.get_commits(since_sha=last_sha, max_count=50)
            for c_info in new_commits:
                ingest_commit(
                    self.db,
                    organization_id=self.organization_id,
                    repository_id=self.repository_id,
                    commit_sha=c_info.commit_sha,
                    author_name=c_info.author_name,
                    author_email=c_info.author_email,
                    commit_message=c_info.message,
                    committed_at=c_info.committed_at,
                    files_changed=c_info.files_changed,
                    insertions=c_info.insertions,
                    deletions=c_info.deletions,
                    changed_files=c_info.changed_files,
                )

        # 4. Update repository record
        if current_head_sha:
            repo.last_synced_sha = current_head_sha
            repo.last_synced_at = datetime.now(timezone.utc)
            self.db.commit()

        duration = time.time() - start_time

        return IncrementalIndexResult(
            repository_id=self.repository_id,
            is_incremental=is_incremental,
            base_sha=last_sha,
            target_sha=current_head_sha,
            total_files_scanned=len(files_to_process) + len(files_to_delete),
            files_indexed=files_indexed_count,
            files_skipped_unchanged=files_skipped_count,
            files_deleted=files_deleted_count,
            total_chunks=total_chunks,
            new_chunks=new_chunks,
            reused_chunks=reused_chunks,
            duration_seconds=round(duration, 3),
        )
