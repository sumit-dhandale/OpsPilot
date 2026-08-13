"""CLI smoke tests."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from opspilot.cli import build_parser, main


class CLITests(unittest.TestCase):
    def test_version_flag(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            build_parser().parse_args(["--version"])
        self.assertEqual(ctx.exception.code, 0)

    def test_analyze_sample_log_llm_off(self) -> None:
        fixture = Path(__file__).parent / "fixtures" / "sample_incident.log"
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            code = main([str(fixture), "--llm-off"])

        self.assertEqual(code, 0)
        output = stdout.getvalue()
        self.assertIn("executive_summary", output)
        self.assertIn("static_fallback", output)

    def test_missing_file_returns_error_code(self) -> None:
        code = main(["/tmp/opspilot-missing-file.log", "--llm-off"])
        self.assertEqual(code, 1)
