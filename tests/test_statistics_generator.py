"""Statistics generator tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from opspilot.parsers.log_parser import LogParser
from opspilot.stats.statistics_generator import StatisticsGenerator


class StatisticsGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixture = Path(__file__).parent / "fixtures" / "sample_incident.log"
        cls.entries = LogParser().parse(fixture.read_text(encoding="utf-8"))

    def test_generate_counts_levels(self) -> None:
        stats = StatisticsGenerator().generate(self.entries)

        self.assertEqual(stats["total_lines"], 6)
        self.assertEqual(stats["levels"]["INFO"], 3)
        self.assertEqual(stats["levels"]["WARNING"], 1)
        self.assertEqual(stats["levels"]["ERROR"], 2)

    def test_empty_entries(self) -> None:
        stats = StatisticsGenerator().generate([])

        self.assertEqual(stats["total_lines"], 0)
        self.assertEqual(stats["levels"], {})
