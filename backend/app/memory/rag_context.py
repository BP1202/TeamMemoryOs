"""
RAG context builder for TeamMemoryOS.

Retrieves the top-k semantically similar memory entries and formats them
into a context block suitable for injection into an LLM prompt.  The
builder is provider-agnostic — it accepts any ``EmbeddingProvider`` and
uses the ``semantic_search`` service for retrieval.

No LLM generation is performed here.
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.memory.embedding_provider import EmbeddingProvider
from app.models.memory_entry import MemoryEntry
from app.services.memory_entry import semantic_search


@dataclass
class RAGContext:
    """The output of a retrieval pass.

    Attributes:
        entries:  The retrieved ``MemoryEntry`` objects, ranked by relevance.
        context_text: Pre-formatted string ready to be inserted into a prompt.
    """

    entries: list[MemoryEntry]
    context_text: str


def build_rag_context(
    db: Session,
    query: str,
    organization_id: UUID,
    provider: EmbeddingProvider,
    top_k: int = 5,
    scenario_id: UUID | None = None,
) -> RAGContext:
    """Embed ``query``, retrieve top-k memories, and build a context block.

    Args:
        db:              Active SQLAlchemy session.
        query:           The raw query string to embed and search against.
        organization_id: Restrict retrieval to this organisation's memory.
        provider:        Any ``EmbeddingProvider`` implementation.
        top_k:           Maximum number of memories to include.
        scenario_id:     Optional — restrict retrieval to a single scenario.

    Returns:
        A ``RAGContext`` with the ranked entries and a formatted text block.
    """
    query_embedding = provider.embed(query)

    entries = semantic_search(
        db=db,
        query_embedding=query_embedding,
        organization_id=organization_id,
        top_k=top_k,
        scenario_id=scenario_id,
    )

    context_text = _format_context(query, entries)
    return RAGContext(entries=entries, context_text=context_text)


def _format_context(query: str, entries: list[MemoryEntry]) -> str:
    """Format retrieved entries into a concise prompt context block.

    The format is intentionally structured so an LLM can parse it reliably:

        --- Organisational Memory Context ---
        Query: <query>

        [1] TYPE: decision
            TITLE: Use PostgreSQL
            We decided to use PostgreSQL ...

        [2] ...
        --- End of Context ---
    """
    if not entries:
        return (
            "--- Organisational Memory Context ---\n"
            f"Query: {query}\n\n"
            "No relevant memories found.\n"
            "--- End of Context ---"
        )

    lines: list[str] = [
        "--- Organisational Memory Context ---",
        f"Query: {query}",
        "",
    ]
    for i, entry in enumerate(entries, start=1):
        title_line = f"    TITLE: {entry.title}" if entry.title else ""
        block = [f"[{i}] TYPE: {entry.memory_type.value}"]
        if title_line:
            block.append(title_line)
        block.append(f"    {entry.content}")
        lines.append("\n".join(block))

    lines.append("--- End of Context ---")
    return "\n\n".join(lines)
