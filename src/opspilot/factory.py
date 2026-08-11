"""Dependency wiring for the log analysis agent."""

from __future__ import annotations

from opspilot.agent.log_analysis_agent import LogAnalysisAgent
from opspilot.analyzers.llm_analyzer import LLMAnalyzer
from opspilot.analyzers.static_fallback_analyzer import StaticFallbackAnalyzer
from opspilot.config import Settings, get_settings
from opspilot.evidence.builder import EvidenceBuilder
from opspilot.llm.client import OpenAICompatibleLLMClient
from opspilot.loaders.file_loader import FileLoader
from opspilot.parsers.log_parser import LogParser


def build_log_analysis_agent(
    settings: Settings | None = None,
    disable_llm: bool = False,
    model_name: str | None = None,
) -> LogAnalysisAgent:
    """Construct a fully wired log analysis agent from settings."""
    resolved_settings = settings or get_settings()

    file_loader = FileLoader(resolved_settings)
    parser = LogParser()
    evidence_builder = EvidenceBuilder(resolved_settings)
    static_analyzer = StaticFallbackAnalyzer()

    llm_analyzer = None
    enable_llm = not disable_llm
    if enable_llm and resolved_settings.openai_api_key:
        llm_client = OpenAICompatibleLLMClient(resolved_settings, model=model_name)
        llm_analyzer = LLMAnalyzer(llm_client)

    return LogAnalysisAgent(
        file_loader=file_loader,
        parser=parser,
        evidence_builder=evidence_builder,
        llm_analyzer=llm_analyzer,
        static_analyzer=static_analyzer,
        enable_llm=enable_llm,
    )
