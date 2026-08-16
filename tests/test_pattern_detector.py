"""Pattern detector tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from opspilot.detectors.pattern_detector import PatternDetector
from opspilot.parsers.log_parser import LogParser


class PatternDetectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixture = Path(__file__).parent / "fixtures" / "sample_incident.log"
        cls.incident_entries = LogParser().parse(fixture.read_text(encoding="utf-8"))
        cls.clean_entries = LogParser().parse("2024-01-01 10:00:00 INFO Healthy heartbeat\n")

    def test_detects_timeout_and_connection_patterns(self) -> None:
        patterns, _ = PatternDetector().detect(self.incident_entries)

        self.assertTrue(any("timeout" in pattern.lower() for pattern in patterns))
        self.assertTrue(any("connection" in pattern.lower() for pattern in patterns))

    def test_detects_shutdown_anomaly(self) -> None:
        _, anomalies = PatternDetector().detect(self.incident_entries)

        self.assertTrue(any("shutdown" in anomaly.lower() for anomaly in anomalies))

    def test_clean_log_has_no_connection_failure_anomaly(self) -> None:
        _, anomalies = PatternDetector().detect(self.clean_entries)

        self.assertFalse(any("connection" in anomaly.lower() for anomaly in anomalies))
