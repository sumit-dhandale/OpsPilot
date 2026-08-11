from __future__ import annotations

import json
import os
import re
import urllib.request
from abc import ABC, abstractmethod
from typing import Any


class LLMClient(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError

    def generate_json(self, prompt: str) -> dict[str, Any]:
        raw = self.generate(prompt)
        return self._parse_json_response(raw)

    def _parse_json_response(self, raw: str) -> dict[str, Any]:
        cleaned = raw.strip()
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if fence_match:
            cleaned = fence_match.group(1).strip()

        payload = json.loads(cleaned)
        if not isinstance(payload, dict):
            raise ValueError("LLM response must be a JSON object.")
        return payload


class OpenAICompatibleLLMClient(LLMClient):
    """Minimal OpenAI-compatible client configured via environment variables."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        temperature: float | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPSPILOT_LLM_MODEL", "gpt-4o-mini")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.temperature = temperature if temperature is not None else float(os.getenv("OPSPILOT_LLM_TEMPERATURE", "0.2"))
        self.timeout_seconds = timeout_seconds or int(os.getenv("OPSPILOT_LLM_TIMEOUT", "120"))

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an on-call log analysis agent. "
                        "Return only valid JSON matching the requested schema. "
                        "Be concise, evidence-based, and avoid speculation."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
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

        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))

        return body["choices"][0]["message"]["content"]
