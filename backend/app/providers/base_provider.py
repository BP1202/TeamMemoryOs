"""
Base LLM Provider interface and deterministic Stub implementation.

Defines the contract that any LLM backend (Ollama, Granite, OpenAI, Gemini, etc.)
must fulfill to integrate with TeamMemoryOS.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterator
from typing import Any

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract Base Class defining the LLM Provider interface."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'ollama', 'stub', 'granite')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the active model (e.g., 'llama3.1:8b', 'granite3-dense:2b')."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Synchronously send prompt to the model and return complete text."""
        pass

    @abstractmethod
    async def agenerate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Asynchronously send prompt to the model and return complete text."""
        pass

    @abstractmethod
    def stream_generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Synchronously stream response tokens from the model."""
        pass

    @abstractmethod
    async def astream_generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Asynchronously stream response tokens from the model."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider backend is reachable and ready."""
        pass

    @abstractmethod
    async def acheck_health(self) -> dict[str, Any]:
        """Check detailed provider health status and installed models."""
        pass


class StubLLMProvider(BaseLLMProvider):
    """Deterministic stub provider for testing and offline fallback."""

    def __init__(self, model_name: str = "stub-model") -> None:
        self._model_name = model_name

    @property
    def provider_name(self) -> str:
        return "stub"

    @property
    def model_name(self) -> str:
        return self._model_name

    def _generate_stub_response(self, prompt: str) -> str:
        for line in reversed(prompt.splitlines()):
            line = line.strip()
            if line.lower().startswith("question:"):
                q = line[len("question:"):].strip()
                return (
                    f"[Stub response] This is a deterministic answer for: "
                    f'"{q}". In production, the local Ollama LLM provides '
                    "a grounded response based on organizational memory."
                )
        return (
            "[Stub response] This is a deterministic answer from the Stub LLM Provider."
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        logger.info("[StubLLMProvider] generate called with prompt length %d", len(prompt))
        return self._generate_stub_response(prompt)

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        return self.generate(prompt, system_prompt, temperature, max_tokens, **kwargs)

    def stream_generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        response = self.generate(prompt, system_prompt, temperature, max_tokens, **kwargs)
        # Yield words to simulate streaming
        words = response.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")

    async def astream_generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        for token in self.stream_generate(prompt, system_prompt, temperature, max_tokens, **kwargs):
            yield token

    def is_available(self) -> bool:
        return True

    async def acheck_health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "provider": "stub",
            "model": self.model_name,
            "available_models": [self.model_name],
            "message": "Stub provider is always available.",
        }
