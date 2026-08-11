"""Application-specific exceptions for OpsPilot."""

from __future__ import annotations


class OpsPilotError(Exception):
    """Base exception for recoverable OpsPilot failures."""


class FileLoadError(OpsPilotError):
    """Raised when a log file cannot be loaded or validated."""


class ParseError(OpsPilotError):
    """Raised when log content cannot be parsed."""


class LLMError(OpsPilotError):
    """Raised when the LLM provider fails or returns invalid output."""


class ReportValidationError(OpsPilotError):
    """Raised when analysis output does not match the expected report schema."""
