from __future__ import annotations

from opspilot.domain.models import StructuredReport


class PromptBuilder:
    """Builds a compact prompt for an LLM to refine a structured report."""

    def build(self, report: StructuredReport) -> str:
        parts = [
            "You are analyzing a single log file for an on-call engineer.",
            "Produce a concise and actionable investigation summary with technical precision.",
            "Use only evidence from the log entries and avoid speculation.",
            "",
            f"Executive Summary: {report.executive_summary}",
            f"Log Overview: {report.log_overview}",
            f"Timeline: {report.timeline}",
            f"Error Analysis: {report.error_analysis}",
            f"Warning Analysis: {report.warning_analysis}",
            f"Pattern Detection: {report.pattern_detection}",
            f"Anomalies: {report.anomalies}",
            f"Likely Root Cause: {report.likely_root_cause}",
            f"Recommendations: {report.recommendations}",
            f"Interesting Snippets: {report.interesting_log_snippets}",
        ]
        return "\n".join(parts)
