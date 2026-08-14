from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from opspilot.domain.models import LogEntry

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
    r"|\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}"
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
    "%d/%b/%Y:%H:%M:%S",
    "%b %d %H:%M:%S",
]

BRACKET_LEVEL_RE = re.compile(
    r"^\[(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL|TRACE)\]",
    flags=re.IGNORECASE,
)

STRUCTURED_LOG_RE = re.compile(
    r"^\[(?P<level>DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL|TRACE)\]\s*"
    r"\[(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d+)?)\]\s*"
    r"\[(?P<thread>[^\]]+)\]\s*"
    r"T:(?P<trace>.+?)\s+-\s+R:"
    r"(?P<request>[^\s\[]*)\s*"
    r"(?:\[(?P<logger>[^\]]+)\]:?\s*)?"
    r"(?P<message>.*)$",
    flags=re.IGNORECASE,
)

LEVEL_RE = re.compile(
    r"\b(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL|TRACE)\b",
    flags=re.IGNORECASE,
)

TRACE_ID_RE = re.compile(r"\bT:([^\s-]+)")
REQUEST_REF_RE = re.compile(r"\bR:([^\s\[]+)")

REQUEST_ID_PATTERNS = [
    re.compile(r"request[_-]?id[:= ]+([A-Za-z0-9-]+)", re.IGNORECASE),
    re.compile(r"trace[_-]?id[:= ]+([A-Za-z0-9-]+)", re.IGNORECASE),
    re.compile(r"session[_-]?id[:= ]+([A-Za-z0-9-]+)", re.IGNORECASE),
    re.compile(r"\bREQ[-_]?([A-Z0-9]+)\b"),
    re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"),
]

ACCESS_LOG_RE = re.compile(
    r"^(?P<client_ip>\d+\.\d+\.\d+\.\d+)\s+-\s+-\s+-\s+"
    r"(?P<timestamp>\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}\s+[+-]\d{4})\s+"
    r'"(?P<method>\w+)\s+(?P<path>[^"]+)\s+HTTP/[^"]+"\s+(?P<status>\d+)(?:\s+(?P<bytes>\d+))?'
)

STACK_TRACE_RE = re.compile(
    r"^(?:\s+at\s+|Caused by:|\t)",
)
EXCEPTION_LINE_RE = re.compile(r"^[a-z][\w.$]*(?:Exception|Error)(?::\s.*)?$", re.IGNORECASE)

COMPONENT_TOKENS = ("Service", "Component", "Controller", "Worker", "Scheduler", "DB", "Cache", "API")

LOGGER_BRACKET_SKIP = frozenset(
    {
        "info",
        "warn",
        "warning",
        "error",
        "debug",
        "trace",
        "critical",
        "fatal",
    }
)


