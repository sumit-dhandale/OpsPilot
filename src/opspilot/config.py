from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Settings:
    """Project defaults for the log analysis pipeline."""

    allowed_extensions: set[str] = field(default_factory=lambda: {".log", ".txt"})
    max_file_size_mb: int = 200
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2


DEFAULT_SETTINGS = Settings()
