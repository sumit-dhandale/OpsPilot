"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the log analysis agent."""

    model_config = SettingsConfigDict(
        env_prefix="OPSPILOT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    allowed_extensions: set[str] = Field(default={".log", ".txt"})
    max_file_size_mb: int = 200
    max_evidence_lines: int = 500
    max_level_evidence_lines: int = 150

    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2
    llm_timeout_seconds: int = 120
    llm_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "OPSPILOT_OPENAI_API_KEY"),
    )

    log_level: str = "INFO"

    @field_validator("allowed_extensions", mode="before")
    @classmethod
    def parse_extensions(cls, value: object) -> set[str]:
        if isinstance(value, str):
            return {item.strip() for item in value.split(",") if item.strip()}
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
