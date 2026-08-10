import unittest

from opspilot.parsers.log_parser import LogParser


class LogParserTests(unittest.TestCase):
    def test_parse_common_log_line(self):
        content = "2024-01-01 10:00:00,123 INFO Application started\n"
        entries = LogParser().parse(content)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].level, "INFO")
        self.assertIn("Application started", entries[0].message)
        self.assertIsNotNone(entries[0].timestamp)

    def test_parse_error_message(self):
        content = "2024-01-01 10:05:30 ERROR Database connection timeout\n"
        entries = LogParser().parse(content)

        self.assertEqual(entries[0].level, "ERROR")
        self.assertIn("Database connection timeout", entries[0].message)
