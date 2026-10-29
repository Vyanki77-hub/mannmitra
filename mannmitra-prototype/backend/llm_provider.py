# llm_provider.py
# Minimal LLM Provider Abstraction for MannMitra.
# Decouples model calls from direct vendor-specific implementations.

import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from groq import Groq, RateLimitError

load_dotenv()


@dataclass
class LLMResponse:
    """Unified response object returned by all LLM providers."""
    content: str
    finish_reason: str | None = None

    @property
    def text(self) -> str:
        return self.content

    def __str__(self) -> str:
        return self.content or ""


class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 600,
        temperature: float | None = None,
    ) -> LLMResponse:
        """
        Generate completion for a list of conversation messages.
        Each message must be a dict with 'role' and 'content'.
        """
        raise NotImplementedError


class GroqProvider(LLMProvider):
    """
    Groq implementation preserving existing MannMitra behavior:
    - Default model: 'openai/gpt-oss-20b'
    - API key from GROQ_API_KEY environment variable
    - Supports max_completion_tokens and temperature
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "openai/gpt-oss-20b",
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is missing. Please add it to backend/.env")
        self.model = model
        self.client = Groq(api_key=self.api_key)

    def generate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 600,
        temperature: float | None = None,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_completion_tokens": max_tokens,
        }
        if temperature is not None:
            kwargs["temperature"] = temperature

        resp = self.client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content or ""
        finish_reason = getattr(resp.choices[0], "finish_reason", None)
        return LLMResponse(content=content, finish_reason=finish_reason)


class OllamaProvider(LLMProvider):
    """
    Local Ollama implementation:
    - Default base URL: 'http://127.0.0.1:11434' (configurable via OLLAMA_BASE_URL)
    - Default model: 'llama3.2:3b' (configurable via OLLAMA_MODEL)
    - Calls /api/chat with stream: False
    - Maps max_tokens to options.num_predict, sets options.num_ctx = 4096
    - Preserves LLMResponse contract
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
    ):
        raw_base = base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.base_url = raw_base.rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.timeout = timeout

    def generate(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 600,
        temperature: float | None = None,
    ) -> LLMResponse:
        endpoint = f"{self.base_url}/api/chat"
        options: dict[str, Any] = {
            "num_predict": max_tokens,
            "num_ctx": 4096,
        }
        if temperature is not None:
            options["temperature"] = temperature

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": options,
        }

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                endpoint,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw_body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            raise RuntimeError(
                f"Ollama API error: HTTP {e.code} ({e.reason}) at {endpoint}"
            ) from e
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"Ollama connection failed at {endpoint}: {e.reason}"
            ) from e
        except TimeoutError as e:
            raise RuntimeError(
                f"Ollama request timed out after {self.timeout}s at {endpoint}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"Ollama request failed unexpectedly: {type(e).__name__}: {str(e)}"
            ) from e

        try:
            data = json.loads(raw_body)
        except Exception as e:
            raise RuntimeError(
                f"Ollama returned malformed JSON response: {type(e).__name__}"
            ) from e

        if not isinstance(data, dict):
            raise RuntimeError(
                f"Ollama response root is not a dictionary (got {type(data).__name__})"
            )

        msg_obj = data.get("message")
        if not isinstance(msg_obj, dict):
            if "error" in data:
                raise RuntimeError(f"Ollama error: {data['error']}")
            raise RuntimeError("Ollama response missing valid 'message' object")

        content = msg_obj.get("content")
        if content is None:
            content = ""
        elif not isinstance(content, str):
            content = str(content)

        finish_reason = data.get("done_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            finish_reason = str(finish_reason)

        return LLMResponse(content=content, finish_reason=finish_reason)


def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    """
    Factory function for provider selection.
    Controlled by LLM_PROVIDER env var, defaulting to 'groq'.
    Fails clearly with a helpful error if an unsupported provider is requested.
    """
    if provider_name is None:
        raw_env = os.getenv("LLM_PROVIDER")
        provider_name = raw_env if (raw_env and raw_env.strip()) else "groq"
    elif not provider_name.strip():
        provider_name = "groq"

    key = provider_name.strip().lower()

    if key == "groq":
        return GroqProvider()
    elif key == "ollama":
        return OllamaProvider()
    else:
        raise ValueError(
            f"Unsupported LLM provider: '{provider_name}'. Supported providers: ['groq', 'ollama']."
        )
