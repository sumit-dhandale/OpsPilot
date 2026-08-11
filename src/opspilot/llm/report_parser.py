from __future__ import annotations

from typing import Any

from opspilot.domain.models import (
    AnalysisOverview,
    ErrorGroup,
    StructuredReport,
    TimelineEvent,
    WarningGroup,
)


class ReportParser:
    """Parses LLM JSON output into a StructuredReport."""

    def parse(self, data: dict[str, Any]) -> StructuredReport:
        overview_data = data.get("log_overview", {})
        overview = AnalysisOverview(
            time_range=overview_data.get("time_range"),
            total_lines_processed=int(overview_data.get("total_lines_processed", 0)),
            log_levels_observed=list(overview_data.get("log_levels_observed", [])),
            major_components=list(overview_data.get("major_components", [])),
            request_identifiers=list(overview_data.get("request_identifiers", [])),
            thread_names=list(overview_data.get("thread_names", [])),
        )

        timeline = [
            TimelineEvent(
                timestamp=item.get("timestamp"),
                message=str(item.get("message", "")),
                source=item.get("source"),
            )
            for item in data.get("timeline", [])
            if isinstance(item, dict)
        ]

        error_analysis = [
            ErrorGroup(
                error_type=str(item.get("error_type", "unknown_error")),
                occurrence_count=int(item.get("occurrence_count", 0)),
                first_occurrence=item.get("first_occurrence"),
                last_occurrence=item.get("last_occurrence"),
                short_explanation=str(item.get("short_explanation", "")),
            )
            for item in data.get("error_analysis", [])
            if isinstance(item, dict)
        ]

        warning_analysis = [
            WarningGroup(
                warning_type=str(item.get("warning_type", "unknown_warning")),
                occurrence_count=int(item.get("occurrence_count", 0)),
                first_occurrence=item.get("first_occurrence"),
                last_occurrence=item.get("last_occurrence"),
                short_explanation=str(item.get("short_explanation", "")),
            )
            for item in data.get("warning_analysis", [])
            if isinstance(item, dict)
        ]

        root_cause = data.get("likely_root_cause", {})
        if not isinstance(root_cause, dict):
            root_cause = {}

        return StructuredReport(
            executive_summary=str(data.get("executive_summary", "")),
            log_overview=overview,
            timeline=timeline,
            error_analysis=error_analysis,
            warning_analysis=warning_analysis,
            pattern_detection=[str(item) for item in data.get("pattern_detection", [])],
            anomalies=[str(item) for item in data.get("anomalies", [])],
            likely_root_cause={
                "observed_facts": list(root_cause.get("observed_facts", [])),
                "possible_causes": list(root_cause.get("possible_causes", [])),
                "assumptions": list(root_cause.get("assumptions", [])),
            },
            recommendations=[str(item) for item in data.get("recommendations", [])],
            interesting_log_snippets=[str(item) for item in data.get("interesting_log_snippets", [])],
        )
