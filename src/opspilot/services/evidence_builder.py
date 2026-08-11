from __future__ import annotations

from opspilot.config import DEFAULT_SETTINGS
from opspilot.domain.models import LogEntry, LogEvidenceBundle
from opspilot.stats.statistics_generator import StatisticsGenerator


class EvidenceBuilder:
    """Builds factual evidence for LLM input without producing analysis conclusions."""

    LIFECYCLE_KEYWORDS = (
        "start",
        "started",
        "shutdown",
        "stop",
        "connect",
        "connected",
        "ready",
        "listen",
        "deploy",
        "config",
        "initialized",
        "bootstrap",
    )

    def __init__(
        self,
        statistics_generator: StatisticsGenerator | None = None,
        max_sample_lines: int | None = None,
        max_level_lines: int | None = None,
    ) -> None:
        self.statistics_generator = statistics_generator or StatisticsGenerator()
        self.max_sample_lines = max_sample_lines or DEFAULT_SETTINGS.max_evidence_lines
        self.max_level_lines = max_level_lines or DEFAULT_SETTINGS.max_level_evidence_lines

    def build(self, entries: list[LogEntry]) -> LogEvidenceBundle:
        statistics = self.statistics_generator.generate(entries)
        timestamps = [entry.timestamp for entry in entries if entry.timestamp is not None]
        time_range = None
        if timestamps:
            time_range = f"{min(timestamps).isoformat()} -> {max(timestamps).isoformat()}"

        error_lines = self._collect_level_lines(entries, {"ERROR", "CRITICAL", "FATAL"})
        warning_lines = self._collect_level_lines(entries, {"WARNING"})
        lifecycle_lines = self._collect_lifecycle_lines(entries)
        sample_lines = self._collect_sample_lines(entries, error_lines, warning_lines, lifecycle_lines)

        return LogEvidenceBundle(
            total_lines=len(entries),
            time_range=time_range,
            statistics=statistics,
            sample_lines=sample_lines,
            error_lines=error_lines,
            warning_lines=warning_lines,
            lifecycle_lines=lifecycle_lines,
        )

    def _format_line(self, entry: LogEntry) -> str:
        timestamp = entry.timestamp.isoformat() if entry.timestamp else "unknown"
        level = entry.level or "UNKNOWN"
        return f"[{timestamp}] {level} {entry.raw}"

    def _collect_level_lines(self, entries: list[LogEntry], levels: set[str]) -> list[str]:
        lines = [self._format_line(entry) for entry in entries if entry.level in levels]
        return lines[:self.max_level_lines]

    def _collect_lifecycle_lines(self, entries: list[LogEntry]) -> list[str]:
        lifecycle: list[str] = []
        for entry in entries:
            message = entry.message.lower()
            if any(keyword in message for keyword in self.LIFECYCLE_KEYWORDS):
                lifecycle.append(self._format_line(entry))
        return lifecycle[:self.max_level_lines]

    def _collect_sample_lines(
        self,
        entries: list[LogEntry],
        error_lines: list[str],
        warning_lines: list[str],
        lifecycle_lines: list[str],
    ) -> list[str]:
        if not entries:
            return []

        prioritized = set(error_lines + warning_lines + lifecycle_lines)
        samples: list[str] = list(prioritized)

        head = [self._format_line(entry) for entry in entries[:50]]
        tail = [self._format_line(entry) for entry in entries[-50:]]
        for line in head + tail:
            if line not in prioritized:
                samples.append(line)

        return samples[:self.max_sample_lines]
