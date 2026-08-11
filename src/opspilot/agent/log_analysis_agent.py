"""Log analysis agent orchestration."""

from __future__ import annotations

import logging
from pathlib import Path

from opspilot.domain.interfaces import (
    EvidenceBuilderProtocol,
    FileLoaderProtocol,
    LLMAnalyzerProtocol,
    LogParserProtocol,
    StaticAnalyzerProtocol,
)
from opspilot.domain.models import AnalysisResult, LogEntry
from opspilot.exceptions import LLMError, ReportValidationError

logger = logging.getLogger(__name__)


class LogAnalysisAgent:
    """LLM-first log analysis agent with an isolated static fallback path."""

    def __init__(
        self,
        file_loader: FileLoaderProtocol,
        parser: LogParserProtocol,
        evidence_builder: EvidenceBuilderProtocol,
        llm_analyzer: LLMAnalyzerProtocol | None,
        static_analyzer: StaticAnalyzerProtocol,
        enable_llm: bool = True,
    ) -> None:
        self._file_loader = file_loader
        self._parser = parser
        self._evidence_builder = evidence_builder
        self._llm_analyzer = llm_analyzer
        self._static_analyzer = static_analyzer
        self._enable_llm = enable_llm

    def analyze_file(self, file_path: str | Path) -> AnalysisResult:
        path = Path(file_path)
        logger.info("Loading log file: %s", path)
        content = self._file_loader.load(str(path))
        entries = self._parser.parse(content)
        logger.info("Parsed %d log entries from %s", len(entries), path)
        return self.analyze_entries(entries)

    def analyze_entries(self, entries: list[LogEntry]) -> AnalysisResult:
        if self._should_use_llm():
            try:
                logger.info("Running LLM analysis")
                evidence = self._evidence_builder.build(entries)
                report = self._llm_analyzer.analyze(evidence)
                logger.info("LLM analysis completed successfully")
                return AnalysisResult(report=report, analysis_source="llm")
            except (LLMError, ReportValidationError) as exc:
                logger.warning("LLM analysis failed, using static fallback: %s", exc)
                report = self._static_analyzer.analyze(entries)
                return AnalysisResult(
                    report=report,
                    analysis_source="static_fallback",
                    llm_error=str(exc),
                )

        logger.info("Running static fallback analysis")
        report = self._static_analyzer.analyze(entries)
        return AnalysisResult(report=report, analysis_source="static_fallback")

    def _should_use_llm(self) -> bool:
        return self._enable_llm and self._llm_analyzer is not None
