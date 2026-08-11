from __future__ import annotations

import json
import re

from opspilot.domain.models import LogEvidenceBundle, StructuredReport


class PromptBuilder:
    """Builds LLM prompts for primary log analysis."""

    REPORT_SCHEMA = {
        "executive_summary": "string",
        "log_overview": {
            "time_range": "string|null",
            "total_lines_processed": "integer",
            "log_levels_observed": ["string"],
            "major_components": ["string"],
            "request_identifiers": ["string"],
            "thread_names": ["string"],
        },
        "timeline": [{"timestamp": "string|null", "message": "string", "source": "string|null"}],
        "error_analysis": [
            {
                "error_type": "string",
                "occurrence_count": "integer",
                "first_occurrence": "string|null",
                "last_occurrence": "string|null",
                "short_explanation": "string",
            }
        ],
        "warning_analysis": [
            {
                "warning_type": "string",
                "occurrence_count": "integer",
                "first_occurrence": "string|null",
                "last_occurrence": "string|null",
                "short_explanation": "string",
            }
        ],
        "pattern_detection": ["string"],
        "anomalies": ["string"],
        "likely_root_cause": {
            "observed_facts": ["string"],
            "possible_causes": ["string"],
            "assumptions": ["string"],
        },
        "recommendations": ["string"],
        "interesting_log_snippets": ["string"],
    }

    def build_analysis_prompt(self, evidence: LogEvidenceBundle) -> str:
        evidence_payload = {
            "total_lines": evidence.total_lines,
            "time_range": evidence.time_range,
            "statistics": evidence.statistics,
            "sample_lines": evidence.sample_lines,
            "error_lines": evidence.error_lines,
            "warning_lines": evidence.warning_lines,
            "lifecycle_lines": evidence.lifecycle_lines,
        }

        return (
            "You are an on-call log analysis agent.\n"
            "Analyze ONLY the evidence below and produce a structured incident report.\n"
            "Rules:\n"
            "- Use only evidence from the provided log material.\n"
            "- Ignore repetitive noise and merge duplicate events.\n"
            "- Do not invent patterns, causes, or events unsupported by evidence.\n"
            "- Separate facts from assumptions in likely_root_cause.\n"
            "- Keep executive_summary readable in under one minute.\n"
            "- Return valid JSON only, matching the schema exactly.\n\n"
            f"JSON schema:\n{json.dumps(self.REPORT_SCHEMA, indent=2)}\n\n"
            f"Evidence bundle:\n{json.dumps(evidence_payload, indent=2)}"
        )

    def build(self, report: StructuredReport) -> str:
        """Optional refinement prompt for an existing structured report."""
        from opspilot.domain.models import to_serializable

        return (
            "Refine this structured log analysis report for clarity and actionability. "
            "Return valid JSON with the same schema.\n"
            f"Report:\n{json.dumps(to_serializable(report), indent=2)}"
        )
