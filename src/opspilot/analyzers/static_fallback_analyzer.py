from __future__ import annotations

from opspilot.analyzers.log_analyzer import LogAnalyzer
from opspilot.detectors.pattern_detector import PatternDetector
from opspilot.domain.models import LogEntry, StructuredReport
from opspilot.reports.report_generator import ReportGenerator
from opspilot.stats.statistics_generator import StatisticsGenerator


class StaticFallbackAnalyzer:
    """Heuristic-only analyzer used when LLM analysis is unavailable or fails."""

    def __init__(
        self,
        log_analyzer: LogAnalyzer | None = None,
        pattern_detector: PatternDetector | None = None,
        statistics_generator: StatisticsGenerator | None = None,
        report_generator: ReportGenerator | None = None,
    ) -> None:
        self.log_analyzer = log_analyzer or LogAnalyzer()
        self.pattern_detector = pattern_detector or PatternDetector()
        self.statistics_generator = statistics_generator or StatisticsGenerator()
        self.report_generator = report_generator or ReportGenerator()

    def analyze(self, entries: list[LogEntry]) -> StructuredReport:
        findings = self.log_analyzer.analyze(entries)
        patterns, anomalies = self.pattern_detector.detect(entries)
        statistics = self.statistics_generator.generate(entries)

        overview = findings["overview"]
        error_analysis = findings["error_analysis"]
        warning_analysis = findings["warning_analysis"]
        timeline = findings["timeline"]

        executive_summary = self._build_executive_summary(entries, overview, error_analysis, warning_analysis)
        likely_root_cause = self._build_likely_root_cause(error_analysis, patterns, anomalies)
        recommendations = self._build_recommendations(error_analysis, warning_analysis, patterns)
        snippets = self._build_snippets(entries, error_analysis)

        merged_patterns = list(dict.fromkeys(list(findings["pattern_detection"]) + patterns))
        merged_anomalies = list(dict.fromkeys(list(findings["anomalies"]) + anomalies))

        return self.report_generator.generate(
            executive_summary=executive_summary,
            overview=overview,
            timeline=timeline,
            error_analysis=error_analysis,
            warning_analysis=warning_analysis,
            pattern_detection=merged_patterns,
            anomalies=merged_anomalies,
            likely_root_cause=likely_root_cause,
            recommendations=recommendations,
            interesting_log_snippets=snippets,
        )

    def _build_executive_summary(
        self,
        entries: list[LogEntry],
        overview: object,
        error_analysis: list,
        warning_analysis: list,
    ) -> str:
        if not entries:
            return "No log entries were found. The file may be empty or unparsable."

        error_count = sum(group.occurrence_count for group in error_analysis)
        warning_count = sum(group.occurrence_count for group in warning_analysis)
        levels = getattr(overview, "log_levels_observed", [])
        time_range = getattr(overview, "time_range", None)

        health = "failed" if error_count else "healthy"
        if error_count and warning_count:
            health = "degraded"

        parts = [
            f"The log contains {len(entries)} parsed line(s) with levels {', '.join(levels) if levels else 'unknown'}.",
        ]
        if time_range:
            parts.append(f"Time range: {time_range}.")
        parts.append(f"Execution appears {health} with {error_count} error occurrence(s) and {warning_count} warning occurrence(s).")
        if error_analysis:
            parts.append(f"Primary issue: {error_analysis[0].error_type[:160]}.")
        return " ".join(parts)

    def _build_likely_root_cause(
        self,
        error_analysis: list,
        patterns: list[str],
        anomalies: list[str],
    ) -> dict[str, list[str]]:
        observed_facts: list[str] = []
        possible_causes: list[str] = []
        assumptions: list[str] = []

        for group in error_analysis[:3]:
            observed_facts.append(
                f"{group.error_type} occurred {group.occurrence_count} time(s) "
                f"between {group.first_occurrence or 'unknown'} and {group.last_occurrence or 'unknown'}."
            )

        for pattern in patterns[:5]:
            observed_facts.append(pattern)

        for anomaly in anomalies[:5]:
            observed_facts.append(anomaly)

        if any("timeout" in fact.lower() for fact in observed_facts):
            possible_causes.append("Downstream dependency latency or network timeout.")
        if any("connection" in fact.lower() for fact in observed_facts):
            possible_causes.append("Connectivity issue between services or to infrastructure.")
        if any("memory" in fact.lower() for fact in observed_facts):
            possible_causes.append("Memory pressure affecting service stability.")
        if error_analysis and not possible_causes:
            possible_causes.append("Recurring application error path in the dominant error message.")

        if not observed_facts:
            assumptions.append("No strong failure signals were detected; health assessment is based on limited evidence.")

        return {
            "observed_facts": observed_facts,
            "possible_causes": possible_causes,
            "assumptions": assumptions,
        }

    def _build_recommendations(
        self,
        error_analysis: list,
        warning_analysis: list,
        patterns: list[str],
    ) -> list[str]:
        recommendations: list[str] = []

        if error_analysis:
            recommendations.append("Inspect the earliest occurrence of the top error group and correlate with deployment or config changes.")
        if warning_analysis:
            recommendations.append("Review warning trends that precede errors to identify early degradation signals.")
        if any("timeout" in pattern.lower() for pattern in patterns):
            recommendations.append("Verify network connectivity and timeout settings for affected dependencies.")
        if any("connection" in pattern.lower() for pattern in patterns):
            recommendations.append("Check service endpoints, credentials, and firewall rules for connection failures.")
        if any("memory" in pattern.lower() for pattern in patterns):
            recommendations.append("Inspect memory usage, GC behavior, and container limits for the affected service.")

        if not recommendations:
            recommendations.append("Collect additional logs around the reported time range if behavior remains unclear.")

        return recommendations[:6]

    def _build_snippets(self, entries: list[LogEntry], error_analysis: list) -> list[str]:
        snippets: list[str] = []
        error_levels = {"ERROR", "CRITICAL", "FATAL"}

        for group in error_analysis[:3]:
            for entry in entries:
                if entry.level in error_levels and entry.message.startswith(group.error_type[:40]):
                    snippets.append(entry.raw)
                    break

        for entry in entries:
            if entry.level in error_levels and entry.raw not in snippets:
                snippets.append(entry.raw)
            if len(snippets) >= 5:
                break

        return snippets[:5]
