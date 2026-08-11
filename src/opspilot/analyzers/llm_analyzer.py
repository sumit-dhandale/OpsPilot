from __future__ import annotations

from opspilot.domain.models import LogEvidenceBundle, StructuredReport
from opspilot.llm.client import LLMClient
from opspilot.llm.prompt_builder import PromptBuilder
from opspilot.llm.report_parser import ReportParser


class LLMAnalyzer:
    """Primary analysis path: evidence in, structured report out via LLM."""

    def __init__(
        self,
        llm_client: LLMClient,
        prompt_builder: PromptBuilder | None = None,
        report_parser: ReportParser | None = None,
    ) -> None:
        self._llm_client = llm_client
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._report_parser = report_parser or ReportParser()

    def analyze(self, evidence: LogEvidenceBundle) -> StructuredReport:
        prompt = self._prompt_builder.build_analysis_prompt(evidence)
        payload = self._llm_client.generate_json(prompt)
        return self._report_parser.parse(payload)
