from __future__ import annotations

from collections import Counter
from typing import Iterable

from opspilot.domain.models import LogEntry


class PatternDetector:
    """Detects simple recurring patterns and anomalies from log data."""

    def detect(self, entries: list[LogEntry]) -> tuple[list[str], list[str]]:
        patterns = self._detect_patterns(entries)
        anomalies = self._detect_anomalies(entries)
        return patterns, anomalies

    def _detect_patterns(self, entries: list[LogEntry]) -> list[str]:
        messages = [entry.message.lower() for entry in entries]
        patterns: list[str] = []

        if any("retry" in message for message in messages):
            patterns.append("Repeated retries detected.")
        if any("timeout" in message for message in messages):
            patterns.append("Timeout loop signatures were found.")
        if any("connection" in message for message in messages):
            patterns.append("Connection-related issues appear in the logs.")
        if any("thread pool" in message or "pool exhausted" in message for message in messages):
            patterns.append("Thread-pool exhaustion may be a factor.")
        if any("gc" in message or "garbage" in message for message in messages):
            patterns.append("Garbage collection activity was observed.")
        if any("memory" in message for message in messages):
            patterns.append("Memory pressure indicators are present.")

        return patterns

    def _detect_anomalies(self, entries: list[LogEntry]) -> list[str]:
        anomalies: list[str] = []
        messages = [entry.message.lower() for entry in entries]

        if any("unexpected shutdown" in message or "shutdown" in message for message in messages):
            anomalies.append("Unexpected shutdown or termination was observed.")
        if any("connection refused" in message or "connection reset" in message for message in messages):
            anomalies.append("Connection failures were seen in the execution flow.")
        if any("exception" in message for message in messages):
            anomalies.append("Recurring exception patterns may indicate systemic instability.")

        return anomalies
