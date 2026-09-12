"""
Generation provider abstraction for TeamMemoryOS.

Defines the ``GenerationProvider`` protocol and integrates with the unified
``app.providers`` provider subsystem (Ollama, Stub, etc.).
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.core.settings import settings
from app.providers.base_provider import BaseLLMProvider, StubLLMProvider
from app.providers.llm_factory import get_llm_provider
from app.providers.ollama_provider import OllamaProvider


@runtime_checkable
class GenerationProvider(Protocol):
    """Provider-agnostic contract for text generation."""

    def generate(self, prompt: str) -> str:
        """Send ``prompt`` to the model and return the generated text."""
        ...

    @property
    def provider_name(self) -> str:
        """Human-readable name of the active provider."""
        ...


# Type aliases for backwards compatibility
StubGenerationProvider = StubLLMProvider
OllamaGraniteProvider = OllamaProvider


class GraniteProvider(StubLLMProvider):
    """Fallback stub for legacy Granite provider references."""

    @property
    def provider_name(self) -> str:
        return "granite-legacy-stub"


def get_generation_provider() -> BaseLLMProvider:
    """Return the configured ``BaseLLMProvider`` from the provider factory."""
    if getattr(settings, "GRANITE_PROVIDER", "") == "stub" and getattr(settings, "LLM_PROVIDER", "ollama") == "ollama":
        return get_llm_provider("stub")

    provider_name = getattr(settings, "LLM_PROVIDER", None) or getattr(settings, "GRANITE_PROVIDER", "ollama")
    return get_llm_provider(provider_name)
