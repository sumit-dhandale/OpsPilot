from __future__ import annotations

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class StubLLMClient(LLMClient):
    """Simple in-memory implementation used for boilerplate/testing."""

    def generate(self, prompt: str) -> str:
        return "LLM integration placeholder. This project is intentionally scoped to Phase 1 boilerplate."
