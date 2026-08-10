from __future__ import annotations

from collections import Counter
from datetime import datetime

from opspilot.domain.models import AnalysisOverview, ErrorGroup, LogEntry, TimelineEvent, WarningGroup


class LogAnalyzer:
    """Builds structured findings from parsed log entries."""

    def analyze(self, entries: list[LogEntry]) -> dict[str, object]:
        if not entries:
            return {
                "overview": AnalysisOverview(),
                "timeline": [],
                "error_analysis": [],
                "warning_analysis": [],
                "pattern_detection": [],
                "anomalies": [],
            }

        overview = self._build_overview(entries)
        timeline = self._build_timeline(entries)
        error_analysis = self._build_error_groups(entries)
        warning_analysis = self._build_warning_groups(entries)
        pattern_detection = self._detect_patterns(entries)
        anomalies = self._detect_anomalies(entries)

        return {
            "overview": overview,
            "timeline": timeline,
            "error_analysis": error_analysis,
            "warning_analysis": warning_analysis,
            "pattern_detection": pattern_detection,
            "anomalies": anomalies,
        }

    def _build_overview(self, entries: list[LogEntry]) -> AnalysisOverview:
        timestamps = [entry.timestamp for entry in entries if entry.timestamp is not None]
        levels = sorted({entry.level for entry in entries if entry.level})

        overview = AnalysisOverview(
            time_range=self._build_time_range(timestamps),
            total_lines_processed=len(entries),
            log_levels_observed=levels,
            major_components=self._major_components(entries),
            request_identifiers=self._unique_request_ids(entries),
            thread_names=self._unique_thread_names(entries),
        )
        return overview

    def _build_time_range(self, timestamps: list[datetime]) -> str | None:
        if not timestamps:
            return None
        start = min(timestamps)
        end = max(timestamps)
        return f"{start.isoformat()} -> {end.isoformat()}"

    def _major_components(self, entries: list[LogEntry]) -> list[str]:
        components = [entry.component for entry in entries if entry.component]
        return sorted(set(components))[:10]

    def _unique_request_ids(self, entries: list[LogEntry]) -> list[str]:
        request_ids = [entry.request_id for entry in entries if entry.request_id]
        return sorted(set(request_ids))[:10]

    def _unique_thread_names(self, entries: list[LogEntry]) -> list[str]:
        thread_names = [entry.thread_name for entry in entries if entry.thread_name]
        return sorted(set(thread_names))[:10]

    def _build_timeline(self, entries: list[LogEntry], limit: int = 12) -> list[TimelineEvent]:
        events: list[TimelineEvent] = []
        for entry in entries:
            if entry.level in {"ERROR", "WARNING", "CRITICAL", "FATAL"}:
                events.append(
                    TimelineEvent(
                        timestamp=entry.timestamp.isoformat() if entry.timestamp else None,
                        message=entry.message[:200],
                        source=entry.level,
                    )
                )
        if not events:
            for entry in entries[:limit]:
                events.append(
                    TimelineEvent(
                        timestamp=entry.timestamp.isoformat() if entry.timestamp else None,
                        message=entry.message[:200],
                        source=entry.level,
                    )
                )
        return events[:limit]

    def _build_error_groups(self, entries: list[LogEntry]) -> list[ErrorGroup]:
        groups: dict[str, list[LogEntry]] = {}
        for entry in entries:
            if entry.level == "ERROR":
                key = entry.message or "unknown_error"
                groups.setdefault(key, []).append(entry)

        result: list[ErrorGroup] = []
        for key, grouped in groups.items():
            timestamps = [e.timestamp for e in grouped if e.timestamp]
            result.append(
                ErrorGroup(
                    error_type=key[:120],
                    occurrence_count=len(grouped),
                    first_occurrence=min(timestamps).isoformat() if timestamps else None,
                    last_occurrence=max(timestamps).isoformat() if timestamps else None,
                    short_explanation="Repeated error condition observed in logs.",
                )
            )
        return sorted(result, key=lambda item: item.occurrence_count, reverse=True)

    def _build_warning_groups(self, entries: list[LogEntry]) -> list[WarningGroup]:
        groups: dict[str, list[LogEntry]] = {}
        for entry in entries:
            if entry.level == "WARNING":
                key = entry.message or "unknown_warning"
                groups.setdefault(key, []).append(entry)

        result: list[WarningGroup] = []
        for key, grouped in groups.items():
            timestamps = [e.timestamp for e in grouped if e.timestamp]
            result.append(
                WarningGroup(
                    warning_type=key[:120],
                    occurrence_count=len(grouped),
                    first_occurrence=min(timestamps).isoformat() if timestamps else None,
                    last_occurrence=max(timestamps).isoformat() if timestamps else None,
                    short_explanation="Repeated warning condition observed in logs.",
                )
            )
        return sorted(result, key=lambda item: item.occurrence_count, reverse=True)

    def _detect_patterns(self, entries: list[LogEntry]) -> list[str]:
        patterns: list[str] = []
        error_count = sum(1 for entry in entries if entry.level == "ERROR")
        warning_count = sum(1 for entry in entries if entry.level == "WARNING")

        if error_count:
            patterns.append(f"{error_count} error events detected.")
        if warning_count:
            patterns.append(f"{warning_count} warning events detected.")
        if any(entry.message.lower().find("timeout") >= 0 for entry in entries):
            patterns.append("Timeout-related messages were observed.")
        if any(entry.message.lower().find("retry") >= 0 for entry in entries):
            patterns.append("Retry activity appears in the logs.")
        return patterns[:8]

    def _detect_anomalies(self, entries: list[LogEntry]) -> list[str]:
        anomalies: list[str] = []
        levels = Counter(entry.level for entry in entries if entry.level)
        if levels.get("ERROR", 0) and levels.get("WARNING", 0):
            anomalies.append("Warnings preceded or accompanied error activity.")
        if any(entry.message.lower().find("shutdown") >= 0 for entry in entries):
            anomalies.append("Shutdown-related events were detected.")
        if not entries:
            anomalies.append("No entries were available for analysis.")
        return anomalies[:8]
