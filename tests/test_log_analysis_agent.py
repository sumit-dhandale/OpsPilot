"""Log analysis agent orchestration tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from opspilot.analyzers.llm_analyzer import LLMAnalyzer
from opspilot.config import Settings
from opspilot.exceptions import LLMError
from opspilot.factory import build_log_analysis_agent
from opspilot.llm.client import LLMClient


class MockLLMClient(LLMClient):
    def generate(self, prompt: str) -> str:
        return json.dumps(
            {
                "executive_summary": "Incident involved database timeout after slow responses.",
                "log_overview": {
                    "time_range": "2024-01-01T10:00:00 -> 2024-01-01T10:00:15",
                    "total_lines_processed": 6,
                    "log_levels_observed": ["INFO", "WARNING", "ERROR"],
                    "major_components": [],
                    "request_identifiers": [],
                    "thread_names": [],
                },
                "timeline": [],
                "error_analysis": [],
                "warning_analysis": [],
                "pattern_detection": [],
                "anomalies": [],
                "likely_root_cause": {
                    "observed_facts": [],
                    "possible_causes": [],
                    "assumptions": [],
                },
                "recommendations": [],
                "interesting_log_snippets": [],
            }
        )


class LogAnalysisAgentTests(unittest.TestCase):
    def test_analyze_fixture_with_static_fallback(self) -> None:
        fixture = Path(__file__).parent / "fixtures" / "sample_incident.log"
        agent = build_log_analysis_agent(disable_llm=True)
        result = agent.analyze_file(fixture)

        self.assertEqual(result.analysis_source, "static_fallback")
        self.assertTrue(result.report.executive_summary)
        self.assertEqual(result.report.log_overview.total_lines_processed, 6)

    def test_llm_path_when_mock_client_injected(self) -> None:
        fixture = Path(__file__).parent / "fixtures" / "sample_incident.log"
        agent = build_log_analysis_agent(settings=Settings(openai_api_key="test-key"))
        agent._llm_analyzer = LLMAnalyzer(llm_client=MockLLMClient())
        result = agent.analyze_file(fixture)

        self.assertEqual(result.analysis_source, "llm")
        self.assertIn("timeout", result.report.executive_summary.lower())

    def test_llm_failure_falls_back_to_static(self) -> None:
        class FailingLLMClient(LLMClient):
            def generate(self, prompt: str) -> str:
                raise LLMError("LLM unavailable")

        fixture = Path(__file__).parent / "fixtures" / "sample_incident.log"
        agent = build_log_analysis_agent(settings=Settings(openai_api_key="test-key"))
        agent._llm_analyzer = LLMAnalyzer(llm_client=FailingLLMClient())
        result = agent.analyze_file(fixture)

        self.assertEqual(result.analysis_source, "static_fallback")
        self.assertIsNotNone(result.llm_error)

    def test_analyze_file_from_temp_path(self) -> None:
        fixture = Path(__file__).parent / "fixtures" / "sample_incident.log"
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "copy.log"
            log_path.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")
            agent = build_log_analysis_agent(disable_llm=True)
            result = agent.analyze_file(log_path)

            self.assertEqual(result.report.log_overview.total_lines_processed, 6)
