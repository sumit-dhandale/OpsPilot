from __future__ import annotations

from collections import Counter

from opspilot.domain.models import LogEntry


class StatisticsGenerator:
    """Generates summary-level statistics for log analysis."""

    def generate(self, entries: list[LogEntry]) -> dict[str, object]:
        total = len(entries)
        levels = Counter(entry.level for entry in entries if entry.level)
        components = Counter(entry.component for entry in entries if entry.component)
        request_ids = Counter(entry.request_id for entry in entries if entry.request_id)
        thread_names = Counter(entry.thread_name for entry in entries if entry.thread_name)

        return {
            "total_lines": total,
            "levels": dict(levels),
            "components": dict(components.most_common(10)),
            "request_ids": dict(request_ids.most_common(10)),
            "thread_names": dict(thread_names.most_common(10)),
        }
