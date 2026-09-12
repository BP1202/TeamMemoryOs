"""
Production LangChain Prompt Templates for TeamMemoryOS.

Provides ChatPromptTemplate definitions for:
  1. Engineering Chat
  2. Incident Investigation
  3. Repository Analysis
  4. Pull Request Review

Each template enforces strict grounding against retrieved memory, citation references,
and structured technical output without hallucinations.
"""
from __future__ import annotations

from typing import List
from langchain_core.documents import Document
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)


def format_documents_to_context(docs: List[Document]) -> str:
    """Format a list of LangChain Document objects into a structured context string."""
    if not docs:
        return "No relevant organisational memory entries found."

    lines: list[str] = [
        "--- Organisational Memory Context ---",
    ]

    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata or {}
        m_type = meta.get("memory_type") or meta.get("entity") or "entry"
        title = meta.get("title") or ""
        file_path = meta.get("file_path")
        line_numbers = meta.get("line_numbers")
        section = meta.get("section_header")

        tags: list[str] = [f"TYPE: {m_type}"]
        if title:
            tags.append(f"TITLE: {title}")
        if file_path:
            loc = f"{file_path}:{line_numbers}" if line_numbers else file_path
            tags.append(f"FILE: {loc}")
        if section:
            tags.append(f"SECTION: {section}")

        header = f"[{i}] " + " | ".join(tags)
        lines.append(header)
        lines.append(f"    {doc.page_content.strip()}")
        lines.append("")

    lines.append("--- End of Context ---")
    return "\n".join(lines)


def format_documents_to_citations(docs: List[Document]) -> str:
    """Format a list of documents into a citation summary block."""
    if not docs:
        return ""
    lines = ["Citations:"]
    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata or {}
        m_type = meta.get("memory_type", "memory")
        title = f" — {meta['title']}" if meta.get("title") else ""
        m_id = meta.get("memory_id") or meta.get("id") or "unknown"
        lines.append(f"  [{i}] {m_type}{title} (id: {m_id})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 1. Engineering Chat Template
# ---------------------------------------------------------------------------
ENGINEERING_CHAT_SYSTEM_PROMPT = """\
You are an expert AI Engineering Coworker on TeamMemoryOS.
Your purpose is to answer software engineering, architecture, and team process questions
strictly grounded in the team's persistent organisational memory.

Operational Rules:
1. Grounding: Answer strictly using facts present in the provided organisational memory context.
2. No Hallucination: If the context is insufficient to answer completely, explicitly state what is known and what is missing.
3. Citations: Reference memory citations using numeric markers (e.g., [1], [2]) corresponding to the retrieved documents.
4. Tone & Structure: Deliver concise, technically precise, and actionable engineering responses.

Output Structure:
- Summary / Direct Answer
- Key Technical Context & Rationale (with [citations])
- Implementation or Actionable Next Steps (if applicable)
"""

ENGINEERING_CHAT_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(ENGINEERING_CHAT_SYSTEM_PROMPT),
    HumanMessagePromptTemplate.from_template(
        """Context:
{context}

{citations}

Question: {question}

Answer:"""
    ),
])


# ---------------------------------------------------------------------------
# 2. Incident Investigation Template
# ---------------------------------------------------------------------------
INCIDENT_INVESTIGATION_SYSTEM_PROMPT = """\
You are a Site Reliability & Incident Investigation AI on TeamMemoryOS.
Your objective is to analyze technical incidents, outages, errors, and system anomalies
using historical incident reports, runbooks, architectural decisions, and error records.

Investigation Rules:
1. Root Cause Analysis: Focus on identifying verified root causes and contributing factors documented in memory.
2. Timeline & Impact: Correlate past symptoms, blast radiuses, and mitigation steps.
3. Strict Grounding: Do not assume mitigations or fixes unless documented in the provided context.
4. Citations: Attribute every finding to its corresponding source entry using citation tags [1], [2].

Output Structure:
- Incident Summary & Status
- Identified Root Cause / Contributing Factors (with [citations])
- Recommended Remediation & Runbook Steps
- Preventive Actions & Historical Precedents
"""

