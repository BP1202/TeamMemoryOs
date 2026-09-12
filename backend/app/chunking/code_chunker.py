"""Code-aware semantic chunker supporting Python AST and multi-language structural parsing."""
from __future__ import annotations

import ast
import re
import time
from pathlib import Path
from typing import Any

from app.chunking.base_chunker import BaseChunker
from app.chunking.chunk_metadata import enrich_metadata
from app.chunking.chunk_models import Chunk, ChunkingConfig, ChunkingStrategy, ChunkMetadata, ChunkResult
from app.chunking.recursive_chunker import RecursiveChunker

# Language detection map
EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".sql": "sql",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
}

# Regex patterns for structural code boundaries
_JS_TS_PATTERN = re.compile(
    r"^(?:export\s+)?(?:async\s+)?(?:function\*?\s+([a-zA-Z0-9_$]+)|class\s+([a-zA-Z0-9_$]+)|const\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)",
    re.MULTILINE,
)

_GO_PATTERN = re.compile(
    r"^(?:func\s+(?:\([^)]+\)\s+)?([a-zA-Z0-9_]+)|type\s+([a-zA-Z0-9_]+)\s+(?:struct|interface))",
    re.MULTILINE,
)

_RUST_PATTERN = re.compile(
    r"^(?:pub\s+)?(?:async\s+)?(?:fn\s+([a-zA-Z0-9_]+)|struct\s+([a-zA-Z0-9_]+)|enum\s+([a-zA-Z0-9_]+)|impl(?:<[^>]+>)?\s+([a-zA-Z0-9_]+)|trait\s+([a-zA-Z0-9_]+))",
    re.MULTILINE,
)

_SQL_PATTERN = re.compile(
    r"^(?:CREATE\s+(?:OR\s+REPLACE\s+)?(?:TABLE|VIEW|PROCEDURE|FUNCTION|INDEX|TRIGGER)\s+([a-zA-Z0-9_.\"']+)|ALTER\s+TABLE\s+([a-zA-Z0-9_.\"']+))",
    re.MULTILINE | re.IGNORECASE,
)


