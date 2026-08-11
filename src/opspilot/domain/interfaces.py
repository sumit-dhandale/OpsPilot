"""Protocol definitions for loosely coupled agent components."""

from __future__ import annotations

from typing import Any, Protocol

from opspilot.domain.models import LogEntry, LogEvidenceBundle, StructuredReport


class FileLoaderProtocol(Protocol):
    def load(self, file_path: str) -> str: ...


class LogParserProtocol(Protocol):
    def parse(self, content: str) -> list[LogEntry]: ...


class EvidenceBuilderProtocol(Protocol):
    def build(self, entries: list[LogEntry]) -> LogEvidenceBundle: ...


class LLMAnalyzerProtocol(Protocol):
    def analyze(self, evidence: LogEvidenceBundle) -> StructuredReport: ...


class StaticAnalyzerProtocol(Protocol):
    def analyze(self, entries: list[LogEntry]) -> StructuredReport: ...


class LLMClientProtocol(Protocol):
    def generate(self, prompt: str) -> str: ...

    def generate_json(self, prompt: str) -> dict[str, Any]: ...
