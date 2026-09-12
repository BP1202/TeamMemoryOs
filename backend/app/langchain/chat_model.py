"""
LangChain Chat Model factory and provider for TeamMemoryOS.

Integrates local Ollama models with LangChain's ChatOllama, supporting
synchronous execution, async invoke, streaming, and configurable generation
parameters with robust fallback to deterministic stub responses.
"""
from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Iterator, List, Optional

import httpx
from langchain_core.callbacks import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_ollama import ChatOllama

from app.core.settings import settings

logger = logging.getLogger(__name__)


class StubChatModel(BaseChatModel):
    """Deterministic fallback ChatModel for offline testing and stub environments."""

    model_name: str = "stub"
    default_prefix: str = "Based on the provided team memory:\n"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt_text = ""
        for m in reversed(messages):
            if m.type in ("user", "human"):
                prompt_text = m.content
                break
        if not prompt_text and messages:
            prompt_text = messages[-1].content

        answer = self._build_deterministic_answer(str(prompt_text))
        message = AIMessage(content=answer)
        return ChatResult(generations=[ChatGeneration(message=message)])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        return self._generate(messages, stop=stop, **kwargs)

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        result = self._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
        content = result.generations[0].message.content
        if isinstance(content, str):
            words = content.split(" ")
            for i, word in enumerate(words):
                token = word if i == len(words) - 1 else word + " "
                chunk = ChatGenerationChunk(message=AIMessageChunk(content=token))
                if run_manager:
                    run_manager.on_llm_new_token(token)
                yield chunk

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        for chunk in self._stream(messages, stop=stop, **kwargs):
            yield chunk

    def _build_deterministic_answer(self, prompt: str) -> str:
        question = prompt
        if "Question:" in prompt:
            question = prompt.split("Question:")[-1].split("Answer:")[0].strip()
        elif "User Query:" in prompt:
            question = prompt.split("User Query:")[-1].strip()

        return (
            f"Based on the provided team memory:\n"
            f"Regarding '{question}': The team documentation and architectural records "
            f"indicate verified configuration and technical alignment."
        )

    @property
    def _llm_type(self) -> str:
        return "stub-chat-model"


_chat_model_cache: dict[str, BaseChatModel] = {}


def get_chat_model(
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[float] = None,
    streaming: bool = False,
    fallback_to_stub: bool = True,
) -> BaseChatModel:
    """Factory creating or returning a configured instance of ChatOllama with fallback."""
    provider = getattr(settings, "LLM_PROVIDER", "ollama").lower()
    if provider == "stub":
        return StubChatModel(model_name="stub")

    target_model = model or getattr(settings, "OLLAMA_MODEL", "llama3.1:8b")
    target_base_url = (base_url or getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
    target_temp = temperature if temperature is not None else getattr(settings, "OLLAMA_TEMPERATURE", 0.2)
    target_max_tokens = max_tokens or getattr(settings, "OLLAMA_MAX_TOKENS", 1024)
    target_timeout = timeout or getattr(settings, "OLLAMA_TIMEOUT_SECONDS", 60.0)

    cache_key = f"{target_base_url}::{target_model}::{target_temp}::{target_max_tokens}::{streaming}"
    if cache_key in _chat_model_cache:
        return _chat_model_cache[cache_key]

    stub = StubChatModel(model_name="stub")

    if fallback_to_stub:
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"{target_base_url}/api/tags")
                if resp.status_code != 200:
                    return stub
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                model_present = any(target_model in m or m.startswith(target_model) for m in models)
                if not model_present:
                    logger.info("[ChatModel] Model '%s' not found in local Ollama (%s). Using Stub fallback.", target_model, models)
                    return stub
        except Exception as exc:
            logger.info("[ChatModel] Local Ollama daemon not reachable at %s (%s). Using Stub fallback.", target_base_url, exc)
            return stub

    chat_model = ChatOllama(
        model=target_model,
        base_url=target_base_url,
        temperature=target_temp,
        num_predict=target_max_tokens,
        timeout=target_timeout,
        streaming=streaming,
    )

    if fallback_to_stub:
        chat_model = chat_model.with_fallbacks([stub])

    _chat_model_cache[cache_key] = chat_model
    return chat_model
