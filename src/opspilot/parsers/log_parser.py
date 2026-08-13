from __future__ import annotations

import re
from datetime import datetime

from opspilot.domain.models import LogEntry

# Captures common timestamp prefixes at the start of a log line.
TIMESTAMP_PREFIX_RE = re.compile(
    r"^("
    r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?"
    r"|\d{4}/\d{2}/\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?"
    r"|\d{2}-\d{2}-\d{4}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?"
    r")(?:\s+)?"
)

TIMESTAMP_SEARCH_RE = re.compile(
    r"("
    r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?"
    r"|\d{4}/\d{2}/\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?"
    r"|\d{2}-\d{2}-\d{4}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?"
    r")"
)

TIMESTAMP_PARSE_PATTERNS = [
    "%Y-%m-%d %H:%M:%S,%f",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S,%f",
    "%Y/%m/%d %H:%M:%S.%f",
    "%Y/%m/%d %H:%M:%S",
    "%d-%m-%Y %H:%M:%S,%f",
    "%d-%m-%Y %H:%M:%S.%f",
    "%d-%m-%Y %H:%M:%S",
    "%b %d %H:%M:%S",
]

LEVEL_RE = re.compile(
    r"\b(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL|TRACE)\b",
    flags=re.IGNORECASE,
)

REQUEST_ID_PATTERNS = [
    re.compile(r"request[_-]?id[:= ]+([A-Za-z0-9-]+)", re.IGNORECASE),
    re.compile(r"trace[_-]?id[:= ]+([A-Za-z0-9-]+)", re.IGNORECASE),
    re.compile(r"session[_-]?id[:= ]+([A-Za-z0-9-]+)", re.IGNORECASE),
    re.compile(r"\bREQ[-_]?([A-Z0-9]+)\b"),
    re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
]

COMPONENT_TOKENS = ("Service", "Component", "Controller", "Worker", "Scheduler", "DB", "Cache", "API")


class LogParser:
    """Parses common text log formats into structured entries."""

    def parse(self, content: str) -> list[LogEntry]:
        entries: list[LogEntry] = []
        for line_number, raw_line in enumerate(content.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            entries.append(self._parse_line(line, line_number))
        return entries

    def _parse_line(self, line: str, line_number: int) -> LogEntry:
        timestamp = self._extract_timestamp(line)
        level = self._extract_level(line)
        message = self._clean_message(line)
        logger = self._extract_logger(line)
        thread_name = self._extract_thread_name(line)
        component = self._extract_component(line)
        request_id = self._extract_request_id(line)

        return LogEntry(
            raw=line,
            line_number=line_number,
            timestamp=timestamp,
            level=level,
            message=message,
            logger=logger,
            thread_name=thread_name,
            component=component,
            request_id=request_id,
        )

    def _extract_timestamp(self, line: str) -> datetime | None:
        match = TIMESTAMP_SEARCH_RE.search(line)
        if not match:
            return None

        normalized = self._normalize_timestamp_value(match.group(1))
        for pattern in TIMESTAMP_PARSE_PATTERNS:
            try:
                return datetime.strptime(normalized, pattern)
            except ValueError:
                continue
        return None

    def _normalize_timestamp_value(self, value: str) -> str:
        normalized = value.strip().replace("T", " ")
        normalized = re.sub(r"Z$", "", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"[+-]\d{2}:?\d{2}$", "", normalized)
        normalized = re.sub(r"(\d{2}:\d{2}:\d{2})\.(\d+)", r"\1,\2", normalized)
        return normalized.strip()

    def _extract_level(self, line: str) -> str | None:
        match = LEVEL_RE.search(line)
        if not match:
            return None

        upper = match.group(1).upper()
        if upper == "WARN":
            return "WARNING"
        return upper

    def _extract_logger(self, line: str) -> str | None:
        for match in re.finditer(r"\[([^\]]+)\]", line):
            candidate = match.group(1).strip()
            if not candidate:
                continue
            if re.search(r"thread|pool", candidate, re.IGNORECASE):
                continue
            if re.match(r"^[A-Za-z0-9_.-]+$", candidate):
                return candidate

        match = re.search(
            r"(?:\[)?(?P<logger>[A-Za-z0-9_.-]+(?:Logger|LOGGER|loger|logger))(?:\])?",
            line,
        )
        if match and match.group("logger"):
            return match.group("logger")
        return None

    def _extract_thread_name(self, line: str) -> str | None:
        match = re.search(
            r"thread(?:\s*name)?(?:\s*[:=]|\s*\[)\s*(?P<name>[A-Za-z0-9_.-]+)",
            line,
            re.IGNORECASE,
        )
        if match:
            return match.group("name")

        bracket_match = re.search(r"\[(?P<name>Thread[^\]]*)\]", line, re.IGNORECASE)
        if bracket_match:
            return bracket_match.group("name")
        return None

    def _extract_component(self, line: str) -> str | None:
        for token in COMPONENT_TOKENS:
            match = re.search(
                rf"{token}[:= ]+(?P<name>[A-Za-z0-9_.-]+)",
                line,
                re.IGNORECASE,
            )
            if match:
                return match.group("name")
        return None

    def _extract_request_id(self, line: str) -> str | None:
        for pattern in REQUEST_ID_PATTERNS:
            match = pattern.search(line)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        return None

    def _clean_message(self, line: str) -> str:
        cleaned = line.strip()

        timestamp_match = TIMESTAMP_PREFIX_RE.match(cleaned)
        if timestamp_match:
            cleaned = cleaned[timestamp_match.end():].strip()

        cleaned = re.sub(
            r"^(?:\[[^\]]+\]\s*)+(?:[A-Z_]+\s+)?(?:DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL|TRACE)\s*[:\-]?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(r"^\[[^\]]+\]\s*", "", cleaned)
        cleaned = re.sub(
            r"\s+\b(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL|TRACE)\b.*$",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        return cleaned.strip()
