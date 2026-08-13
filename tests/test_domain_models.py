"""Pydantic domain model tests."""

from __future__ import annotations

import unittest

from opspilot.domain.models import AnalysisResult, LikelyRootCause, StructuredReport
from pydantic import ValidationError


class DomainModelTests(unittest.TestCase):
    def test_structured_report_requires_log_overview(self) -> None:
        with self.assertRaises(ValidationError):
            StructuredReport(executive_summary="Summary without overview.")

    def test_analysis_result_output_dict(self) -> None:
        report = StructuredReport(
            executive_summary="Healthy run.",
            log_overview={
                "total_lines_processed": 1,
                "log_levels_observed": ["INFO"],
                "major_components": [],
                "request_identifiers": [],
                "thread_names": [],
            },
        )
        result = AnalysisResult(report=report, analysis_source="static_fallback")
        payload = result.to_output_dict()

        self.assertEqual(payload["analysis_source"], "static_fallback")
        self.assertEqual(payload["executive_summary"], "Healthy run.")
        self.assertIn("observed_facts", payload["likely_root_cause"])

    def test_likely_root_cause_defaults(self) -> None:
        root_cause = LikelyRootCause()

        self.assertEqual(root_cause.observed_facts, [])
        self.assertEqual(root_cause.possible_causes, [])
        self.assertEqual(root_cause.assumptions, [])
