"""Log parser tests."""

from __future__ import annotations

import unittest
from datetime import datetime
from pathlib import Path

from opspilot.parsers.log_parser import LogParser


class LogParserFixtureTests(unittest.TestCase):
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

    def test_skips_blank_lines(self) -> None:
        content = "2024-01-01 10:00:00 INFO first\n\n2024-01-01 10:00:01 INFO second\n"
        entries = LogParser().parse(content)
        self.assertEqual(len(entries), 2)


class LogParserTimestampTests(unittest.TestCase):
    """Milestone 1.2 — timestamp formats."""

    def _parse_single(self, line: str) -> datetime | None:
        return LogParser().parse(line)[0].timestamp

    def test_iso_with_t_separator(self) -> None:
        ts = self._parse_single("2024-01-01T10:00:00 INFO started")
        self.assertEqual(ts, datetime(2024, 1, 1, 10, 0, 0))

    def test_iso_with_z_suffix(self) -> None:
        ts = self._parse_single("2024-01-01T10:00:00Z INFO started")
        self.assertEqual(ts, datetime(2024, 1, 1, 10, 0, 0))

    def test_iso_with_milliseconds_dot(self) -> None:
        ts = self._parse_single("2024-01-01T10:00:00.456 INFO started")
        self.assertEqual(ts, datetime(2024, 1, 1, 10, 0, 0, 456000))

    def test_iso_with_milliseconds_comma(self) -> None:
        ts = self._parse_single("2024-01-01 10:00:00,789 INFO started")
        self.assertEqual(ts, datetime(2024, 1, 1, 10, 0, 0, 789000))

    def test_slash_date_format(self) -> None:
        ts = self._parse_single("2024/01/01 10:00:00 INFO started")
        self.assertEqual(ts, datetime(2024, 1, 1, 10, 0, 0))

    def test_slash_date_with_milliseconds(self) -> None:
        ts = self._parse_single("2024/01/01 10:00:00,123 INFO started")
        self.assertEqual(ts, datetime(2024, 1, 1, 10, 0, 0, 123000))

    def test_day_first_date_format(self) -> None:
        ts = self._parse_single("01-01-2024 10:00:00 INFO started")
        self.assertEqual(ts, datetime(2024, 1, 1, 10, 0, 0))

    def test_timezone_offset_is_stripped_for_parsing(self) -> None:
        ts = self._parse_single("2024-01-01T10:00:00+05:30 INFO started")
        self.assertEqual(ts, datetime(2024, 1, 1, 10, 0, 0))


class LogParserMetadataTests(unittest.TestCase):
    """Milestone 1.3 — levels and metadata."""

    def test_warn_maps_to_warning(self) -> None:
        entry = LogParser().parse("2024-01-01 10:00:00 WARN Slow response")[0]
        self.assertEqual(entry.level, "WARNING")

    def test_bracketed_logger(self) -> None:
        entry = LogParser().parse("2024-01-01 10:00:00 INFO [com.example.App] started")[0]
        self.assertEqual(entry.logger, "com.example.App")
        self.assertIn("started", entry.message)

    def test_request_id_extraction(self) -> None:
        entry = LogParser().parse("2024-01-01 10:00:00 INFO request_id=abc-123 done")[0]
        self.assertEqual(entry.request_id, "abc-123")

    def test_trace_id_extraction(self) -> None:
        entry = LogParser().parse("2024-01-01 10:00:00 INFO trace_id=trace-99 done")[0]
        self.assertEqual(entry.request_id, "trace-99")

    def test_session_id_extraction(self) -> None:
        entry = LogParser().parse("2024-01-01 10:00:00 INFO session_id=sess-42 done")[0]
        self.assertEqual(entry.request_id, "sess-42")

    def test_uuid_request_identifier(self) -> None:
        entry = LogParser().parse(
            "2024-01-01 10:00:00 INFO 550e8400-e29b-41d4-a716-446655440000 complete"
        )[0]
        self.assertEqual(entry.request_id, "550e8400-e29b-41d4-a716-446655440000")

    def test_thread_name_from_keyword(self) -> None:
        entry = LogParser().parse("2024-01-01 10:00:00 INFO thread=worker-1 busy")[0]
        self.assertEqual(entry.thread_name, "worker-1")

    def test_thread_name_from_bracket(self) -> None:
        entry = LogParser().parse("2024-01-01 10:00:00 INFO [Thread-5] busy")[0]
        self.assertEqual(entry.thread_name, "Thread-5")

    def test_component_extraction(self) -> None:
        entry = LogParser().parse("2024-01-01 10:00:00 INFO Service=PaymentGateway ready")[0]
        self.assertEqual(entry.component, "PaymentGateway")

    def test_trace_level_supported(self) -> None:
        entry = LogParser().parse("2024-01-01 10:00:00 TRACE detailed step")[0]
        self.assertEqual(entry.level, "TRACE")
