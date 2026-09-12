"""
Local Ollama LLM Provider for TeamMemoryOS.

Connects to a locally running Ollama instance via its native HTTP REST API.
Supports streaming responses, synchronous and asynchronous execution,
and model health checks.
"""
from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any

import httpx

from app.core.settings import settings
from app.providers.base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """LLM Provider powered by a local Ollama daemon."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        fallback_to_stub: bool = True,
    ) -> None:
        from app.providers.base_provider import StubLLMProvider

        self._base_url = (base_url or getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self._model = model or getattr(settings, "OLLAMA_MODEL", "llama3.1:8b")
        self._timeout = timeout or getattr(settings, "OLLAMA_TIMEOUT_SECONDS", 60.0)
        self._temperature = temperature if temperature is not None else getattr(settings, "OLLAMA_TEMPERATURE", 0.2)
        self._max_tokens = max_tokens or getattr(settings, "OLLAMA_MAX_TOKENS", 1024)
        self._fallback_to_stub = fallback_to_stub
        self._stub = StubLLMProvider(model_name=f"{self._model}-stub")

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def base_url(self) -> str:
        return self._base_url

    def _build_payload(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        temp = temperature if temperature is not None else self._temperature
        num_predict = max_tokens or self._max_tokens

        payload: dict[str, Any] = {
            "model": self._model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temp,
                "num_predict": num_predict,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt
        return payload

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Synchronous prompt generation via Ollama /api/generate."""
        payload = self._build_payload(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        url = f"{self._base_url}/api/generate"
        logger.info("[OllamaProvider] Generating with model '%s' at %s (prompt len=%d)", self._model, url, len(prompt))

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip()
        except httpx.ConnectError as exc:
            logger.warning("[OllamaProvider] Could not connect to Ollama at %s: %s", self._base_url, exc)
            if self._fallback_to_stub:
                logger.info("[OllamaProvider] Falling back to deterministic stub response.")
                return self._stub.generate(prompt, system_prompt, temperature, max_tokens, **kwargs)
            raise RuntimeError(
                f"Could not connect to Ollama at {self._base_url}. Please ensure 'ollama serve' is running."
            ) from exc
        except httpx.HTTPStatusError as exc:
            logger.error("[OllamaProvider] Ollama HTTP %s: %s", exc.response.status_code, exc.response.text)
            if self._fallback_to_stub:
                return self._stub.generate(prompt, system_prompt, temperature, max_tokens, **kwargs)
            raise RuntimeError(
                f"Ollama returned error status {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except Exception as exc:
            logger.error("[OllamaProvider] Unexpected error during generation: %s", exc)
            if self._fallback_to_stub:
                return self._stub.generate(prompt, system_prompt, temperature, max_tokens, **kwargs)
            raise

    async def agenerate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Asynchronous prompt generation via Ollama /api/generate."""
        payload = self._build_payload(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        url = f"{self._base_url}/api/generate"
        logger.info("[OllamaProvider] Async generating with model '%s' at %s", self._model, url)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip()
        except httpx.ConnectError as exc:
            logger.warning("[OllamaProvider] Failed to connect to Ollama at %s: %s", self._base_url, exc)
            if self._fallback_to_stub:
                return await self._stub.agenerate(prompt, system_prompt, temperature, max_tokens, **kwargs)
            raise RuntimeError(
                f"Could not connect to Ollama at {self._base_url}. Please ensure 'ollama serve' is running."
            ) from exc
        except httpx.HTTPStatusError as exc:
            logger.error("[OllamaProvider] Ollama HTTP %s: %s", exc.response.status_code, exc.response.text)
            if self._fallback_to_stub:
                return await self._stub.agenerate(prompt, system_prompt, temperature, max_tokens, **kwargs)
            raise RuntimeError(
                f"Ollama returned error status {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except Exception as exc:
            logger.error("[OllamaProvider] Unexpected error during async generation: %s", exc)
            if self._fallback_to_stub:
                return await self._stub.agenerate(prompt, system_prompt, temperature, max_tokens, **kwargs)
            raise

    def stream_generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Synchronous streaming generation via Ollama /api/generate."""
        payload = self._build_payload(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        url = f"{self._base_url}/api/generate"
        logger.info("[OllamaProvider] Streaming with model '%s' at %s", self._model, url)

        try:
            with httpx.Client(timeout=self._timeout) as client:
                with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            token = chunk.get("response", "")
                            if token:
                                yield token
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError as exc:
            logger.warning("[OllamaProvider] Stream connection failed to Ollama at %s: %s", self._base_url, exc)
            if self._fallback_to_stub:
                for token in self._stub.stream_generate(prompt, system_prompt, temperature, max_tokens, **kwargs):
                    yield token
                return
            raise RuntimeError(
                f"Could not connect to Ollama at {self._base_url}. Please ensure 'ollama serve' is running."
            ) from exc
        except Exception as exc:
            logger.error("[OllamaProvider] Error during streaming: %s", exc)
            if self._fallback_to_stub:
                for token in self._stub.stream_generate(prompt, system_prompt, temperature, max_tokens, **kwargs):
                    yield token
                return
            raise

    async def astream_generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Asynchronous streaming generation via Ollama /api/generate."""
        payload = self._build_payload(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        url = f"{self._base_url}/api/generate"
        logger.info("[OllamaProvider] Async streaming with model '%s' at %s", self._model, url)

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            token = chunk.get("response", "")
                            if token:
                                yield token
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError as exc:
            logger.warning("[OllamaProvider] Async stream connection failed to Ollama at %s: %s", self._base_url, exc)
            if self._fallback_to_stub:
                async for token in self._stub.astream_generate(prompt, system_prompt, temperature, max_tokens, **kwargs):
                    yield token
                return
            raise RuntimeError(
                f"Could not connect to Ollama at {self._base_url}. Please ensure 'ollama serve' is running."
            ) from exc
        except Exception as exc:
            logger.error("[OllamaProvider] Error during async streaming: %s", exc)
            if self._fallback_to_stub:
                async for token in self._stub.astream_generate(prompt, system_prompt, temperature, max_tokens, **kwargs):
                    yield token
                return
            raise

    def is_available(self) -> bool:
        """Check if Ollama server is reachable and active."""
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(f"{self._base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    async def acheck_health(self) -> dict[str, Any]:
        """Detailed health check returning status and model list."""
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    model_present = any(self._model in m or m.startswith(self._model) for m in models)
                    return {
                        "status": "healthy",
                        "provider": "ollama",
                        "base_url": self._base_url,
                        "model": self._model,
                        "model_available": model_present,
                        "available_models": models,
                    }
                return {
                    "status": "unhealthy",
                    "provider": "ollama",
                    "base_url": self._base_url,
                    "model": self._model,
                    "error": f"HTTP {resp.status_code}",
                }
        except httpx.ConnectError:
            return {
                "status": "offline",
                "provider": "ollama",
                "base_url": self._base_url,
                "model": self._model,
                "error": f"Cannot connect to Ollama at {self._base_url}. Is 'ollama serve' running?",
            }
        except Exception as exc:
            return {
                "status": "error",
                "provider": "ollama",
                "base_url": self._base_url,
                "model": self._model,
                "error": str(exc),
            }
