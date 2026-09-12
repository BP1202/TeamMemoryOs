"""Chunking API endpoints for TeamMemoryOS."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.chunking import chunk_text
from app.chunking.chunk_models import ChunkingConfig, ChunkMetadata
from app.models.user import User
from app.schemas.chunking import ChunkPreviewItem, ChunkPreviewRequest, ChunkPreviewResponse

router = APIRouter()


@router.post("/preview", response_model=ChunkPreviewResponse)
def preview_chunking(
    request: ChunkPreviewRequest,
    _: User = Depends(get_current_user),
) -> ChunkPreviewResponse:
    """Preview document or code chunking with token estimation, hashing, and metadata.
    
    Deterministically splits the content using the specified or auto-detected strategy,
    computes SHA-256 hashes, marks duplicates, and returns structured chunk previews
    without persisting any records to the database.
    """
    metadata = ChunkMetadata(
        file_path=request.file_path,
        language=request.language,
    )
    config = ChunkingConfig(
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap,
        min_chunk_size=request.min_chunk_size,
        strategy=request.strategy,
        language=request.language,
        preserve_headers=request.preserve_headers,
        hierarchical=request.hierarchical,
    )

    result = chunk_text(
        text=request.content,
        strategy=request.strategy,
        metadata=metadata,
        config=config,
    )

    items = [
        ChunkPreviewItem(
            chunk_index=ch.chunk_index,
            chunk_hash=ch.chunk_hash,
            content=ch.content,
            token_count=ch.token_count,
            start_char=ch.start_char,
            end_char=ch.end_char,
            start_line=ch.start_line,
            end_line=ch.end_line,
            symbol_name=ch.metadata.symbol_name,
            section_header=ch.metadata.section_header,
            header_hierarchy=ch.metadata.header_hierarchy,
            parent_chunk_hash=ch.parent_chunk_hash,
            is_parent=ch.metadata.is_parent,
            is_duplicate=ch.is_duplicate,
        )
        for ch in result.chunks
    ]

    return ChunkPreviewResponse(
        strategy_used=result.strategy_used,
        document_hash=result.document_hash,
        total_chunks=result.total_chunks,
        duplicate_chunks_skipped=result.duplicate_chunks_skipped,
        execution_time_ms=result.execution_time_ms,
        chunks=items,
    )
