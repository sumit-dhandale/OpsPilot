import unittest
from pathlib import Path

from opspilot.parsers.log_parser import LogParser


class LogParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixture = Path(__file__).parent / "fixtures" / "sample_incident.log"
        cls.fixture_entries = LogParser().parse(fixture.read_text(encoding="utf-8"))

    def test_parse_common_log_line(self) -> None:
        content = "2024-01-01 10:00:00,123 INFO Application started\n"
        entries = LogParser().parse(content)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].level, "INFO")
        self.assertIn("Application started", entries[0].message)
        self.assertIsNotNone(entries[0].timestamp)

    def test_parse_error_message(self) -> None:
        content = "2024-01-01 10:05:30 ERROR Database connection timeout\n"
        entries = LogParser().parse(content)

        self.assertEqual(entries[0].level, "ERROR")
        self.assertIn("Database connection timeout", entries[0].message)

    def test_parse_fixture_incident_log(self) -> None:
        self.assertEqual(len(self.fixture_entries), 6)
        levels = {entry.level for entry in self.fixture_entries}
        self.assertIn("INFO", levels)
        self.assertIn("WARNING", levels)
        self.assertIn("ERROR", levels)
