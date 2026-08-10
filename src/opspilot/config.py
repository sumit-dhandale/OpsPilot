from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Settings:
    """Project defaults for single-file code/log analysis."""

    allowed_extensions: set[str] = field(default_factory=lambda: {".log", ".txt", ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".cs", ".rb", ".php"})
    max_file_size_mb: int = 200
    llm_model: str = os.getenv("OPSPILOT_LLM_MODEL", "gpt-4o-mini")
    llm_temperature: float = 0.2
    llm_api_key: str | None = os.getenv("OPENAI_API_KEY")
    llm_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")


DEFAULT_SETTINGS = Settings()