class LogParser:
    """Parses common text log formats into structured entries."""

    def parse(self, content: str) -> list[LogEntry]:
        entries: list[LogEntry] = []
        context: dict[str, Any] = {}

        for line_number, raw_line in enumerate(content.splitlines(), start=1):
            if not raw_line.strip():
                continue

            if self._is_stack_or_exception_line(raw_line):
                entries.append(self._parse_continuation_line(raw_line.strip(), line_number, context))
                continue

            line = raw_line.strip()

            access_match = ACCESS_LOG_RE.match(line)
            if access_match:
                entry = self._parse_access_log(line, line_number, access_match)
                entries.append(entry)
                self._update_context(context, entry)
                continue

            entry = self._parse_line(line, line_number)
            entries.append(entry)
            self._update_context(context, entry)

        return entries

    def _parse_line(self, line: str, line_number: int) -> LogEntry:
        structured = STRUCTURED_LOG_RE.match(line)
        if structured:
            return self._parse_structured_line(line, line_number, structured)

        timestamp = self._extract_timestamp(line)
        level = self._extract_level(line)
        message = self._clean_message(line)
        logger = self._extract_logger(line)
        thread_name = self._extract_thread_name(line)
        component = self._extract_component(line)
        request_id = self._extract_request_id(line)
        trace_id = self._extract_trace_id(line)

        metadata: dict[str, Any] = {"entry_type": "log"}
        if trace_id:
            metadata["trace_id"] = trace_id

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
            metadata=metadata,
        )

    def _parse_structured_line(self, line: str, line_number: int, match: re.Match[str]) -> LogEntry:
        level = self._normalize_level(match.group("level"))
        timestamp = self._parse_timestamp_value(match.group("timestamp"))
        thread_name = match.group("thread").strip()
        trace_id = match.group("trace").strip()
        request_raw = match.group("request").strip()
        request_id = request_raw if request_raw and request_raw != "_default_" else None
        logger = match.group("logger")
        message = (match.group("message") or "").strip()

        if not message and logger:
            message = logger
            logger = None

        metadata: dict[str, Any] = {
            "entry_type": "structured",
            "trace_id": trace_id if trace_id != "_default_" else None,
        }

        return LogEntry(
            raw=line,
            line_number=line_number,
            timestamp=timestamp,
            level=level,
            message=message,
            logger=logger,
            thread_name=thread_name,
            request_id=request_id,
            metadata=metadata,
        )

    def _parse_access_log(self, line: str, line_number: int, match: re.Match[str]) -> LogEntry:
        timestamp = self._parse_timestamp_value(match.group("timestamp").split()[0])
        method = match.group("method")
        path = match.group("path")
        status = match.group("status")

        return LogEntry(
            raw=line,
            line_number=line_number,
            timestamp=timestamp,
            level="INFO",
            message=f"{method} {path} status={status}",
            component="access_log",
            metadata={
                "entry_type": "access_log",
                "client_ip": match.group("client_ip"),
                "http_status": int(status),
            },
        )

    def _parse_continuation_line(self, line: str, line_number: int, context: dict[str, Any]) -> LogEntry:
        entry_type = "exception" if EXCEPTION_LINE_RE.match(line.strip()) else "stack_trace"
        return LogEntry(
            raw=line,
            line_number=line_number,
            level=context.get("level"),
            message=line.strip(),
            logger=context.get("logger"),
            thread_name=context.get("thread_name"),
            request_id=context.get("request_id"),
            metadata={
                "entry_type": entry_type,
                "trace_id": context.get("trace_id"),
            },
        )

    def _update_context(self, context: dict[str, Any], entry: LogEntry) -> None:
        if entry.level in {"ERROR", "WARNING", "INFO", "DEBUG", "TRACE", "CRITICAL", "FATAL"}:
            context["level"] = entry.level
        if entry.request_id:
            context["request_id"] = entry.request_id
        if entry.thread_name:
            context["thread_name"] = entry.thread_name
        if entry.logger:
            context["logger"] = entry.logger
        trace_id = entry.metadata.get("trace_id")
        if trace_id:
            context["trace_id"] = trace_id

    def _is_stack_or_exception_line(self, line: str) -> bool:
        stripped = line.strip()
        if stripped.startswith("at "):
            return True
        if STACK_TRACE_RE.match(line):
            return True
        if stripped.startswith("Caused by:"):
            return True
        if EXCEPTION_LINE_RE.match(stripped):
            return True
        if "common frames omitted" in stripped:
            return True
        if stripped.startswith("MULTIEXCEPTION"):
            return True
        return False

    def _parse_timestamp_value(self, value: str) -> datetime | None:
        normalized = self._normalize_timestamp_value(value)
        for pattern in TIMESTAMP_PARSE_PATTERNS:
            try:
                return datetime.strptime(normalized, pattern)
            except ValueError:
                continue
        return None

    def _extract_timestamp(self, line: str) -> datetime | None:
        match = TIMESTAMP_SEARCH_RE.search(line)
        if not match:
            return None
        return self._parse_timestamp_value(match.group(1))

    def _normalize_timestamp_value(self, value: str) -> str:
        normalized = value.strip().replace("T", " ")
        normalized = re.sub(r"Z$", "", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"\s+[+-]\d{4}$", "", normalized)
        normalized = re.sub(r"[+-]\d{2}:?\d{2}$", "", normalized)
        normalized = re.sub(r"(\d{2}:\d{2}:\d{2})\.(\d+)", r"\1,\2", normalized)
        return normalized.strip()

    def _extract_level(self, line: str) -> str | None:
        bracket_match = BRACKET_LEVEL_RE.match(line)
        if bracket_match:
            return self._normalize_level(bracket_match.group(1))

        match = LEVEL_RE.search(line)
        if not match:
            return None
        return self._normalize_level(match.group(1))

    def _normalize_level(self, level: str) -> str:
        upper = level.upper()
        if upper == "WARN":
            return "WARNING"
        return upper

    def _extract_logger(self, line: str) -> str | None:
        structured = STRUCTURED_LOG_RE.match(line)
        if structured and structured.group("logger"):
            return structured.group("logger")

        for match in re.finditer(r"\[([^\]]+)\]", line):
            candidate = match.group(1).strip()
            if not candidate:
                continue
            if candidate.lower() in LOGGER_BRACKET_SKIP:
                continue
            if re.match(r"^\d{4}-\d{2}-\d{2}", candidate):
                continue
            if candidate.startswith("T-") and " - " in line:
                continue
            if re.match(r"^[A-Za-z][A-Za-z0-9_$]*(?:Impl|Handler|Resource|View|Factory|Executor|Dao|Util|Orchestrator|Listener)?$", candidate):
                return candidate
            if "." in candidate and re.match(r"^[A-Za-z0-9_.]+$", candidate):
                return candidate

        match = re.search(
            r"(?:\[)?(?P<logger>[A-Za-z0-9_.-]+(?:Logger|LOGGER|loger|logger))(?:\])?",
            line,
        )
        if match and match.group("logger"):
            return match.group("logger")
        return None

    def _extract_thread_name(self, line: str) -> str | None:
        structured = STRUCTURED_LOG_RE.match(line)
        if structured:
            return structured.group("thread").strip()

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

        pool_match = re.search(r"\[(?P<name>(?:pool|hystrix|dw)-[^\]]+)\]", line, re.IGNORECASE)
        if pool_match:
            return pool_match.group("name")
        return None

    def _extract_trace_id(self, line: str) -> str | None:
        match = TRACE_ID_RE.search(line)
        if not match:
            return None
        trace_id = match.group(1).strip()
        if trace_id == "_default_":
            return None
        return trace_id

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
        ref_match = REQUEST_REF_RE.search(line)
        if ref_match:
            request_id = ref_match.group(1).strip()
            if request_id and request_id != "_default_":
                return request_id

        for pattern in REQUEST_ID_PATTERNS:
            match = pattern.search(line)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        return None

    def _clean_message(self, line: str) -> str:
        structured = STRUCTURED_LOG_RE.match(line)
        if structured:
            message = (structured.group("message") or "").strip()
            return message

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
            r"^(?:INFO|WARN|WARNING|ERROR|DEBUG|TRACE|CRITICAL|FATAL)\s+\[[^\]]+\]\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(
            r"\s+\b(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL|TRACE)\b.*$",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        return cleaned.strip()
