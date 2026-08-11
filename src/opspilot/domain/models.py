from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from typing import Any, Literal


@dataclass
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


@dataclass
class ErrorGroup:
    """Grouped repeated error pattern."""

    error_type: str
    occurrence_count: int
    first_occurrence: str | None = None
    last_occurrence: str | None = None
    short_explanation: str = ""


@dataclass
class WarningGroup:
    """Grouped repeated warning pattern."""

    warning_type: str
    occurrence_count: int
    first_occurrence: str | None = None
    last_occurrence: str | None = None
    short_explanation: str = ""


@dataclass
class TimelineEvent:
    """Key event in a sequence."""

    timestamp: str | None
    message: str
    source: str | None = None


@dataclass
class AnalysisOverview:
    """Summary of the log file."""

    time_range: str | None = None
    total_lines_processed: int = 0
    log_levels_observed: list[str] = field(default_factory=list)
    major_components: list[str] = field(default_factory=list)
    request_identifiers: list[str] = field(default_factory=list)
    thread_names: list[str] = field(default_factory=list)


@dataclass
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


@dataclass
class LogEvidenceBundle:
    """Compact, factual evidence prepared for LLM analysis (not conclusions)."""

    total_lines: int
    time_range: str | None
    statistics: dict[str, Any]
    sample_lines: list[str]
    error_lines: list[str]
    warning_lines: list[str]
    lifecycle_lines: list[str]


AnalysisSource = Literal["llm", "static_fallback"]


@dataclass
class AnalysisResult:
    """Analysis output with explicit source attribution."""

    report: StructuredReport
    analysis_source: AnalysisSource
    llm_error: str | None = None


def to_serializable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_serializable(item) for key, item in asdict(value).items()}
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [to_serializable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_serializable(item) for key, item in value.items()}
    return value


def analysis_result_to_dict(result: AnalysisResult) -> dict[str, Any]:
    payload = to_serializable(result.report)
    payload["analysis_source"] = result.analysis_source
    if result.llm_error:
        payload["llm_error"] = result.llm_error
    return payload
