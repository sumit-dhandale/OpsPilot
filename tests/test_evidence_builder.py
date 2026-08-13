"""Evidence builder tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from opspilot.config import Settings
from opspilot.evidence.builder import EvidenceBuilder
from opspilot.parsers.log_parser import LogParser


class EvidenceBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixture = Path(__file__).parent / "fixtures" / "sample_incident.log"
        cls.entries = LogParser().parse(fixture.read_text(encoding="utf-8"))

    def test_builds_factual_bundle(self) -> None:
        evidence = EvidenceBuilder(Settings()).build(self.entries)

        self.assertEqual(evidence.total_lines, 6)
        self.assertIsNotNone(evidence.time_range)
        self.assertEqual(evidence.statistics["total_lines"], 6)
        self.assertTrue(evidence.error_lines)
        self.assertTrue(evidence.lifecycle_lines)

    def test_bundle_has_no_analysis_conclusions(self) -> None:
        evidence = EvidenceBuilder(Settings()).build(self.entries)

        self.assertNotIn("executive_summary", evidence.statistics)
        self.assertNotIn("likely_root_cause", evidence.statistics)
        self.assertNotIn("recommendations", evidence.statistics)

    def test_empty_entries(self) -> None:
        evidence = EvidenceBuilder(Settings()).build([])

        self.assertEqual(evidence.total_lines, 0)
        self.assertEqual(evidence.sample_lines, [])