class CodeChunker(BaseChunker):
    """Parses code files into semantic AST and structural symbol chunks."""

    def __init__(self) -> None:
        self.recursive_chunker = RecursiveChunker()

    @staticmethod
    def detect_language(file_path: str | None) -> str | None:
        """Detect programming language from file extension."""
        if not file_path:
            return None
        return EXTENSION_TO_LANGUAGE.get(Path(file_path).suffix.lower())

    def _chunk_python_ast(self, content: str) -> list[dict[str, Any]]:
        """Extract Python functions, classes, async functions via AST."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []

        lines = content.splitlines()
        chunks: list[dict[str, Any]] = []

        # First collect top-level / nested definitions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not hasattr(node, "lineno"):
                    continue
                start_line = node.lineno
                end_line = getattr(node, "end_lineno", None) or start_line
                chunk_lines = lines[start_line - 1 : end_line]
                chunk_content = "\n".join(chunk_lines)

                if isinstance(node, ast.ClassDef):
                    chunk_type = "class"
                elif isinstance(node, ast.AsyncFunctionDef):
                    chunk_type = "async_function"
                else:
                    chunk_type = "function"

                chunks.append({
                    "content": chunk_content,
                    "symbol_name": node.name,
                    "chunk_type": chunk_type,
                    "start_line": start_line,
                    "end_line": end_line,
                })

        # Sort chunks by starting line number
        chunks.sort(key=lambda x: x["start_line"])
        return chunks

    def _chunk_pattern_based(self, content: str, pattern: re.Pattern) -> list[dict[str, Any]]:
        """Extract structural code blocks using regex boundary detection."""
        lines = content.splitlines()
        matches: list[tuple[int, str, str]] = []  # (line_num, symbol_name, chunk_type)

        for line_idx, line in enumerate(lines, start=1):
            m = pattern.match(line)
            if m:
                # Find the matched group name
                matched_groups = [g for g in m.groups() if g is not None]
                sym_name = matched_groups[0] if matched_groups else "anonymous"
                matches.append((line_idx, sym_name, "symbol"))

        if not matches:
            return []

        chunks: list[dict[str, Any]] = []
        for i, (start_line, sym_name, chunk_type) in enumerate(matches):
            next_start = matches[i + 1][0] if i + 1 < len(matches) else len(lines) + 1
            end_line = max(start_line, next_start - 1)
            chunk_lines = lines[start_line - 1 : end_line]
            chunk_content = "\n".join(chunk_lines).strip()
            if chunk_content:
                chunks.append({
                    "content": chunk_content,
                    "symbol_name": sym_name,
                    "chunk_type": chunk_type,
                    "start_line": start_line,
                    "end_line": end_line,
                })

        return chunks

    def _chunk_fixed_window(
        self,
        content: str,
        lines_per_chunk: int = 40,
        overlap_lines: int = 10,
    ) -> list[dict[str, Any]]:
        """Fallback sliding line window chunking."""
        lines = content.splitlines()
        if not lines:
            return []

        chunks: list[dict[str, Any]] = []
        step = max(1, lines_per_chunk - overlap_lines)

        for i in range(0, len(lines), step):
            segment = lines[i : i + lines_per_chunk]
            if segment:
                start_line = i + 1
                end_line = i + len(segment)
                chunks.append({
                    "content": "\n".join(segment),
                    "symbol_name": None,
                    "chunk_type": "code_block",
                    "start_line": start_line,
                    "end_line": end_line,
                })

        return chunks

    def chunk(
        self,
        text: str,
        metadata: ChunkMetadata | dict[str, Any] | None = None,
        config: ChunkingConfig | None = None,
    ) -> ChunkResult:
        """Chunk source code using AST or structural language boundaries."""
        start_time = time.perf_counter()
        cfg = config or ChunkingConfig(strategy=ChunkingStrategy.CODE)
        
        # Determine language
        detected_lang = cfg.language
        if not detected_lang and isinstance(metadata, ChunkMetadata) and metadata.file_path:
            detected_lang = self.detect_language(metadata.file_path)
        elif not detected_lang and isinstance(metadata, dict) and metadata.get("file_path"):
            detected_lang = self.detect_language(metadata["file_path"])

        base_meta = enrich_metadata(
            metadata,
            source="code",
            language=detected_lang or (metadata.language if isinstance(metadata, ChunkMetadata) else None) or "code",
        )
        doc_hash = self.compute_hash(text)

        if not text or not text.strip():
            return ChunkResult(
                chunks=[],
                total_chunks=0,
                strategy_used=ChunkingStrategy.CODE.value,
                document_hash=doc_hash,
                duplicate_chunks_skipped=0,
                execution_time_ms=0.0,
            )

        extracted_blocks: list[dict[str, Any]] = []

        lang = (base_meta.language or "").lower()
        if lang == "python":
            extracted_blocks = self._chunk_python_ast(text)
        elif lang in ("typescript", "javascript"):
            extracted_blocks = self._chunk_pattern_based(text, _JS_TS_PATTERN)
        elif lang == "go":
            extracted_blocks = self._chunk_pattern_based(text, _GO_PATTERN)
        elif lang == "rust":
            extracted_blocks = self._chunk_pattern_based(text, _RUST_PATTERN)
        elif lang == "sql":
            extracted_blocks = self._chunk_pattern_based(text, _SQL_PATTERN)

        # If language parser didn't find symbols or failed, fallback to sliding line window
        if not extracted_blocks:
            extracted_blocks = self._chunk_fixed_window(text, lines_per_chunk=40, overlap_lines=10)

        all_chunks: list[Chunk] = []

        for blk in extracted_blocks:
            blk_content = blk["content"]
            sym_name = blk.get("symbol_name")
            chunk_type = blk.get("chunk_type") or "code_block"
            s_line = blk["start_line"]
            e_line = blk["end_line"]

            # If block size is within chunk_size, make atomic chunk
            if len(blk_content) <= cfg.chunk_size:
                ch_hash = self.compute_hash(blk_content)
                token_count = self.estimate_tokens(blk_content)
                start_char, end_char, _, _ = self.locate_span(text, blk_content)

                chunk_meta = enrich_metadata(
                    base_meta,
                    symbol_name=sym_name,
                    chunk_type=chunk_type,
                    extra={"start_line": s_line, "end_line": e_line},
                )

                all_chunks.append(
                    Chunk(
                        content=blk_content,
                        chunk_index=len(all_chunks),
                        chunk_hash=ch_hash,
                        start_char=start_char,
                        end_char=end_char,
                        start_line=s_line,
                        end_line=e_line,
                        token_count=token_count,
                        metadata=chunk_meta,
                    )
                )
            else:
                # Sub-chunk large code block (e.g. huge class or large function)
                sub_meta = enrich_metadata(
                    base_meta,
                    symbol_name=sym_name,
                    chunk_type=f"{chunk_type}_part",
                )
                sub_res = self.recursive_chunker.chunk(
                    text=blk_content,
                    metadata=sub_meta,
                    config=ChunkingConfig(
                        chunk_size=cfg.chunk_size,
                        chunk_overlap=cfg.chunk_overlap,
                        min_chunk_size=cfg.min_chunk_size,
                        strategy=ChunkingStrategy.RECURSIVE,
                        separators=["\n\n", "\n", ";\n", " ", ""],
                    ),
                )
                for sub_chunk in sub_res.chunks:
                    start_char, end_char, chunk_s_line, chunk_e_line = self.locate_span(text, sub_chunk.content)
                    sub_chunk.start_char = start_char
                    sub_chunk.end_char = end_char
                    sub_chunk.start_line = max(s_line, chunk_s_line)
                    sub_chunk.end_line = min(e_line, max(chunk_s_line, chunk_e_line))
                    sub_chunk.metadata.symbol_name = sym_name
                    sub_chunk.metadata.chunk_type = f"{chunk_type}_part"
                    all_chunks.append(sub_chunk)

        unique_chunks, dupes_skipped = self.deduplicate_chunks(all_chunks)
        exec_time = (time.perf_counter() - start_time) * 1000.0

        return ChunkResult(
            chunks=unique_chunks,
            total_chunks=len(unique_chunks),
            strategy_used=ChunkingStrategy.CODE.value,
            document_hash=doc_hash,
            duplicate_chunks_skipped=dupes_skipped,
            execution_time_ms=round(exec_time, 2),
        )
