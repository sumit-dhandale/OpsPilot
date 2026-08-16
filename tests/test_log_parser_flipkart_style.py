"""Flipkart-style production log format tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from opspilot.parsers.log_parser import LogParser


class LogParserFlipkartStyleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixture = Path(__file__).parent / "fixtures" / "flipkart_style_sample.log"
        cls.entries = LogParser().parse(fixture.read_text(encoding="utf-8"))
        cls.structured = [e for e in cls.entries if e.metadata.get("entry_type") == "structured"]
        cls.stack_lines = [e for e in cls.entries if e.metadata.get("entry_type") in {"stack_trace", "exception"}]

    def test_parses_structured_info_lines(self) -> None:
        info_lines = [e for e in self.structured if e.level == "INFO"]
        self.assertGreaterEqual(len(info_lines), 3)

        executor = next(e for e in info_lines if e.logger == "HttpCasCommandExecutor")
        self.assertEqual(executor.request_id, "718828fa-dfd9-4871-8f6f-a7102cc2dd37")
        self.assertEqual(executor.thread_name, "hystrix-USER_INSIGHTS-32")
        self.assertEqual(executor.metadata["trace_id"], "T-1502615169846681-1899-106653173")
        self.assertIn("authentication ticket", executor.message.lower())

    def test_parses_warn_with_impl_logger(self) -> None:
        warn = next(e for e in self.structured if e.logger == "MlpModelResponseEntityDaoImpl")
        self.assertEqual(warn.level, "WARNING")
        self.assertIn("mlpModelResponseEntity", warn.message)

    def test_parses_dw_thread_and_refund_resource(self) -> None:
        refund = next(e for e in self.structured if e.logger == "RefundResource")
        self.assertIn("dw-246", refund.thread_name)
        self.assertIn("refundOptions", refund.thread_name)
        self.assertIn("Received refundOptions request", refund.message)

    def test_default_trace_and_request_are_not_promoted(self) -> None:
        default_line = next(e for e in self.structured if e.logger == "RulesPlatformDEExecutionHandler")
        self.assertIsNone(default_line.request_id)
        self.assertIsNone(default_line.metadata.get("trace_id"))

    def test_parses_stack_trace_and_exception_lines(self) -> None:
        self.assertGreaterEqual(len(self.stack_lines), 2)
        exception = next(e for e in self.stack_lines if e.metadata["entry_type"] == "exception")
        self.assertIn("DataNotFoundException", exception.message)
        stack = next(e for e in self.stack_lines if e.metadata["entry_type"] == "stack_trace")
        self.assertTrue(stack.message.startswith("at "))

    def test_stack_lines_inherit_request_context(self) -> None:
        stack_with_context = next(
            e for e in self.stack_lines
            if e.request_id == "718828fa-dfd9-4871-8f6f-a7102cc2dd37"
        )
        self.assertIsNotNone(stack_with_context)

    def test_parses_access_log_line(self) -> None:
        access = next(e for e in self.entries if e.metadata.get("entry_type") == "access_log")
        self.assertEqual(access.level, "INFO")
        self.assertIn("POST /de/refund/refundOptions", access.message)
        self.assertEqual(access.metadata["http_status"], 200)
        self.assertIsNotNone(access.timestamp)

    def test_parses_error_with_empty_request_ref(self) -> None:
        error = next(
            e for e in self.structured
            if e.level == "ERROR" and e.logger == "HttpCommandExecutor"
        )
        self.assertIsNone(error.request_id)
        self.assertIn("Read timed out", error.message)

    def test_single_line_structured_format(self) -> None:
        line = (
            "[INFO] [2026-06-13 20:30:52,925] [pool-8-thread-1] "
            "T:T-trace-1 - R:abc-123-def [MyService]: hello world"
        )
        entry = LogParser().parse(line)[0]
        self.assertEqual(entry.level, "INFO")
        self.assertEqual(entry.logger, "MyService")
        self.assertEqual(entry.request_id, "abc-123-def")
        self.assertEqual(entry.metadata["trace_id"], "T-trace-1")
        self.assertEqual(entry.message, "hello world")
