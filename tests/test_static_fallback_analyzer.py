"""Static fallback analyzer tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from opspilot.analyzers.static_fallback_analyzer import StaticFallbackAnalyzer
from opspilot.parsers.log_parser import LogParser


class StaticFallbackAnalyzerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixture = Path(__file__).parent / "fixtures" / "sample_incident.log"
        cls.entries = LogParser().parse(fixture.read_text(encoding="utf-8"))

    def test_produces_all_report_sections(self) -> None:
        report = StaticFallbackAnalyzer().analyze(self.entries)

        self.assertTrue(report.executive_summary)
        self.assertEqual(report.log_overview.total_lines_processed, 6)
        self.assertTrue(report.timeline)
        self.assertTrue(report.error_analysis)
        self.assertTrue(report.warning_analysis)
        self.assertTrue(report.recommendations)
        self.assertTrue(report.interesting_log_snippets)

    def test_root_cause_has_fact_buckets(self) -> None:
        report = StaticFallbackAnalyzer().analyze(self.entries)

        self.assertIsNotNone(report.likely_root_cause.observed_facts)
        self.assertIsNotNone(report.likely_root_cause.possible_causes)
        self.assertIsNotNone(report.likely_root_cause.assumptions)
