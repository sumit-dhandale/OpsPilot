"""LLM client implementations."""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

from opspilot.config import Settings
from opspilot.exceptions import LLMError
from opspilot.llm.prompts import LOG_ANALYSIS_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


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

        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise LLMError(f"LLM returned invalid JSON: {exc}") from exc

        if not isinstance(payload, dict):
            raise LLMError("LLM response must be a JSON object.")
        return payload


class OpenAICompatibleLLMClient(LLMClient):
    """OpenAI-compatible chat completions client."""

    def __init__(self, settings: Settings, model: str | None = None) -> None:
        self.api_key = settings.openai_api_key
        self.model = model or settings.llm_model
        self.base_url = settings.llm_base_url.rstrip("/")
        self.temperature = settings.llm_temperature
        self.timeout_seconds = settings.llm_timeout_seconds
        self.system_prompt = LOG_ANALYSIS_SYSTEM_PROMPT

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise LLMError("OPENAI_API_KEY is not configured.")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
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

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            logger.error("LLM HTTP error %s: %s", exc.code, detail)
            raise LLMError(f"LLM request failed with status {exc.code}") from exc
        except urllib.error.URLError as exc:
            logger.error("LLM connection error: %s", exc.reason)
            raise LLMError(f"LLM connection failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise LLMError("LLM request timed out") from exc

        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("LLM response missing expected content field") from exc
