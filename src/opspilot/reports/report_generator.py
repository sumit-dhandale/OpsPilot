from __future__ import annotations

from opspilot.domain.models import AnalysisOverview, LikelyRootCause, StructuredReport


class ReportGenerator:
    """Builds the final report object from analyzer output."""

    def generate(
        self,
        executive_summary: str,
        overview: AnalysisOverview,
        timeline: list,
        error_analysis: list,
        warning_analysis: list,
        pattern_detection: list[str],
        anomalies: list[str],
        likely_root_cause: LikelyRootCause,
        recommendations: list[str],
        interesting_log_snippets: list[str],
    ) -> StructuredReport:
        return StructuredReport(
            executive_summary=executive_summary,
            log_overview=overview,
            timeline=timeline,
            error_analysis=error_analysis,
            warning_analysis=warning_analysis,
            pattern_detection=pattern_detection,
            anomalies=anomalies,
            likely_root_cause=likely_root_cause,
            recommendations=recommendations,
            interesting_log_snippets=interesting_log_snippets,
        )
