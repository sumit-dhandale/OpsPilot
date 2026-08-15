"""LLM provider presets and runtime resolution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from opspilot.config import Settings
from opspilot.exceptions import LLMError

ProviderName = Literal["openai", "gemini", "grok", "groq", "ollama", "custom"]
SUPPORTED_PROVIDERS: tuple[ProviderName, ...] = (
    "openai",
    "gemini",
    "grok",
    "groq",
    "ollama",
    "custom",
)


@dataclass(frozen=True)
class ProviderPreset:
    name: ProviderName
    base_url: str
    default_model: str
    requires_api_key: bool = True
    supports_json_response_format: bool = True


@dataclass(frozen=True)
class ResolvedProviderConfig:
    provider: ProviderName
    api_key: str
    model: str
    base_url: str
    temperature: float
    timeout_seconds: int
    supports_json_response_format: bool


PROVIDER_PRESETS: dict[ProviderName, ProviderPreset] = {
    "openai": ProviderPreset(
        name="openai",
        base_url="https://api.openai.com/v1",
        default_model="gpt-4o-mini",
    ),
    "gemini": ProviderPreset(
        name="gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        default_model="gemini-2.0-flash",
    ),
    "grok": ProviderPreset(
        name="grok",
        base_url="https://api.x.ai/v1",
        default_model="grok-2-latest",
    ),
    "groq": ProviderPreset(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        default_model="llama-3.3-70b-versatile",
    ),
    "ollama": ProviderPreset(
        name="ollama",
        base_url="http://localhost:11434/v1",
        default_model="llama3.2",
        requires_api_key=False,
        supports_json_response_format=False,
    ),
    "custom": ProviderPreset(
        name="custom",
        base_url="",
        default_model="gpt-4o-mini",
    ),
}


def normalize_provider_name(value: str | None, default: str = "openai") -> ProviderName:
    candidate = (value or default).strip().lower()
    if candidate not in PROVIDER_PRESETS:
        supported = ", ".join(SUPPORTED_PROVIDERS)
        raise LLMError(f"Unsupported LLM provider '{candidate}'. Supported providers: {supported}")
    return candidate  # type: ignore[return-value]


def resolve_provider_config(
    settings: Settings,
    provider: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
) -> ResolvedProviderConfig | None:
    """Resolve provider settings for a single analysis request."""
    provider_name = normalize_provider_name(provider or settings.llm_provider)
    preset = PROVIDER_PRESETS[provider_name]
    api_key = _resolve_api_key(settings, provider_name)
    if preset.requires_api_key and not api_key:
        return None

    resolved_base_url = (base_url or settings.llm_base_url or preset.base_url).rstrip("/")
    if provider_name == "custom" and not resolved_base_url:
        raise LLMError(
            "Custom provider requires a base URL via --base-url or OPSPILOT_LLM_BASE_URL."
        )

    resolved_model = model or (
        settings.llm_model if provider_name == "custom" else preset.default_model
    )

    return ResolvedProviderConfig(
        provider=provider_name,
        api_key=api_key or "local",
        model=resolved_model,
        base_url=resolved_base_url,
        temperature=settings.llm_temperature,
        timeout_seconds=settings.llm_timeout_seconds,
        supports_json_response_format=preset.supports_json_response_format,
    )


def _resolve_api_key(settings: Settings, provider: ProviderName) -> str | None:
    if provider == "openai":
        return settings.openai_api_key or settings.llm_api_key
    if provider == "gemini":
        return settings.gemini_api_key or settings.llm_api_key
    if provider == "grok":
        return settings.grok_api_key or settings.llm_api_key
    if provider == "groq":
        return settings.groq_api_key or settings.llm_api_key
    if provider == "ollama":
        return settings.llm_api_key
    return settings.llm_api_key or settings.openai_api_key
