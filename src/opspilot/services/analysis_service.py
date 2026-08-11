"""Backward-compatible service facade over LogAnalysisAgent."""

from __future__ import annotations

from opspilot.factory import build_log_analysis_agent


class AnalysisService:
    """Facade for callers expecting the legacy AnalysisService interface."""

    def __init__(
        self,
        model_name: str | None = None,
        disable_llm: bool = False,
    ) -> None:
        self._agent = build_log_analysis_agent(
            disable_llm=disable_llm,
            model_name=model_name,
        )

    def analyze_file(self, file_path: str) -> dict:
        return self._agent.analyze_file(file_path).to_output_dict()

    def analyze_entries(self, entries: list) -> object:
        return self._agent.analyze_entries(entries)
