"""Talking to a model. The backend is a configuration choice, not a hard-coded format."""

import uuid
from functools import lru_cache
from typing import Protocol, runtime_checkable

import httpx

from aitsm.core.config import settings

DEFAULT_SYSTEM_PROMPT = "You are a helpful ITSM assistant."


class LLMError(RuntimeError):
    """The model backend could not answer. Business code treats this as a failed call."""


@runtime_checkable
class LLM(Protocol):
    """One method: send text with a system prompt, get text back."""

    def invoke(self, text: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> str: ...


class OllamaLLM:
    """Local models over Ollama's HTTP API. The default: it is what a reader can run."""

    def __init__(self, host: str, model: str, timeout: float) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout

    def invoke(self, text: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> str:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            "stream": False,
            "options": {"temperature": 0.3},
        }
        try:
            response = httpx.post(f"{self.host}/api/chat", json=body, timeout=self.timeout)
            response.raise_for_status()
            return response.json()["message"]["content"]
        except httpx.HTTPError as exc:
            raise LLMError(f"Ollama unavailable at {self.host}: {exc}") from exc
        except (KeyError, ValueError) as exc:
            raise LLMError(f"Unexpected answer from Ollama: {exc}") from exc


class GatewayLLM:
    """A hosted gateway with its own request envelope. Kept for the deployment that has one."""

    def __init__(
        self,
        url: str,
        api_key: str,
        model: str,
        provider: str,
        workspace_id: str,
        timeout: float,
    ) -> None:
        self.url = url
        self.api_key = api_key
        self.model = model
        self.provider = provider
        self.workspace_id = workspace_id
        self.timeout = timeout

    def invoke(self, text: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            headers["x-api-key"] = self.api_key

        body = {
            "action": "run",
            "modelInterface": "langchain",
            "data": {
                "mode": "chain",
                "text": text,
                "files": [],
                "modelName": self.model,
                "provider": self.provider,
                "systemPrompt": system_prompt,
                "sessionId": str(uuid.uuid4()),
                "workspaceId": self.workspace_id or None,
                "modelKwargs": {
                    "maxTokens": 512,
                    "temperature": 0.3,  # Good tradeoff between creativity and relevance
                    "streaming": False,
                    "topP": 0.9,
                },
            },
        }
        try:
            response = httpx.post(self.url, json=body, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()["content"]
        except httpx.HTTPError as exc:
            raise LLMError(f"LLM gateway unavailable: {exc}") from exc
        except (KeyError, ValueError) as exc:
            raise LLMError(f"Unexpected answer from the LLM gateway: {exc}") from exc


BACKENDS = ("ollama", "gateway")


@lru_cache(maxsize=1)
def get_llm() -> LLM:
    """Build the configured backend once. Adding one means adding a branch here."""
    if settings.LLM_BACKEND == "ollama":
        return OllamaLLM(settings.OLLAMA_HOST, settings.OLLAMA_MODEL, settings.LLM_TIMEOUT)
    if settings.LLM_BACKEND == "gateway":
        return GatewayLLM(
            settings.LLM_API_URL,
            settings.LLM_API_KEY,
            settings.LLM_MODEL_NAME,
            settings.LLM_PROVIDER,
            settings.LLM_WORKSPACE_ID,
            settings.LLM_TIMEOUT,
        )
    raise LLMError(f"Unknown LLM_BACKEND '{settings.LLM_BACKEND}'. Use one of: {BACKENDS}.")


def invoke(text: str, system_prompt: str = DEFAULT_SYSTEM_PROMPT) -> str:
    """Module-level facade, so callers do not pick a backend.

    Tests replace this function rather than injecting a client: the three call sites in
    ai_service are about prompting, not about which backend answers.
    """
    return get_llm().invoke(text, system_prompt=system_prompt)