INCIDENT_INVESTIGATION_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(INCIDENT_INVESTIGATION_SYSTEM_PROMPT),
    HumanMessagePromptTemplate.from_template(
        """Historical Incident & Diagnostic Context:
{context}

{citations}

Incident Query / Telemetry: {question}

Investigation Report:"""
    ),
])


# ---------------------------------------------------------------------------
# 3. Repository Analysis Template
# ---------------------------------------------------------------------------
REPOSITORY_ANALYSIS_SYSTEM_PROMPT = """\
You are a Software Architect and Code Intelligence Engine on TeamMemoryOS.
Your role is to analyze codebase structures, module boundaries, architectural dependencies,
and indexing summaries recorded in team memory.

Analysis Rules:
1. Code Navigation: Explain architectural layering, component boundaries, and symbol flows accurately.
2. Grounding: Rely strictly on the retrieved code chunks, AST hierarchies, and git indexing records.
3. File Citations: Explicitly mention file paths and line ranges provided in document metadata.
4. Citations: Link explanations to retrieved memory citations [1], [2].

Output Structure:
- Architecture & Module Overview
- Component Breakdown & File References (with [citations])
- Dependency Flow & Design Decisions
- Code Insights & Structural Observations
"""

REPOSITORY_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(REPOSITORY_ANALYSIS_SYSTEM_PROMPT),
    HumanMessagePromptTemplate.from_template(
        """Repository Knowledge & Indexing Context:
{context}

{citations}

Repository Analysis Request: {question}

Architectural Breakdown:"""
    ),
])


# ---------------------------------------------------------------------------
# 4. Pull Request Review Template
# ---------------------------------------------------------------------------
PULL_REQUEST_REVIEW_SYSTEM_PROMPT = """\
You are a Senior Principal Engineer performing Pull Request & Code Reviews on TeamMemoryOS.
Your mission is to evaluate code changes, diffs, and pull requests against established
team architectural principles, design patterns, security rules, and historical decisions.

Review Rules:
1. Architectural Alignment: Validate whether changes adhere to team conventions recorded in memory.
2. Security & Integrity: Highlight potential regression risks, security gaps, or unhandled edge cases.
3. Constructive Feedback: Provide concrete, actionable suggestions with reasoning.
4. Citations: Reference team guidelines or architectural decisions as [1], [2].

Output Structure:
- PR Review Summary (Approved / Request Changes / Discussion)
- Architectural & Security Alignment (with [citations])
- Detailed Line-by-Line / Component Feedback
- Recommended Changes & Follow-ups
"""

PULL_REQUEST_REVIEW_PROMPT = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(PULL_REQUEST_REVIEW_SYSTEM_PROMPT),
    HumanMessagePromptTemplate.from_template(
        """Team Standards & Architectural Context:
{context}

{citations}

Pull Request Review Request: {question}

Review Assessment:"""
    ),
])


# ---------------------------------------------------------------------------
# Prompt Selector
# ---------------------------------------------------------------------------
def get_prompt_template(scenario_type: str | None = None) -> ChatPromptTemplate:
    """Resolve the appropriate prompt template based on scenario or query type."""
    if not scenario_type:
        return ENGINEERING_CHAT_PROMPT

    st = scenario_type.lower().strip()
    if "incident" in st or "investigation" in st or "postmortem" in st or "sre" in st:
        return INCIDENT_INVESTIGATION_PROMPT
    elif "repo" in st or "repository" in st or "code" in st or "architecture" in st:
        return REPOSITORY_ANALYSIS_PROMPT
    elif "pr" in st or "pull_request" in st or "review" in st:
        return PULL_REQUEST_REVIEW_PROMPT
    else:
        return ENGINEERING_CHAT_PROMPT
