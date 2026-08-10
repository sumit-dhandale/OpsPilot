from __future__ import annotations

from opspilot.analyzers.log_analyzer import LogAnalyzer
from opspilot.domain.models import StructuredReport
from opspilot.detectors.pattern_detector import PatternDetector
from opspilot.loaders.file_loader import FileLoader
from opspilot.llm.llm_client import LLMClient
from opspilot.llm.prompt_builder import PromptBuilder
from opspilot.parsers.log_parser import LogParser
from opspilot.reports.report_generator import ReportGenerator
from opspilot.stats.statistics_generator import StatisticsGenerator


class AnalysisService:
    """Orchestrates the single-file log analysis pipeline."""

    def __init__(
        self,
        file_loader: FileLoader | None = None,
        parser: LogParser | None = None,
        analyzer: LogAnalyzer | None = None,
        pattern_detector: PatternDetector | None = None,
        stats_generator: StatisticsGenerator | None = None,
        prompt_builder: PromptBuilder | None = None,
        llm_client: LLMClient | None = None,
        report_generator: ReportGenerator | None = None,
    ) -> None:
        self.file_loader = file_loader or FileLoader()
        self.parser = parser or LogParser()
        self.analyzer = analyzer or LogAnalyzer()
        self.pattern_detector = pattern_detector or PatternDetector()
        self.stats_generator = stats_generator or StatisticsGenerator()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.llm_client = llm_client
        self.report_generator = report_generator or ReportGenerator()

    def analyze_file(self, file_path: str) -> StructuredReport:
        content = self.file_loader.load(file_path)
        entries = self.parser.parse(content)

        analysis = self.analyzer.analyze(entries)
        stats = self.stats_generator.generate(entries)
        patterns, anomalies = self.pattern_detector.detect(entries)

        likely_root_cause = {
            "Observed Facts": [
                "The log file was parsed successfully.",
                "Pattern and anomaly detection were applied to the available log data.",
            ],
            "Possible Causes": patterns or ["No clear root cause was detected from the available evidence."],
            "Assumptions": [
                "This Phase 1 implementation is intentionally conservative and evidence-based.",
            ],
        }

        recommendations = [
            "Review the earliest errors and warnings in the timeline.",
            "Check whether the failures align with recent configuration or deployment events.",
            "Verify network or dependency health if connection-related errors are present.",
        ]

        if patterns:
            recommendations.append("Prioritize the repeated patterns identified by the log analysis engine.")

        executive_summary = (
            "A single log file was analyzed for operational health. "
            "The results are intentionally high level and evidence-based, with emphasis on error clusters, warnings, and timeline events."
        )

        report = self.report_generator.generate(
            executive_summary=executive_summary,
            overview=analysis["overview"],
            timeline=analysis["timeline"],
            error_analysis=analysis["error_analysis"],
            warning_analysis=analysis["warning_analysis"],
            pattern_detection=patterns,
            anomalies=anomalies,
            likely_root_cause=likely_root_cause,
            recommendations=recommendations,
            interesting_log_snippets=[entry.raw for entry in entries[:5]],
        )

        if self.llm_client is not None:
            prompt = self.prompt_builder.build(report)
            self.llm_client.generate(prompt)

        return report
