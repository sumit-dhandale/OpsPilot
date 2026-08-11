from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError

from opspilot.domain.models import StructuredReport
from opspilot.exceptions import ReportValidationError

logger = logging.getLogger(__name__)


class ReportParser:
    """Validates and parses LLM JSON output into a StructuredReport."""

    def parse(self, data: dict[str, Any]) -> StructuredReport:
        try:
            return StructuredReport.model_validate(data)
        except ValidationError as exc:
            logger.error("Report validation failed: %s", exc)
            raise ReportValidationError(str(exc)) from exc
