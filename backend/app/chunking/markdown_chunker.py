"""Markdown-aware chunker with header hierarchy tracking, code fence preservation, and breadcrumb context injection."""
from __future__ import annotations

import re
import time
from typing import Any

from app.chunking.base_chunker import BaseChunker
from app.chunking.chunk_metadata import enrich_metadata
from app.chunking.chunk_models import Chunk, ChunkingConfig, ChunkingStrategy, ChunkMetadata, ChunkResult
from app.chunking.recursive_chunker import RecursiveChunker

# Matches markdown headers like # Title, ## Section, ### Subsection
_HEADER_REGEX = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


class MarkdownChunker(BaseChunker):
    """Parses Markdown documents into semantic sections preserving header hierarchies."""

    def __init__(self) -> None:
        self.recursive_chunker = RecursiveChunker()

    def _parse_sections(self, markdown_text: str) -> list[dict[str, Any]]:
        """Parse markdown text into structured sections with header levels and breadcrumbs."""
        lines = markdown_text.splitlines()
        sections: list[dict[str, Any]] = []

        header_stack: list[tuple[int, str]] = []  # (level, header_text)
        current_lines: list[str] = []
        current_start_line = 1
        current_header = ""
        in_code_block = False

        def get_breadcrumbs() -> list[str]:
            return [f"{'#' * lvl} {txt}" for lvl, txt in header_stack]

        def flush_section(end_line: int):
            content = "\n".join(current_lines).strip()
            if content:
                sections.append({
                    "content": content,
                    "section_header": current_header,
                    "header_hierarchy": get_breadcrumbs(),
                    "start_line": current_start_line,
                    "end_line": max(current_start_line, end_line),
                })

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Handle code block fences (``` or ~~~) so headers inside code blocks are ignored
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_code_block = not in_code_block
                current_lines.append(line)
                continue

            if not in_code_block and stripped.startswith("#"):
                match = _HEADER_REGEX.match(line)
                if match:
                    hashes, title = match.groups()
                    level = len(hashes)

                    # Flush previous section before starting new header
                    flush_section(line_num - 1)

                    # Update header stack
                    while header_stack and header_stack[-1][0] >= level:
                        header_stack.pop()
                    header_stack.append((level, title.strip()))

                    current_header = f"{hashes} {title.strip()}"
                    current_lines = [line]
                    current_start_line = line_num
                    continue

            current_lines.append(line)

        # Flush final section
        flush_section(len(lines))

        # If no markdown headers were found at all, treat whole text as single root section
        if not sections and markdown_text.strip():
            sections.append({
                "content": markdown_text.strip(),
                "section_header": "",
                "header_hierarchy": [],
                "start_line": 1,
                "end_line": len(lines),
            })

        return sections

    def chunk(
        self,
        text: str,
        metadata: ChunkMetadata | dict[str, Any] | None = None,
        config: ChunkingConfig | None = None,
    ) -> ChunkResult:
        """Split Markdown document into header-aware semantic chunks."""
        start_time = time.perf_counter()
        cfg = config or ChunkingConfig(strategy=ChunkingStrategy.MARKDOWN)
        base_meta = enrich_metadata(metadata, source="markdown", language="markdown")
        doc_hash = self.compute_hash(text)

        if not text or not text.strip():
            return ChunkResult(
                chunks=[],
                total_chunks=0,
                strategy_used=ChunkingStrategy.MARKDOWN.value,
                document_hash=doc_hash,
                duplicate_chunks_skipped=0,
                execution_time_ms=0.0,
            )

        sections = self._parse_sections(text)
        all_chunks: list[Chunk] = []

        for sec in sections:
            sec_content = sec["content"]
            sec_header = sec["section_header"]
            hierarchy = sec["header_hierarchy"]
            start_line = sec["start_line"]
            end_line = sec["end_line"]

            # If section fits within chunk_size, keep as a single atomic chunk
            if len(sec_content) <= cfg.chunk_size:
                final_content = sec_content
                # If preserve_headers is enabled and hierarchy exists but header isn't in content
                if cfg.preserve_headers and hierarchy and not sec_content.startswith(hierarchy[-1]):
                    breadcrumb_str = " > ".join(hierarchy)
                    final_content = f"<!-- Section: {breadcrumb_str} -->\n{sec_content}"

                ch_hash = self.compute_hash(final_content)
                token_count = self.estimate_tokens(final_content)
                start_char, end_char, _, _ = self.locate_span(text, sec_content)

                chunk_meta = enrich_metadata(
                    base_meta,
                    section_header=sec_header,
                    header_hierarchy=hierarchy,
                    chunk_type="markdown_section",
                    extra={"hierarchy_path": " > ".join(hierarchy) if hierarchy else ""},
                )

                all_chunks.append(
                    Chunk(
                        content=final_content,
                        chunk_index=len(all_chunks),
                        chunk_hash=ch_hash,
                        start_char=start_char,
                        end_char=end_char,
                        start_line=start_line,
                        end_line=end_line,
                        token_count=token_count,
                        metadata=chunk_meta,
                    )
                )
            else:
                # Sub-chunk oversized section using RecursiveChunker
                sub_meta = enrich_metadata(
                    base_meta,
                    section_header=sec_header,
                    header_hierarchy=hierarchy,
                    chunk_type="markdown_section_part",
                )
                sub_res = self.recursive_chunker.chunk(
                    text=sec_content,
                    metadata=sub_meta,
                    config=ChunkingConfig(
                        chunk_size=cfg.chunk_size,
                        chunk_overlap=cfg.chunk_overlap,
                        min_chunk_size=cfg.min_chunk_size,
                        strategy=ChunkingStrategy.RECURSIVE,
                        separators=cfg.separators or ["\n\n", "\n", ". ", " ", ""],
                    ),
                )
                for sub_chunk in sub_res.chunks:
                    # Contextualize with header breadcrumbs if enabled
                    if cfg.preserve_headers and hierarchy and not sub_chunk.content.startswith("#"):
                        breadcrumb_str = " > ".join(hierarchy)
                        sub_chunk.content = f"<!-- Section: {breadcrumb_str} -->\n{sub_chunk.content}"
                        sub_chunk.chunk_hash = self.compute_hash(sub_chunk.content)
                        sub_chunk.token_count = self.estimate_tokens(sub_chunk.content)

                    # Adjust character and line offsets relative to the parent document
                    sub_start_char, sub_end_char, s_line, e_line = self.locate_span(text, sub_chunk.content)
                    sub_chunk.start_char = sub_start_char
                    sub_chunk.end_char = sub_end_char
                    sub_chunk.start_line = max(start_line, s_line)
                    sub_chunk.end_line = min(end_line, max(s_line, e_line))
                    sub_chunk.metadata.section_header = sec_header
                    sub_chunk.metadata.header_hierarchy = hierarchy
                    all_chunks.append(sub_chunk)

        unique_chunks, dupes_skipped = self.deduplicate_chunks(all_chunks)
        exec_time = (time.perf_counter() - start_time) * 1000.0

        return ChunkResult(
            chunks=unique_chunks,
            total_chunks=len(unique_chunks),
            strategy_used=ChunkingStrategy.MARKDOWN.value,
            document_hash=doc_hash,
            duplicate_chunks_skipped=dupes_skipped,
            execution_time_ms=round(exec_time, 2),
        )
