"""Service facade tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from opspilot.services.analysis_service import AnalysisService


class AnalysisServiceFacadeTests(unittest.TestCase):
    def test_facade_matches_agent_output(self) -> None:
        fixture = Path(__file__).parent / "fixtures" / "sample_incident.log"
        report = AnalysisService(disable_llm=True).analyze_file(str(fixture))

        self.assertEqual(report["analysis_source"], "static_fallback")
        self.assertEqual(report["log_overview"]["total_lines_processed"], 6)
        self.assertIn("executive_summary", report)
