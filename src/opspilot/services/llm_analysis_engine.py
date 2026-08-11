from __future__ import annotations

from opspilot.domain.models import LogEvidenceBundle, StructuredReport
from opspilot.llm.llm_client import LLMClient
from opspilot.llm.prompt_builder import PromptBuilder
from opspilot.llm.report_parser import ReportParser


class LLMAnalysisEngine:
    """Primary analysis path: evidence in, structured report out via LLM."""

    def __init__(
        self,
        llm_client: LLMClient,
        prompt_builder: PromptBuilder | None = None,
        report_parser: ReportParser | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.report_parser = report_parser or ReportParser()

    def analyze(self, evidence: LogEvidenceBundle) -> StructuredReport:
        prompt = self.prompt_builder.build_analysis_prompt(evidence)
        payload = self.llm_client.generate_json(prompt)
        return self.report_parser.parse(payload)
