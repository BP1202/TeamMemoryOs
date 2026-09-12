"""
Prompt builder for TeamMemoryOS RAG pipeline.

Provides prompt formatting helpers for both direct string generation and
LangChain ChatPromptTemplate workflows.

Assembles prompts in structured layers:
1. System prompt  — describes the assistant's role and constraints.
2. Memory context — the top-k retrieved memory entries from ``rag_context`` or LangChain Document objects.
3. User question  — the original question verbatim.
4. Citations      — formatted list of memory entry IDs and titles.
"""
from __future__ import annotations

from typing import List, Union
from langchain_core.documents import Document

from app.langchain.prompt_templates import (
    ENGINEERING_CHAT_PROMPT,
    INCIDENT_INVESTIGATION_PROMPT,
    PULL_REQUEST_REVIEW_PROMPT,
    REPOSITORY_ANALYSIS_PROMPT,
    format_documents_to_citations,
    format_documents_to_context,
    get_prompt_template,
)
from app.models.memory_entry import MemoryEntry

SYSTEM_PROMPT = """\
You are an AI assistant for an engineering team. Your role is to answer \
questions by drawing on the team's recorded organisational memory — decisions, \
context, insights, artifacts, and discussions captured below.

Rules:
- Base your answer on the provided memory context whenever relevant.
- If the context does not contain enough information, say so clearly.
- Be concise and precise.
- Do not invent facts not present in the context.
- Reference the memory citation numbers (e.g. [1], [2]) when you use them.\
"""


def build_prompt(
    question: str,
    context_text: str,
    entries: Union[list[MemoryEntry], list[Document]],
    max_chars: int = 8000,
) -> str:
    """Assemble the full generation prompt.

    Args:
        question:     The user's question verbatim.
        context_text: Pre-formatted context block from ``build_rag_context``.
        entries:      Retrieved ``MemoryEntry`` or ``Document`` objects used to build citations.
        max_chars:    Hard cap on total prompt length (characters).  Context is
                      trimmed from the bottom if the limit is exceeded.

    Returns:
        A single string ready to be sent to the generation model.
    """
    citations = _build_citations(entries)
    prompt = _assemble(question, context_text, citations)

    if len(prompt) > max_chars:
        prompt = _trim_prompt(question, context_text, citations, max_chars)

    return prompt


def _build_citations(entries: Union[list[MemoryEntry], list[Document]]) -> str:
    """Format a compact citation block listing each retrieved memory."""
    if not entries:
        return ""
    lines = ["Citations:"]
    for i, entry in enumerate(entries, start=1):
        if isinstance(entry, Document):
            meta = entry.metadata or {}
            m_type = meta.get("memory_type", "memory")
            title = f" — {meta['title']}" if meta.get("title") else ""
            m_id = meta.get("memory_id") or meta.get("id") or "unknown"
            lines.append(f"  [{i}] {m_type}{title} (id: {m_id})")
        else:
            title = f" — {entry.title}" if getattr(entry, "title", None) else ""
            m_type = getattr(entry, "memory_type", "memory")
            m_type_val = m_type.value if hasattr(m_type, "value") else str(m_type)
            lines.append(f"  [{i}] {m_type_val}{title} (id: {entry.id})")
    return "\n".join(lines)


def _assemble(question: str, context_text: str, citations: str) -> str:
    parts = [SYSTEM_PROMPT, "", context_text]
    if citations:
        parts += ["", citations]
    parts += ["", f"Question: {question}", "", "Answer:"]
    return "\n".join(parts)


def _trim_prompt(
    question: str,
    context_text: str,
    citations: str,
    max_chars: int,
) -> str:
    """Trim context_text from the bottom until the prompt fits within max_chars.

    We always preserve the system prompt, question, and citations in full.
    Only the memory context block is shortened — from the end, so the highest-
    ranked (most relevant) entries at the top are kept.
    """
    overhead = len(_assemble(question, "", citations))
    available = max_chars - overhead
    if available <= 0:
        # Extreme edge case: even without context the prompt is too long.
        return _assemble(question, "[Context omitted — prompt too long]", citations)

    trimmed_context = context_text[:available]
    # Trim to the last complete line to avoid cutting mid-sentence.
    last_newline = trimmed_context.rfind("\n")
    if last_newline > 0:
        trimmed_context = trimmed_context[:last_newline]
    trimmed_context += "\n[... context trimmed ...]"

    return _assemble(question, trimmed_context, citations)
