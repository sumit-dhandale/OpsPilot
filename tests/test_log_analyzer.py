"""Log analyzer tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from opspilot.analyzers.log_analyzer import LogAnalyzer
from opspilot.parsers.log_parser import LogParser


class LogAnalyzerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixture = Path(__file__).parent / "fixtures" / "sample_incident.log"
        cls.entries = LogParser().parse(fixture.read_text(encoding="utf-8"))

    def test_overview_counts_and_levels(self) -> None:
        findings = LogAnalyzer().analyze(self.entries)
        overview = findings["overview"]

        self.assertEqual(overview.total_lines_processed, 6)
        self.assertIn("INFO", overview.log_levels_observed)
        self.assertIn("WARNING", overview.log_levels_observed)
        self.assertIn("ERROR", overview.log_levels_observed)
        self.assertIsNotNone(overview.time_range)

    def test_error_groups_merge_duplicates(self) -> None:
        findings = LogAnalyzer().analyze(self.entries)
        error_groups = findings["error_analysis"]

        self.assertEqual(len(error_groups), 1)
        self.assertEqual(error_groups[0].occurrence_count, 2)
        self.assertIsNotNone(error_groups[0].first_occurrence)
        self.assertIsNotNone(error_groups[0].last_occurrence)

    def test_warning_groups(self) -> None:
        findings = LogAnalyzer().analyze(self.entries)
        warning_groups = findings["warning_analysis"]

        self.assertEqual(len(warning_groups), 1)
        self.assertEqual(warning_groups[0].occurrence_count, 1)

    def test_timeline_includes_errors_and_warnings(self) -> None:
        findings = LogAnalyzer().analyze(self.entries)
        timeline = findings["timeline"]

        sources = {event.source for event in timeline}
        self.assertIn("ERROR", sources)
        self.assertIn("WARNING", sources)

    def test_empty_entries(self) -> None:
        findings = LogAnalyzer().analyze([])

        self.assertEqual(findings["overview"].total_lines_processed, 0)
        self.assertEqual(findings["error_analysis"], [])
