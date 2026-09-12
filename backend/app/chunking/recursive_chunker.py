"""Recursive text chunker with hierarchical separator splitting and sliding window overlap."""
from __future__ import annotations

import time
from typing import Any

from app.chunking.base_chunker import BaseChunker
from app.chunking.chunk_metadata import enrich_metadata
from app.chunking.chunk_models import Chunk, ChunkingConfig, ChunkingStrategy, ChunkMetadata, ChunkResult

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", "; ", ", ", " ", ""]


class RecursiveChunker(BaseChunker):
    """Recursively splits text using a list of separators in priority order."""

    def __init__(self, default_separators: list[str] | None = None) -> None:
        self.default_separators = default_separators or list(DEFAULT_SEPARATORS)

    def _split_text(
        self,
        text: str,
        separators: list[str],
        chunk_size: int,
        chunk_overlap: int,
    ) -> list[str]:
        """Recursively split text into segments within chunk_size, applying overlap."""
        if not text:
            return []

        if len(text) <= chunk_size:
            return [text.strip()] if text.strip() else []

        # Find first separator present in text
        separator = ""
        new_separators: list[str] = []
        for i, sep in enumerate(separators):
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1:]
                break

        if separator:
            splits = text.split(separator)
        else:
            # Character by character fallback
            splits = list(text)

        # Merge splits into chunks of size <= chunk_size with sliding window overlap
        docs: list[str] = []
        current_doc: list[str] = []
        total_len = 0

        for s in splits:
            if not s:
                continue

            piece = s if not separator else (s + separator)
            piece_len = len(piece)

            if piece_len > chunk_size and new_separators:
                # Flush current doc
                if current_doc:
                    merged = "".join(current_doc).strip()
                    if merged:
                        docs.append(merged)
                    current_doc = []
                    total_len = 0

                # Recurse on oversized piece
                sub_splits = self._split_text(s, new_separators, chunk_size, chunk_overlap)
                docs.extend(sub_splits)
                continue

            if total_len + piece_len > chunk_size and current_doc:
                merged = "".join(current_doc).strip()
                if merged:
                    docs.append(merged)

                # Overlap: keep the trailing pieces that fit into chunk_overlap
                overlap_doc: list[str] = []
                overlap_len = 0
                for prev in reversed(current_doc):
                    if overlap_len + len(prev) <= chunk_overlap:
                        overlap_doc.insert(0, prev)
                        overlap_len += len(prev)
                    else:
                        break

                current_doc = list(overlap_doc)
                total_len = overlap_len

            current_doc.append(piece)
            total_len += piece_len

        if current_doc:
            merged = "".join(current_doc).strip()
            if merged:
                docs.append(merged)

        return [d for d in docs if len(d) >= 1]

    def _build_chunks(
        self,
        raw_chunks: list[str],
        full_text: str,
        meta: ChunkMetadata,
        parent_hash: str | None = None,
        is_parent: bool = False,
    ) -> list[Chunk]:
        """Convert raw text pieces into fully-tracked Chunk models."""
        chunks: list[Chunk] = []
        last_search_idx = 0

        for idx, content in enumerate(raw_chunks):
            ch_hash = self.compute_hash(content)
            token_count = self.estimate_tokens(content)

            start_char, end_char, start_line, end_line = self.locate_span(
                full_text, content, start_search=last_search_idx
            )
            # Advance search index slightly after match to keep monotonic search
            if start_char >= last_search_idx:
                last_search_idx = max(start_char, last_search_idx)

            chunk_meta = enrich_metadata(
                meta,
                parent_hash=parent_hash,
                is_parent=is_parent,
                chunk_type="parent_block" if is_parent else (meta.chunk_type or "paragraph"),
            )

            chunks.append(
                Chunk(
                    content=content,
                    chunk_index=idx,
                    chunk_hash=ch_hash,
                    start_char=start_char,
                    end_char=end_char,
                    start_line=start_line,
                    end_line=end_line,
                    token_count=token_count,
                    metadata=chunk_meta,
                    parent_chunk_hash=parent_hash,
                )
            )

        return chunks

    def chunk(
        self,
        text: str,
        metadata: ChunkMetadata | dict[str, Any] | None = None,
        config: ChunkingConfig | None = None,
    ) -> ChunkResult:
        """Split input text recursively."""
        start_time = time.perf_counter()
        cfg = config or ChunkingConfig(strategy=ChunkingStrategy.RECURSIVE)
        meta = enrich_metadata(metadata, source=metadata.source if isinstance(metadata, ChunkMetadata) else "recursive")
        separators = cfg.separators or self.default_separators
        doc_hash = self.compute_hash(text)

        if not text or not text.strip():
            return ChunkResult(
                chunks=[],
                total_chunks=0,
                strategy_used=ChunkingStrategy.RECURSIVE.value,
                document_hash=doc_hash,
                duplicate_chunks_skipped=0,
                execution_time_ms=0.0,
            )

        if cfg.hierarchical:
            # 1. Generate large parent chunks
            parent_raw = self._split_text(
                text=text,
                separators=separators,
                chunk_size=cfg.parent_chunk_size,
                chunk_overlap=cfg.parent_chunk_overlap,
            )
            parent_chunks = self._build_chunks(parent_raw, text, meta, is_parent=True)

            # 2. For each parent chunk, generate child chunks
            all_chunks: list[Chunk] = []
            for p_chunk in parent_chunks:
                child_raw = self._split_text(
                    text=p_chunk.content,
                    separators=separators,
                    chunk_size=cfg.chunk_size,
                    chunk_overlap=cfg.chunk_overlap,
                )
                child_chunks = self._build_chunks(
                    child_raw,
                    text,
                    meta,
                    parent_hash=p_chunk.chunk_hash,
                    is_parent=False,
                )
                # Include parent chunk + its child chunks
                all_chunks.append(p_chunk)
                all_chunks.extend(child_chunks)

            unique_chunks, dupes_skipped = self.deduplicate_chunks(all_chunks)
        else:
            raw_splits = self._split_text(
                text=text,
                separators=separators,
                chunk_size=cfg.chunk_size,
                chunk_overlap=cfg.chunk_overlap,
            )
            created_chunks = self._build_chunks(raw_splits, text, meta, is_parent=False)
            unique_chunks, dupes_skipped = self.deduplicate_chunks(created_chunks)

        exec_time = (time.perf_counter() - start_time) * 1000.0

        return ChunkResult(
            chunks=unique_chunks,
            total_chunks=len(unique_chunks),
            strategy_used=ChunkingStrategy.RECURSIVE.value,
            document_hash=doc_hash,
            duplicate_chunks_skipped=dupes_skipped,
            execution_time_ms=round(exec_time, 2),
        )
