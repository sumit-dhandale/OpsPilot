import json
import tempfile
import unittest
from pathlib import Path

from opspilot.analyzers.llm_analyzer import LLMAnalyzer
from opspilot.analyzers.static_fallback_analyzer import StaticFallbackAnalyzer
from opspilot.domain.models import LogEvidenceBundle
from opspilot.evidence.builder import EvidenceBuilder
from opspilot.factory import build_log_analysis_agent
from opspilot.llm.client import LLMClient
from opspilot.parsers.log_parser import LogParser
from opspilot.config import Settings


class MockLLMClient(LLMClient):
    def generate(self, prompt: str) -> str:
        return json.dumps(
            {
                "executive_summary": "Application started, then degraded with warnings and a database timeout error.",
                "log_overview": {
                    "time_range": "2024-01-01T10:00:00 -> 2024-01-01T10:00:10",
                    "total_lines_processed": 3,
                    "log_levels_observed": ["INFO", "WARNING", "ERROR"],
                    "major_components": [],
                    "request_identifiers": [],
                    "thread_names": [],
                },
                "timeline": [
                    {
                        "timestamp": "2024-01-01T10:00:00",
                        "message": "Application started",
                        "source": "INFO",
                    },
                    {
                        "timestamp": "2024-01-01T10:00:10",
                        "message": "Database connection timeout",
                        "source": "ERROR",
                    },
                ],
                "error_analysis": [
                    {
                        "error_type": "Database connection timeout",
                        "occurrence_count": 1,
                        "first_occurrence": "2024-01-01T10:00:10",
                        "last_occurrence": "2024-01-01T10:00:10",
                        "short_explanation": "Database dependency failed to respond in time.",
                    }
                ],
                "warning_analysis": [
                    {
                        "warning_type": "Slow response observed",
                        "occurrence_count": 1,
                        "first_occurrence": "2024-01-01T10:00:05",
                        "last_occurrence": "2024-01-01T10:00:05",
                        "short_explanation": "Latency warning before the error.",
                    }
                ],
                "pattern_detection": ["Timeout-related messages were observed."],
                "anomalies": ["Warnings preceded error activity."],
                "likely_root_cause": {
                    "observed_facts": ["Database connection timeout logged after slow response warning."],
                    "possible_causes": ["Database connectivity or latency issue."],
                    "assumptions": [],
                },
                "recommendations": ["Inspect database connectivity and timeout settings."],
                "interesting_log_snippets": ["2024-01-01 10:00:10 ERROR Database connection timeout"],
            }
        )


class AnalysisServiceTests(unittest.TestCase):
    SAMPLE_LOG = (
        "2024-01-01 10:00:00 INFO Application started\n"
        "2024-01-01 10:00:05 WARN Slow response observed\n"
        "2024-01-01 10:00:10 ERROR Database connection timeout\n"
    )

    def _write_log(self, directory: str) -> str:
        log_file = Path(directory) / "sample.log"
        log_file.write_text(self.SAMPLE_LOG, encoding="utf-8")
        return str(log_file)

    def test_static_fallback_generates_full_report(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            agent = build_log_analysis_agent(disable_llm=True)
            report = agent.analyze_file(self._write_log(tmp_dir)).to_output_dict()

            self.assertEqual(report["analysis_source"], "static_fallback")
            self.assertTrue(report["executive_summary"])
            self.assertEqual(report["log_overview"]["total_lines_processed"], 3)
            self.assertTrue(report["timeline"])
            self.assertTrue(report["error_analysis"])
            self.assertIn("observed_facts", report["likely_root_cause"])
            self.assertTrue(report["recommendations"])
            self.assertTrue(report["interesting_log_snippets"])

    def test_llm_path_is_primary_when_client_available(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = Settings(openai_api_key="test-key")
            agent = build_log_analysis_agent(settings=settings, disable_llm=False)
            agent._llm_analyzer = LLMAnalyzer(llm_client=MockLLMClient())
            report = agent.analyze_file(self._write_log(tmp_dir)).to_output_dict()

            self.assertEqual(report["analysis_source"], "llm")
            self.assertIn("database timeout", report["executive_summary"].lower())

    def test_llm_failure_falls_back_to_static(self):
        class FailingLLMClient(LLMClient):
            def generate(self, prompt: str) -> str:
                from opspilot.exceptions import LLMError

                raise LLMError("LLM unavailable")

        with tempfile.TemporaryDirectory() as tmp_dir:
            settings = Settings(openai_api_key="test-key")
            agent = build_log_analysis_agent(settings=settings, disable_llm=False)
            agent._llm_analyzer = LLMAnalyzer(llm_client=FailingLLMClient())
            report = agent.analyze_file(self._write_log(tmp_dir)).to_output_dict()

            self.assertEqual(report["analysis_source"], "static_fallback")
            self.assertIn("llm_error", report)
            self.assertTrue(report["executive_summary"])

    def test_evidence_builder_does_not_include_conclusions(self):
        entries = LogParser().parse(self.SAMPLE_LOG)
        evidence = EvidenceBuilder(Settings()).build(entries)

        self.assertEqual(evidence.total_lines, 3)
        self.assertTrue(evidence.error_lines)
        self.assertTrue(evidence.lifecycle_lines)
        self.assertNotIn("executive_summary", evidence.statistics)

    def test_static_analyzer_is_separate_from_evidence_builder(self):
        entries = LogParser().parse(self.SAMPLE_LOG)
        evidence = EvidenceBuilder(Settings()).build(entries)
        static_report = StaticFallbackAnalyzer().analyze(entries)

        self.assertIsInstance(evidence, LogEvidenceBundle)
        self.assertTrue(static_report.executive_summary)
        self.assertNotEqual(static_report.executive_summary, evidence.time_range)
