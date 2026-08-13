"""File loader tests — Milestone 1.1."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from opspilot.config import Settings
from opspilot.exceptions import FileLoadError
from opspilot.loaders.file_loader import FileLoader


class FileLoaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(max_file_size_mb=1)
        self.loader = FileLoader(self.settings)

    def test_load_valid_log_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "app.log"
            log_file.write_text("2024-01-01 10:00:00 INFO started\n", encoding="utf-8")
            content = self.loader.load(log_file)
            self.assertIn("INFO started", content)

    def test_load_txt_extension(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "app.txt"
            log_file.write_text("plain log line\n", encoding="utf-8")
            content = self.loader.load(log_file)
            self.assertEqual(content, "plain log line\n")

    def test_load_accepts_string_and_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "app.log"
            log_file.write_text("line\n", encoding="utf-8")
            self.assertEqual(self.loader.load(str(log_file)), "line\n")
            self.assertEqual(self.loader.load(log_file), "line\n")

    def test_missing_file_raises(self) -> None:
        with self.assertRaises(FileLoadError):
            self.loader.load("/tmp/does-not-exist-opspilot.log")

    def test_directory_path_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(FileLoadError):
                self.loader.load(tmp_dir)

    def test_unsupported_extension_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_file = Path(tmp_dir) / "app.json"
            bad_file.write_text("{}", encoding="utf-8")
            with self.assertRaises(FileLoadError):
                self.loader.load(bad_file)

    def test_empty_file_loads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "empty.log"
            log_file.write_text("", encoding="utf-8")
            content = self.loader.load(log_file)
            self.assertEqual(content, "")

    def test_unicode_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "unicode.log"
            log_file.write_text("INFO café started 日本語\n", encoding="utf-8")
            content = self.loader.load(log_file)
            self.assertIn("café", content)

    def test_invalid_utf8_is_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "binary.log"
            log_file.write_bytes(b"INFO ok \xff\xfe\n")
            content = self.loader.load(log_file)
            self.assertIn("INFO ok", content)

    def test_oversized_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "huge.log"
            log_file.write_bytes(b"x" * (2 * 1024 * 1024))
            with self.assertRaises(FileLoadError):
                self.loader.load(log_file)

    def test_extension_check_is_case_insensitive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file = Path(tmp_dir) / "app.LOG"
            log_file.write_text("uppercase ext\n", encoding="utf-8")
            content = self.loader.load(log_file)
            self.assertEqual(content, "uppercase ext\n")
