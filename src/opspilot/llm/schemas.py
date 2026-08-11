"""JSON schema reference for structured LLM responses."""

from __future__ import annotations

STRUCTURED_REPORT_SCHEMA: dict[str, object] = {
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
