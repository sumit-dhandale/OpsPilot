from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class LogEntry:
    """Single parsed log line."""

    raw: str
    line_number: int
    timestamp: datetime | None = None
    level: str | None = None
    logger: str | None = None
    message: str = ""
    thread_name: str | None = None
    component: str | None = None
    request_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ErrorGroup:
    """Grouped repeated error pattern."""

    error_type: str
    occurrence_count: int
    first_occurrence: str | None = None
    last_occurrence: str | None = None
    short_explanation: str = ""


@dataclass(slots=True)
class WarningGroup:
    """Grouped repeated warning pattern."""

    warning_type: str
    occurrence_count: int
    first_occurrence: str | None = None
    last_occurrence: str | None = None
    short_explanation: str = ""


@dataclass(slots=True)
class TimelineEvent:
    """Key event in a sequence."""

    timestamp: str | None
    message: str
    source: str | None = None


@dataclass(slots=True)
class AnalysisOverview:
    """Summary of the log file."""

    time_range: str | None = None
    total_lines_processed: int = 0
    log_levels_observed: list[str] = field(default_factory=list)
    major_components: list[str] = field(default_factory=list)
    request_identifiers: list[str] = field(default_factory=list)
    thread_names: list[str] = field(default_factory=list)


@dataclass(slots=True)
class StructuredReport:
    """Final output contract for the log analysis report."""

    executive_summary: str
    log_overview: AnalysisOverview
    timeline: list[TimelineEvent]
    error_analysis: list[ErrorGroup]
    warning_analysis: list[WarningGroup]
    pattern_detection: list[str]
    anomalies: list[str]
    likely_root_cause: dict[str, list[str]]
    recommendations: list[str]
    interesting_log_snippets: list[str]
