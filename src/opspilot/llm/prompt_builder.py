from __future__ import annotations

import json

from opspilot.domain.models import LogEvidenceBundle, StructuredReport
from opspilot.llm.prompts import LOG_ANALYSIS_RULES
from opspilot.llm.schemas import STRUCTURED_REPORT_SCHEMA


class PromptBuilder:
    """Builds LLM prompts for primary log analysis."""

    def build_analysis_prompt(self, evidence: LogEvidenceBundle) -> str:
        evidence_payload = evidence.model_dump()

        return (
            "You are an on-call log analysis agent.\n"
            "Analyze ONLY the evidence below and produce a structured incident report.\n"
            f"{LOG_ANALYSIS_RULES}\n\n"
            f"JSON schema:\n{json.dumps(STRUCTURED_REPORT_SCHEMA, indent=2)}\n\n"
            f"Evidence bundle:\n{json.dumps(evidence_payload, indent=2)}"
        )

    def build_refinement_prompt(self, report: StructuredReport) -> str:
        return (
            "Refine this structured log analysis report for clarity and actionability. "
            "Return valid JSON with the same schema.\n"
            f"Report:\n{json.dumps(report.model_dump(), indent=2)}"
        )
