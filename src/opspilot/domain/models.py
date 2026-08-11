"""Domain models and report schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class LogEntry(BaseModel):
    """Single parsed log line."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    raw: str
    line_number: int
    timestamp: datetime | None = None
    level: str | None = None
    logger: str | None = None
    message: str = ""
    thread_name: str | None = None
    component: str | None = None
    request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ErrorGroup(BaseModel):
    error_type: str
    occurrence_count: int
    first_occurrence: str | None = None
    last_occurrence: str | None = None
    short_explanation: str = ""


class WarningGroup(BaseModel):
    warning_type: str
    occurrence_count: int
    first_occurrence: str | None = None
    last_occurrence: str | None = None
    short_explanation: str = ""


class TimelineEvent(BaseModel):
    timestamp: str | None = None
    message: str
    source: str | None = None


class AnalysisOverview(BaseModel):
    time_range: str | None = None
    total_lines_processed: int = 0
    log_levels_observed: list[str] = Field(default_factory=list)
    major_components: list[str] = Field(default_factory=list)
    request_identifiers: list[str] = Field(default_factory=list)
    thread_names: list[str] = Field(default_factory=list)


class LikelyRootCause(BaseModel):
    observed_facts: list[str] = Field(default_factory=list)
    possible_causes: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class StructuredReport(BaseModel):
    """Final output contract for log analysis."""

    executive_summary: str
    log_overview: AnalysisOverview
    timeline: list[TimelineEvent] = Field(default_factory=list)
    error_analysis: list[ErrorGroup] = Field(default_factory=list)
    warning_analysis: list[WarningGroup] = Field(default_factory=list)
    pattern_detection: list[str] = Field(default_factory=list)
    anomalies: list[str] = Field(default_factory=list)
    likely_root_cause: LikelyRootCause = Field(default_factory=LikelyRootCause)
    recommendations: list[str] = Field(default_factory=list)
    interesting_log_snippets: list[str] = Field(default_factory=list)


class LogEvidenceBundle(BaseModel):
    """Factual evidence prepared for LLM analysis."""

    total_lines: int
    time_range: str | None = None
    statistics: dict[str, Any] = Field(default_factory=dict)
    sample_lines: list[str] = Field(default_factory=list)
    error_lines: list[str] = Field(default_factory=list)
    warning_lines: list[str] = Field(default_factory=list)
    lifecycle_lines: list[str] = Field(default_factory=list)


AnalysisSource = Literal["llm", "static_fallback"]


class AnalysisResult(BaseModel):
    """Analysis output with explicit source attribution."""

    report: StructuredReport
    analysis_source: AnalysisSource
    llm_error: str | None = None

    def to_output_dict(self) -> dict[str, Any]:
        payload = self.report.model_dump()
        payload["analysis_source"] = self.analysis_source
        if self.llm_error:
            payload["llm_error"] = self.llm_error
        return payload
