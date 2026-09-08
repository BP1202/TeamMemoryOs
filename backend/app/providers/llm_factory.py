"""
LLM Provider Factory for TeamMemoryOS.

Resolves and instantiates the configured BaseLLMProvider based on settings
or explicit caller overrides. Supports Ollama, Stub, and future LLM engines.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.settings import settings
from app.providers.base_provider import BaseLLMProvider, StubLLMProvider
from app.providers.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)


def get_llm_provider(
    provider_name: str | None = None,
    **kwargs: Any,
) -> BaseLLMProvider:
    """Return the configured or requested BaseLLMProvider instance.

    Args:
        provider_name: Explicit provider override ('ollama', 'stub', etc.).
                       If None, defaults to `settings.LLM_PROVIDER`.
        **kwargs: Optional overrides passed to provider constructor (e.g. model, base_url).

    Returns:
        An instance of BaseLLMProvider.
    """
    target = (provider_name or getattr(settings, "LLM_PROVIDER", "ollama") or "ollama").lower().strip()

    logger.debug("[LLMFactory] Resolving provider for target='%s'", target)

    if target == "ollama":
        return OllamaProvider(**kwargs)
    elif target == "stub":
        model_name = kwargs.get("model", "stub-model")
        return StubLLMProvider(model_name=model_name)
    else:
        logger.warning(
            "[LLMFactory] Unknown provider '%s'. Falling back to Ollama provider.",
            target,
        )
        return OllamaProvider(**kwargs)
