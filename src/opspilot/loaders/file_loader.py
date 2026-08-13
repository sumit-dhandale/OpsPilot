from __future__ import annotations

from pathlib import Path

from opspilot.config import Settings
from opspilot.exceptions import FileLoadError


class FileLoader:
    """Loads and validates a single log file."""

    def __init__(self, settings: Settings) -> None:
        self.allowed_extensions = {ext.lower() for ext in settings.allowed_extensions}
        self.max_file_size_mb = settings.max_file_size_mb

    def load(self, file_path: str | Path) -> str:
        path = Path(file_path).expanduser().resolve()

        if not path.exists():
            raise FileLoadError(f"File does not exist: {path}")
        if not path.is_file():
            raise FileLoadError(f"Path is not a file: {path}")

        suffix = path.suffix.lower()
        if suffix not in self.allowed_extensions:
            raise FileLoadError(
                f"Unsupported file type '{suffix}'. Allowed types: {sorted(self.allowed_extensions)}"
            )

        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            raise FileLoadError(
                f"File exceeds the supported size limit of {self.max_file_size_mb} MB: {path}"
            )

        return path.read_text(encoding="utf-8", errors="replace")
