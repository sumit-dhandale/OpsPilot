"""Factory wiring tests."""

from __future__ import annotations

import unittest

from opspilot.config import Settings
from opspilot.factory import build_log_analysis_agent


class FactoryTests(unittest.TestCase):
    def test_disable_llm_skips_llm_analyzer(self) -> None:
        settings = Settings(openai_api_key="test-key")
        agent = build_log_analysis_agent(settings=settings, disable_llm=True)

        self.assertIsNone(agent._llm_analyzer)
        self.assertFalse(agent._should_use_llm())

    def test_with_api_key_wires_llm_analyzer(self) -> None:
        settings = Settings(openai_api_key="test-key")
        agent = build_log_analysis_agent(settings=settings, disable_llm=False)

        self.assertIsNotNone(agent._llm_analyzer)
        self.assertTrue(agent._should_use_llm())

    def test_without_api_key_uses_static_only(self) -> None:
        settings = Settings(openai_api_key=None)
        agent = build_log_analysis_agent(settings=settings, disable_llm=False)

        self.assertIsNone(agent._llm_analyzer)
        self.assertFalse(agent._should_use_llm())
