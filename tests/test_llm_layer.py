"""LLM prompt and report parsing tests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from opspilot.config import Settings
from opspilot.evidence.builder import EvidenceBuilder
from opspilot.exceptions import ReportValidationError
from opspilot.llm.prompt_builder import PromptBuilder
from opspilot.llm.report_parser import ReportParser
from opspilot.parsers.log_parser import LogParser


class LLMLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixture = Path(__file__).parent / "fixtures" / "sample_incident.log"
        cls.entries = LogParser().parse(fixture.read_text(encoding="utf-8"))
        cls.evidence = EvidenceBuilder(Settings()).build(cls.entries)

    def test_prompt_includes_schema_and_evidence(self) -> None:
        prompt = PromptBuilder().build_analysis_prompt(self.evidence)

        self.assertIn("executive_summary", prompt)
        self.assertIn("do not invent", prompt.lower())
        self.assertIn("Database connection timeout", prompt)

    def test_report_parser_validates_minimal_report(self) -> None:
        payload = {
            "executive_summary": "Test summary.",
            "log_overview": {
                "time_range": None,
                "total_lines_processed": 1,
                "log_levels_observed": ["INFO"],
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

        report = ReportParser().parse(payload)
        self.assertEqual(report.executive_summary, "Test summary.")

    def test_report_parser_rejects_invalid_report(self) -> None:
        with self.assertRaises(ReportValidationError):
            ReportParser().parse({"executive_summary": "missing sections"})
