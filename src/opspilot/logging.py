"""Logging configuration for OpsPilot."""

from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    """Configure application-wide logging for CLI and library use."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        stream=sys.stderr,
        force=True,
    )
    logging.getLogger("opspilot").setLevel(log_level)
