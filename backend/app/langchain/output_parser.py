"""
LangChain Output Parser for TeamMemoryOS.

Parses generation output into structured, production-ready response objects
containing answers, extracted citations, retrieved memory summaries, participating
agents, and retrieval mode metadata.
"""
from __future__ import annotations

import re
from typing import Any, List, Optional
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import BaseOutputParser
from pydantic import BaseModel, Field


class TeamMemoryRAGOutput(BaseModel):
    """Structured result model parsed from the RAG pipeline."""

    answer: str
    citations: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    retrieved_memories: List[dict[str, Any]] = Field(default_factory=list)
    participating_agents: List[str] = Field(default_factory=lambda: ["LangChain-RAG-Agent"])
    retrieval_mode: str = "semantic"
    provider_used: str = "ollama"


class TeamMemoryOutputParser(BaseOutputParser[TeamMemoryRAGOutput]):
    """Output parser that converts model text into structured TeamMemoryRAGOutput."""

    retrieval_mode: str = "semantic"
    provider_used: str = "ollama"

    def parse(self, text: str) -> TeamMemoryRAGOutput:
        """Parse raw LLM output text into TeamMemoryRAGOutput."""
        cleaned_text = text.strip()
        citations = self._extract_citations_from_text(cleaned_text)
        confidence = self._estimate_confidence(cleaned_text)

        return TeamMemoryRAGOutput(
            answer=cleaned_text,
            citations=citations,
            confidence=confidence,
            retrieved_memories=[],
            participating_agents=["LangChain-RAG-Agent"],
            retrieval_mode=self.retrieval_mode,
            provider_used=self.provider_used,
        )

    def parse_with_documents(
        self,
        text_or_message: str | BaseMessage,
        documents: List[Document],
        retrieval_mode: str = "semantic",
        provider_used: str = "ollama",
        explanation: Any = None,
    ) -> TeamMemoryRAGOutput:
        """Parse generation response and enrich with retrieved document metadata."""
        if isinstance(text_or_message, BaseMessage):
            raw_text = str(text_or_message.content)
        else:
            raw_text = str(text_or_message)

        cleaned_text = raw_text.strip()

        # Build citations list from documents
        doc_citations: list[str] = []
        retrieved_memories: list[dict[str, Any]] = []

        for i, doc in enumerate(documents, start=1):
            meta = doc.metadata or {}
            m_type = meta.get("memory_type") or meta.get("entity") or "memory"
            title = f" — {meta['title']}" if meta.get("title") else ""
            m_id = meta.get("memory_id") or meta.get("id") or "unknown"
            citation_str = f"[{i}] {m_type}{title} (id: {m_id})"
            doc_citations.append(citation_str)

            retrieved_memories.append({
                "rank": i,
                "id": m_id,
                "type": m_type,
                "title": meta.get("title"),
                "chunk_hash": meta.get("chunk_hash"),
                "source": meta.get("source"),
                "file_path": meta.get("file_path"),
                "line_numbers": meta.get("line_numbers"),
                "score": meta.get("score") or meta.get("similarity_score"),
            })

        confidence = self._estimate_confidence(cleaned_text, has_docs=bool(documents))

        return TeamMemoryRAGOutput(
            answer=cleaned_text,
            citations=doc_citations,
            confidence=confidence,
            retrieved_memories=retrieved_memories,
            participating_agents=["LangChain-RAG-Agent"],
            retrieval_mode=retrieval_mode,
            provider_used=provider_used,
        )

    def _extract_citations_from_text(self, text: str) -> List[str]:
        """Find citation markers like [1], [2] in generated text."""
        matches = re.findall(r"\[\d+\]", text)
        # Deduplicate while preserving order
        seen = set()
        citations = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                citations.append(m)
        return citations

    def _estimate_confidence(self, text: str, has_docs: bool = True) -> float:
        """Heuristic confidence calculation based on grounding cues."""
        if not has_docs:
            return 0.3
        lowered = text.lower()
        if "unable to find" in lowered or "no relevant" in lowered or "insufficient information" in lowered:
            return 0.4
        if "[" in text and "]" in text:
            return 0.95
        return 0.85

    @property
    def _type(self) -> str:
        return "team_memory_output_parser"
