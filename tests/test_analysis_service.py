import tempfile
import unittest
from pathlib import Path

from opspilot.services.analysis_service import AnalysisService


class AnalysisServiceTests(unittest.TestCase):
    def test_analysis_service_generates_log_report(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "sample.log"
            log_file.write_text(
                "2024-01-01 10:00:00 INFO Application started\n"
                "2024-01-01 10:00:05 WARN Slow response observed\n"
                "2024-01-01 10:00:10 ERROR Database connection timeout\n",
                encoding="utf-8",
            )

            report = AnalysisService().analyze_file(str(log_file))

            self.assertTrue(report.executive_summary)
            self.assertEqual(report.log_overview.total_lines_processed, 3)
            self.assertTrue(report.timeline)
            self.assertTrue(report.error_analysis)

    def test_analysis_service_handles_python_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            code_file = Path(tmp_dir) / "worker.py"
            code_file.write_text(
                "import os\n\n"
                "def process(data):\n"
                "    if not data:\n"
                "        raise ValueError('missing input')\n"
                "    return data.strip()\n\n"
                "class Worker:\n"
                "    def run(self):\n"
                "        return process(' sample ')\n",
                encoding="utf-8",
            )

            result = AnalysisService().analyze_file(str(code_file))

            self.assertIn("python", result["language"].lower())
            self.assertIn("process", result["functions"]) 
            self.assertIn("Worker", result["classes"]) 
            self.assertTrue(result["summary"]) 
