"""
Granite generation provider abstraction for TeamMemoryOS.

Defines the ``GenerationProvider`` protocol that any text-generation backend
must satisfy.  Two implementations are provided:

* ``StubGenerationProvider`` — fully deterministic, no network, no credentials.
  Used in all tests and local development by default.

* ``GraniteProvider`` — calls IBM watsonx.ai via its OpenAI-compatible REST API
  using the ``openai`` SDK.  Activated when ``GRANITE_PROVIDER=granite`` is set
  in environment configuration.

No LangChain is used.  The provider is isolated from retrieval and prompt logic.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.core.settings import settings


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


# ---------------------------------------------------------------------------
# Stub provider
# ---------------------------------------------------------------------------

class StubGenerationProvider:
    """Deterministic stub — echoes the question back with a structured reply.

    Used in tests and local development.  Never calls any external service.
    """

    @property
    def provider_name(self) -> str:
        return "stub"

    def generate(self, prompt: str) -> str:
        # Extract the last line that starts with "Question:" for a tidy echo.
        for line in reversed(prompt.splitlines()):
            line = line.strip()
            if line.lower().startswith("question:"):
                question = line[len("question:"):].strip()
                return (
                    f"[Stub response] This is a deterministic answer for: "
                    f'"{question}". '
                    "In production, IBM Granite will provide a grounded answer "
                    "based on the retrieved organisational memory."
                )
        return (
            "[Stub response] No question found in prompt. "
            "IBM Granite will generate a grounded answer in production."
        )


# ---------------------------------------------------------------------------
# IBM Granite provider (watsonx.ai via OpenAI-compatible API)
# ---------------------------------------------------------------------------

class GraniteProvider:
    """Calls IBM watsonx.ai using the OpenAI-compatible chat completions API.

    watsonx.ai exposes the same endpoint shape as the OpenAI SDK, so we use
    the ``openai`` client with a custom ``base_url`` and API key.  No
    LangChain, no IBM SDK — just one direct HTTP call.

    Requires environment variables:
        GRANITE_API_KEY      — IBM Cloud IAM API key.
        GRANITE_BASE_URL     — watsonx.ai inference endpoint.
        GRANITE_MODEL_ID     — e.g. "ibm/granite-3-8b-instruct".
        GRANITE_PROJECT_ID   — watsonx.ai project UUID.
        GRANITE_MAX_TOKENS   — token budget for generated text.
    """

    def __init__(self) -> None:
        try:
            from openai import OpenAI  # lazy import — only needed for real provider
        except ImportError as exc:
            raise RuntimeError(
                "The 'openai' package is required for GraniteProvider. "
                "Add it to requirements.txt."
            ) from exc

        if not settings.GRANITE_API_KEY:
            raise ValueError(
                "GRANITE_API_KEY must be set when GRANITE_PROVIDER=granite. "
                "Set GRANITE_PROVIDER=stub to run without credentials."
            )

        # watsonx.ai appends the project_id as a query parameter.
        base_url = settings.GRANITE_BASE_URL.rstrip("/")
        if settings.GRANITE_PROJECT_ID:
            # The OpenAI client passes the base URL as-is; append project_id here
            # so every request carries it automatically.
            base_url = f"{base_url}?version=2023-05-29&project_id={settings.GRANITE_PROJECT_ID}"

        self._client = OpenAI(
            api_key=settings.GRANITE_API_KEY,
            base_url=base_url,
        )
        self._model = settings.GRANITE_MODEL_ID
        self._max_tokens = settings.GRANITE_MAX_TOKENS

    @property
    def provider_name(self) -> str:
        return "granite"

    def generate(self, prompt: str) -> str:
        """Send the full assembled prompt and return the model's reply text."""
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self._max_tokens,
            temperature=0.2,  # low temperature for factual, grounded answers
        )
        return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# Factory — resolves provider from settings
# ---------------------------------------------------------------------------

def get_generation_provider() -> GenerationProvider:
    """Return the configured ``GenerationProvider`` instance.

    Reads ``GRANITE_PROVIDER`` from settings:
    * ``"stub"``    → ``StubGenerationProvider`` (default, no credentials)
    * ``"granite"`` → ``GraniteProvider`` (requires IBM credentials)
    """
    if settings.GRANITE_PROVIDER == "granite":
        return GraniteProvider()
    return StubGenerationProvider()
