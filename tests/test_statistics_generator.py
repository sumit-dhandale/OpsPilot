"""Statistics generator tests — Milestone 1.4."""

from __future__ import annotations

import unittest
from pathlib import Path

from opspilot.domain.models import LogEntry
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
        self.assertEqual(stats["components"], {})
        self.assertEqual(stats["request_ids"], {})
        self.assertEqual(stats["thread_names"], {})

    def test_counts_components(self) -> None:
        entries = [
            LogEntry(raw="a", line_number=1, component="Api", level="INFO", message="a"),
            LogEntry(raw="b", line_number=2, component="Api", level="INFO", message="b"),
            LogEntry(raw="c", line_number=3, component="Db", level="ERROR", message="c"),
        ]
        stats = StatisticsGenerator().generate(entries)

        self.assertEqual(stats["components"]["Api"], 2)
        self.assertEqual(stats["components"]["Db"], 1)

    def test_counts_request_ids(self) -> None:
        entries = [
            LogEntry(raw="a", line_number=1, request_id="req-1", level="INFO", message="a"),
            LogEntry(raw="b", line_number=2, request_id="req-1", level="INFO", message="b"),
            LogEntry(raw="c", line_number=3, request_id="req-2", level="INFO", message="c"),
        ]
        stats = StatisticsGenerator().generate(entries)

        self.assertEqual(stats["request_ids"]["req-1"], 2)
        self.assertEqual(stats["request_ids"]["req-2"], 1)

    def test_counts_thread_names(self) -> None:
        entries = [
            LogEntry(raw="a", line_number=1, thread_name="main", level="INFO", message="a"),
            LogEntry(raw="b", line_number=2, thread_name="worker", level="INFO", message="b"),
            LogEntry(raw="c", line_number=3, thread_name="worker", level="INFO", message="c"),
        ]
        stats = StatisticsGenerator().generate(entries)

        self.assertEqual(stats["thread_names"]["worker"], 2)
        self.assertEqual(stats["thread_names"]["main"], 1)

    def test_limits_top_components_to_ten(self) -> None:
        entries = [
            LogEntry(raw=f"l{i}", line_number=i, component=f"C{i}", level="INFO", message="x")
            for i in range(1, 15)
        ]
        stats = StatisticsGenerator().generate(entries)

        self.assertEqual(len(stats["components"]), 10)
