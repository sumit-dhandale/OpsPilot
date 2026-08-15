import unittest

from opspilot.config import Settings
from opspilot.exceptions import LLMError
from opspilot.factory import build_log_analysis_agent
from opspilot.llm.client import OpenAICompatibleLLMClient
from opspilot.llm.providers import resolve_provider_config


class ProviderConfigTests(unittest.TestCase):
    def test_openai_provider_uses_openai_key_and_defaults(self):
        config = resolve_provider_config(
            Settings(openai_api_key="openai-key"),
            provider="openai",
        )

        self.assertIsNotNone(config)
        assert config is not None
        self.assertEqual(config.provider, "openai")
        self.assertEqual(config.api_key, "openai-key")
        self.assertEqual(config.base_url, "https://api.openai.com/v1")
        self.assertEqual(config.model, "gpt-4o-mini")

    def test_gemini_provider_uses_gemini_key_and_defaults(self):
        config = resolve_provider_config(
            Settings(gemini_api_key="gemini-key"),
            provider="gemini",
        )

        self.assertIsNotNone(config)
        assert config is not None
        self.assertEqual(config.provider, "gemini")
        self.assertEqual(config.api_key, "gemini-key")
        self.assertEqual(
            config.base_url,
            "https://generativelanguage.googleapis.com/v1beta/openai",
        )
        self.assertEqual(config.model, "gemini-2.0-flash")

    def test_grok_provider_uses_grok_key_and_defaults(self):
        config = resolve_provider_config(
            Settings(grok_api_key="grok-key"),
            provider="grok",
        )

        self.assertIsNotNone(config)
        assert config is not None
        self.assertEqual(config.provider, "grok")
        self.assertEqual(config.api_key, "grok-key")
        self.assertEqual(config.base_url, "https://api.x.ai/v1")
        self.assertEqual(config.model, "grok-2-latest")

    def test_groq_provider_uses_groq_key_and_defaults(self):
        config = resolve_provider_config(
            Settings(groq_api_key="groq-key"),
            provider="groq",
        )

        self.assertIsNotNone(config)
        assert config is not None
        self.assertEqual(config.provider, "groq")
        self.assertEqual(config.api_key, "groq-key")
        self.assertEqual(config.base_url, "https://api.groq.com/openai/v1")
        self.assertEqual(config.model, "llama-3.3-70b-versatile")

    def test_ollama_provider_works_without_api_key(self):
        settings = Settings.model_construct(
            llm_provider="ollama",
            llm_model="gpt-4o-mini",
            llm_temperature=0.2,
            llm_timeout_seconds=120,
            allowed_extensions={".log", ".txt"},
            max_file_size_mb=200,
            max_evidence_lines=500,
            max_level_evidence_lines=150,
            openai_api_key=None,
            gemini_api_key=None,
            grok_api_key=None,
            groq_api_key=None,
            llm_api_key=None,
            log_level="INFO",
        )
        config = resolve_provider_config(settings, provider="ollama")

        self.assertIsNotNone(config)
        assert config is not None
        self.assertEqual(config.provider, "ollama")
        self.assertEqual(config.api_key, "local")
        self.assertEqual(config.base_url, "http://localhost:11434/v1")
        self.assertEqual(config.model, "llama3.2")
        self.assertFalse(config.supports_json_response_format)

    def test_model_and_base_url_overrides_apply_per_request(self):
        config = resolve_provider_config(
            Settings(openai_api_key="openai-key"),
            provider="openai",
            model="gpt-4o",
            base_url="https://example.test/v1",
        )

        self.assertIsNotNone(config)
        assert config is not None
        self.assertEqual(config.model, "gpt-4o")
        self.assertEqual(config.base_url, "https://example.test/v1")

    def test_custom_provider_requires_base_url(self):
        settings = Settings.model_construct(
            llm_api_key="shared-key",
            llm_base_url=None,
            llm_provider="custom",
            llm_model="gpt-4o-mini",
            llm_temperature=0.2,
            llm_timeout_seconds=120,
            allowed_extensions={".log", ".txt"},
            max_file_size_mb=200,
            max_evidence_lines=500,
            max_level_evidence_lines=150,
            openai_api_key=None,
            gemini_api_key=None,
            grok_api_key=None,
            groq_api_key=None,
            log_level="INFO",
        )
        with self.assertRaises(LLMError):
            resolve_provider_config(settings, provider="custom")

    def test_missing_provider_key_returns_none(self):
        settings = Settings.model_construct(
            llm_provider="gemini",
            llm_model="gpt-4o-mini",
            llm_temperature=0.2,
            llm_timeout_seconds=120,
            allowed_extensions={".log", ".txt"},
            max_file_size_mb=200,
            max_evidence_lines=500,
            max_level_evidence_lines=150,
            openai_api_key=None,
            gemini_api_key=None,
            grok_api_key=None,
            groq_api_key=None,
            llm_api_key=None,
            log_level="INFO",
        )
        config = resolve_provider_config(settings, provider="gemini")
        self.assertIsNone(config)

    def test_factory_wires_ollama_without_api_key(self):
        settings = Settings.model_construct(
            llm_provider="ollama",
            llm_model="gpt-4o-mini",
            llm_temperature=0.2,
            llm_timeout_seconds=120,
            allowed_extensions={".log", ".txt"},
            max_file_size_mb=200,
            max_evidence_lines=500,
            max_level_evidence_lines=150,
            openai_api_key=None,
            gemini_api_key=None,
            grok_api_key=None,
            groq_api_key=None,
            llm_api_key=None,
            log_level="INFO",
        )
        agent = build_log_analysis_agent(settings=settings, provider="ollama")

        self.assertIsNotNone(agent._llm_analyzer)
        assert agent._llm_analyzer is not None
        client = agent._llm_analyzer._llm_client
        self.assertEqual(client.provider, "ollama")


if __name__ == "__main__":
    unittest.main()
