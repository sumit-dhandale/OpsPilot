"""Shared pytest fixtures for OpsPilot tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from opspilot.config import Settings
from opspilot.parsers.log_parser import LogParser

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_incident_log_path() -> Path:
    return FIXTURES_DIR / "sample_incident.log"


@pytest.fixture
def sample_incident_content(sample_incident_log_path: Path) -> str:
    return sample_incident_log_path.read_text(encoding="utf-8")


@pytest.fixture
def parsed_entries(sample_incident_content: str) -> list:
    return LogParser().parse(sample_incident_content)


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        max_file_size_mb=200,
        max_evidence_lines=500,
        max_level_evidence_lines=150,
    )
