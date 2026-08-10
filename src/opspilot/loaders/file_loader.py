from __future__ import annotations

from pathlib import Path


class FileLoader:
    """Loads and validates a single text or log file."""

    def __init__(self, allowed_extensions: set[str] | None = None, max_file_size_mb: int = 200):
        self.allowed_extensions = allowed_extensions or {".log", ".txt"}
        self.max_file_size_mb = max_file_size_mb

    def load(self, file_path: str | Path) -> str:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File does not exist: {path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")

        suffix = path.suffix.lower()
        if suffix not in self.allowed_extensions:
            raise ValueError(
                f"Unsupported file type '{suffix}'. Allowed types: {sorted(self.allowed_extensions)}"
            )

        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            raise ValueError(
                f"File exceeds the supported size limit of {self.max_file_size_mb} MB: {path}"
            )

        return path.read_text(encoding="utf-8", errors="replace")
