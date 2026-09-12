"""Chunk metadata enrichment and transformation utilities."""
from __future__ import annotations

from typing import Any
from app.chunking.chunk_models import Chunk, ChunkMetadata


def enrich_metadata(
    base_meta: ChunkMetadata | dict[str, Any] | None,
    *,
    source: str | None = None,
    file_path: str | None = None,
    language: str | None = None,
    section_header: str | None = None,
    header_hierarchy: list[str] | None = None,
    symbol_name: str | None = None,
    chunk_type: str | None = None,
    parent_id: str | None = None,
    parent_hash: str | None = None,
    is_parent: bool | None = None,
    extra: dict[str, Any] | None = None,
) -> ChunkMetadata:
    """Enrich or construct a ChunkMetadata object by merging existing and override fields."""
    if base_meta is None:
        meta_dict: dict[str, Any] = {}
    elif isinstance(base_meta, ChunkMetadata):
        meta_dict = base_meta.model_dump()
    elif isinstance(base_meta, dict):
        meta_dict = dict(base_meta)
    else:
        meta_dict = {}

    if source is not None:
        meta_dict["source"] = source
    if file_path is not None:
        meta_dict["file_path"] = file_path
    if language is not None:
        meta_dict["language"] = language
    if section_header is not None:
        meta_dict["section_header"] = section_header
    if header_hierarchy is not None:
        meta_dict["header_hierarchy"] = header_hierarchy
    if symbol_name is not None:
        meta_dict["symbol_name"] = symbol_name
    if chunk_type is not None:
        meta_dict["chunk_type"] = chunk_type
    if parent_id is not None:
        meta_dict["parent_id"] = parent_id
    if parent_hash is not None:
        meta_dict["parent_hash"] = parent_hash
    if is_parent is not None:
        meta_dict["is_parent"] = is_parent
    if extra:
        existing_extra = meta_dict.get("extra") or {}
        existing_extra.update(extra)
        meta_dict["extra"] = existing_extra

    return ChunkMetadata(**meta_dict)


def chunk_to_memory_meta(chunk: Chunk, extra_fields: dict[str, Any] | None = None) -> dict[str, Any]:
    """Convert a Chunk and its metadata into a dict suitable for MemoryEntry.meta."""
    meta: dict[str, Any] = {
        "chunk_hash": chunk.chunk_hash,
        "chunk_index": chunk.chunk_index,
        "start_char": chunk.start_char,
        "end_char": chunk.end_char,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "token_count": chunk.token_count,
    }

    if chunk.parent_chunk_hash:
        meta["parent_chunk_hash"] = chunk.parent_chunk_hash

    cmd = chunk.metadata
    if cmd.source:
        meta["source"] = cmd.source
    if cmd.file_path:
        meta["file_path"] = cmd.file_path
    if cmd.language:
        meta["language"] = cmd.language
    if cmd.section_header:
        meta["section_header"] = cmd.section_header
    if cmd.header_hierarchy:
        meta["header_hierarchy"] = cmd.header_hierarchy
    if cmd.symbol_name:
        meta["symbol_name"] = cmd.symbol_name
    if cmd.chunk_type:
        meta["chunk_type"] = cmd.chunk_type
    if cmd.parent_id:
        meta["parent_id"] = cmd.parent_id
    if cmd.parent_hash:
        meta["parent_hash"] = cmd.parent_hash
    if cmd.is_parent:
        meta["is_parent"] = cmd.is_parent
    if cmd.extra:
        for k, v in cmd.extra.items():
            if k not in meta:
                meta[k] = v

    if extra_fields:
        meta.update(extra_fields)

    return meta
