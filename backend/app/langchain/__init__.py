"""
TeamMemoryOS LangChain Production RAG Pipeline.

Exports core components:
- Chat Models: get_chat_model, StubChatModel
- Retriever: TeamMemoryPGVectorRetriever, get_memory_retriever
- Prompt Templates: get_prompt_template, ENGINEERING_CHAT_PROMPT, INCIDENT_INVESTIGATION_PROMPT, REPOSITORY_ANALYSIS_PROMPT, PULL_REQUEST_REVIEW_PROMPT
- Chains & Pipeline: build_rag_chain, run_rag_chain, arun_rag_chain
- Streaming: stream_rag_chain, astream_rag_chain
- Output Parsers: TeamMemoryOutputParser, TeamMemoryRAGOutput
"""
from app.langchain.chat_model import StubChatModel, get_chat_model
from app.langchain.chains import arun_rag_chain, build_rag_chain, run_rag_chain
from app.langchain.output_parser import TeamMemoryOutputParser, TeamMemoryRAGOutput
from app.langchain.prompt_templates import (
    ENGINEERING_CHAT_PROMPT,
    INCIDENT_INVESTIGATION_PROMPT,
    PULL_REQUEST_REVIEW_PROMPT,
    REPOSITORY_ANALYSIS_PROMPT,
    format_documents_to_citations,
    format_documents_to_context,
    get_prompt_template,
)
from app.langchain.retriever import TeamMemoryPGVectorRetriever, get_memory_retriever
from app.langchain.streaming import astream_rag_chain, stream_rag_chain

__all__ = [
    "StubChatModel",
    "get_chat_model",
    "TeamMemoryPGVectorRetriever",
    "get_memory_retriever",
    "ENGINEERING_CHAT_PROMPT",
    "INCIDENT_INVESTIGATION_PROMPT",
    "REPOSITORY_ANALYSIS_PROMPT",
    "PULL_REQUEST_REVIEW_PROMPT",
    "format_documents_to_context",
    "format_documents_to_citations",
    "get_prompt_template",
    "build_rag_chain",
    "run_rag_chain",
    "arun_rag_chain",
    "stream_rag_chain",
    "astream_rag_chain",
    "TeamMemoryOutputParser",
    "TeamMemoryRAGOutput",
]
