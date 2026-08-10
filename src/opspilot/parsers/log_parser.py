from __future__ import annotations

import re
from datetime import datetime
from typing import Iterable

from opspilot.domain.models import LogEntry


class LogParser:
    """Parses common text log formats into structured entries."""

    TIMESTAMP_PATTERNS = [
        "%Y-%m-%d %H:%M:%S,%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S,%f",
        "%Y/%m/%d %H:%M:%S",
        "%d-%m-%Y %H:%M:%S,%f",
        "%d-%m-%Y %H:%M:%S",
        "%b %d %H:%M:%S",
    ]

    def parse(self, content: str) -> list[LogEntry]:
        entries: list[LogEntry] = []
        for line_number, raw_line in enumerate(content.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue

            entry = self._parse_line(line, line_number)
            entries.append(entry)

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
        match = re.search(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:,\d+)?|\d{4}/\d{2}/\d{2}[ T]\d{2}:\d{2}:\d{2}(?:,\d+)?|\d{2}-\d{2}-\d{4}[ T]\d{2}:\d{2}:\d{2}(?:,\d+)?)", line)
        if not match:
            return None
        value = match.group(1).replace("T", " ")
        for pattern in self.TIMESTAMP_PATTERNS:
            try:
                return datetime.strptime(value, pattern)
            except ValueError:
                continue
        return None

    def _extract_level(self, line: str) -> str | None:
        match = re.search(r"\b(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)\b", line, flags=re.IGNORECASE)
        if not match:
            return None
        upper = match.group(1).upper()
        if upper == "WARN":
            return "WARNING"
        return upper

    def _extract_logger(self, line: str) -> str | None:
        match = re.search(r"(?:\[)?(?P<logger>[A-Za-z0-9_.-]+(?:Logger|LOGGER|loger|logger))?(?:\])?", line)
        if match and match.group("logger"):
            return match.group("logger")
        return None

    def _extract_thread_name(self, line: str) -> str | None:
        match = re.search(r"thread(?:\s*[:=]|\s*\[)?(?P<name>[A-Za-z0-9_.-]+)", line, re.IGNORECASE)
        if match:
            return match.group("name")
        return None

    def _extract_component(self, line: str) -> str | None:
        for token in ["Service", "Component", "Controller", "Worker", "Scheduler", "DB", "Cache", "API"]:
            match = re.search(rf"{token}[:= ]+(?P<name>[A-Za-z0-9_.-]+)", line, re.IGNORECASE)
            if match:
                return match.group("name")
        return None

    def _extract_request_id(self, line: str) -> str | None:
        for pattern in [
            r"request[_-]?id[:= ]+([A-Za-z0-9-]+)",
            r"trace[_-]?id[:= ]+([A-Za-z0-9-]+)",
            r"session[_-]?id[:= ]+([A-Za-z0-9-]+)",
            r"\bREQ[-_]?([A-Z0-9]+)\b",
            r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        ]:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        return None

    def _clean_message(self, line: str) -> str:
        cleaned = line.strip()

        timestamp_match = re.match(
            r"^(?P<ts>\d{4}[-/]\d{2}[-/]\d{2}[ T]\d{2}:\d{2}:\d{2}(?:,\d+)?(?:\s*Z)?)(?:\s+)?",
            cleaned,
        )
        if timestamp_match:
            cleaned = cleaned[timestamp_match.end():].strip()

        cleaned = re.sub(
            r"^(?:\[[^\]]+\]\s*)?(?:[A-Z_]+\s+)?(?:DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)\s*[:\-]?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(r"^\[[^\]]+\]\s*", "", cleaned)
        cleaned = re.sub(r"\s+\b(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)\b.*$", "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip()
