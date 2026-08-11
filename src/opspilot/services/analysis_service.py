from __future__ import annotations

import os

from opspilot.config import DEFAULT_SETTINGS
from opspilot.domain.models import AnalysisResult, analysis_result_to_dict
from opspilot.loaders.file_loader import FileLoader
from opspilot.llm.llm_client import LLMClient, OpenAICompatibleLLMClient
from opspilot.parsers.log_parser import LogParser
from opspilot.analyzers.static_fallback_analyzer import StaticFallbackAnalyzer
from opspilot.services.evidence_builder import EvidenceBuilder
from opspilot.services.llm_analysis_engine import LLMAnalysisEngine


class AnalysisService:
    """Orchestrates LLM-first log analysis with a separate static fallback path."""

    def __init__(
        self,
        file_loader: FileLoader | None = None,
        parser: LogParser | None = None,
        evidence_builder: EvidenceBuilder | None = None,
        llm_engine: LLMAnalysisEngine | None = None,
        static_analyzer: StaticFallbackAnalyzer | None = None,
        llm_client: LLMClient | None = None,
        model_name: str | None = None,
        disable_llm: bool = False,
    ) -> None:
        self.file_loader = file_loader or FileLoader(
            allowed_extensions=DEFAULT_SETTINGS.allowed_extensions,
            max_file_size_mb=DEFAULT_SETTINGS.max_file_size_mb,
        )
        self.parser = parser or LogParser()
        self.evidence_builder = evidence_builder or EvidenceBuilder()
        self.static_analyzer = static_analyzer or StaticFallbackAnalyzer()

        self.disable_llm = disable_llm
        self.llm_client = llm_client
        if self.llm_client is None and not disable_llm and os.getenv("OPENAI_API_KEY"):
            self.llm_client = OpenAICompatibleLLMClient(model=model_name or DEFAULT_SETTINGS.llm_model)

        self.llm_engine = llm_engine
        if self.llm_engine is None and self.llm_client is not None:
            self.llm_engine = LLMAnalysisEngine(llm_client=self.llm_client)

    def analyze_file(self, file_path: str) -> dict:
        content = self.file_loader.load(file_path)
        entries = self.parser.parse(content)
        result = self.analyze_entries(entries)
        return analysis_result_to_dict(result)

    def analyze_entries(self, entries: list) -> AnalysisResult:
        if self._should_use_llm():
            try:
                evidence = self.evidence_builder.build(entries)
                report = self.llm_engine.analyze(evidence)
                return AnalysisResult(report=report, analysis_source="llm")
            except Exception as exc:
                report = self.static_analyzer.analyze(entries)
                return AnalysisResult(
                    report=report,
                    analysis_source="static_fallback",
                    llm_error=str(exc),
                )

        report = self.static_analyzer.analyze(entries)
        return AnalysisResult(report=report, analysis_source="static_fallback")

    def _should_use_llm(self) -> bool:
        return not self.disable_llm and self.llm_engine is not None and self.llm_client is not None
