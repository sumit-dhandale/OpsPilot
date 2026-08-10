from __future__ import annotations

import json
import os
import urllib.request
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class OpenAICompatibleLLMClient(LLMClient):
    """Minimal OpenAI-compatible client that can be configured via environment variables."""

    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPSPILOT_LLM_MODEL", "gpt-4o-mini")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured. Set it or use a fallback analyzer.")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an engineering analyst. Be concise, evidence-based, and explain technical material in simple language."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))

        return body["choices"][0]["message"]["content"]


class FallbackLLMClient(LLMClient):
    """Used when no external API is configured; returns a brief note instead of failing."""

    def generate(self, prompt: str) -> str:
        return "LLM output skipped because no model key is configured. The local heuristic analysis is used instead."
