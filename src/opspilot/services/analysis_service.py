from __future__ import annotations

import ast
import os
import re
from pathlib import Path

from opspilot.config import DEFAULT_SETTINGS
from opspilot.domain.models import AnalysisReport
from opspilot.loaders.file_loader import FileLoader
from opspilot.llm.llm_client import FallbackLLMClient, LLMClient, OpenAICompatibleLLMClient
from opspilot.parsers.log_parser import LogParser


class AnalysisService:
    """Single-file analysis service for code and logs."""

    def __init__(
        self,
        file_loader: FileLoader | None = None,
        parser: LogParser | None = None,
        llm_client: LLMClient | None = None,
        model_name: str | None = None,
        disable_llm: bool = False,
    ) -> None:
        self.file_loader = file_loader or FileLoader(allowed_extensions=DEFAULT_SETTINGS.allowed_extensions, max_file_size_mb=DEFAULT_SETTINGS.max_file_size_mb)
        self.parser = parser or LogParser()
        self.llm_client = llm_client
        if self.llm_client is None and not disable_llm:
            if os.getenv("OPENAI_API_KEY"):
                self.llm_client = OpenAICompatibleLLMClient(model=model_name or DEFAULT_SETTINGS.llm_model)
            else:
                self.llm_client = FallbackLLMClient()

    def analyze_file(self, file_path: str) -> AnalysisReport:
        content = self.file_loader.load(file_path)
        suffix = Path(file_path).suffix.lower()

        if suffix in {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".cs", ".rb", ".php"}:
            return self._analyze_code_file(file_path, content)

        return self._analyze_log_file(file_path, content)

    def _analyze_code_file(self, file_path: str, content: str) -> AnalysisReport:
        language = self._detect_language(file_path)
        lines = content.splitlines()
        functions = self._extract_python_functions(content) if language == "python" else self._extract_generic_functions(content)
        classes = self._extract_python_classes(content) if language == "python" else self._extract_generic_classes(content)
        imports = self._extract_imports(content)

        summary = self._build_code_summary(language, functions, classes, imports)
        issues = self._detect_code_issues(content)
        recommendations = self._build_code_recommendations(issues, functions, classes)

        result = AnalysisReport(
            kind="code",
            language=language,
            summary=summary,
            executive_summary=summary,
            purpose="This file appears to define reusable logic, structure, and processing flow for a specific application component.",
            structure={
                "line_count": len(lines),
                "functions": functions,
                "classes": classes,
                "dependencies": imports,
            },
            key_logic=self._extract_key_logic(content, functions),
            functions=functions,
            classes=classes,
            dependencies=imports,
            issues=issues,
            recommendations=recommendations,
            complexity=self._assess_code_complexity(len(functions), len(classes), len(lines)),
        )

        if self.llm_client is not None and hasattr(self.llm_client, "generate"):
            try:
                prompt = self._build_llm_prompt(result, "code")
                result["llm_summary"] = self.llm_client.generate(prompt)
            except Exception:
                result["llm_summary"] = "LLM enrichment unavailable; local analysis was used."

        return result

    def _analyze_log_file(self, file_path: str, content: str) -> AnalysisReport:
        entries = self.parser.parse(content)
        overview = self._summarize_log_entries(entries)

        issues = []
        for entry in entries:
            if entry.level in {"ERROR", "CRITICAL", "FATAL"}:
                issues.append({
                    "level": entry.level,
                    "message": entry.message,
                    "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                })

        patterns = []
        for token in ["retry", "timeout", "connection", "memory", "shutdown", "exception"]:
            if any(token in entry.message.lower() for entry in entries):
                patterns.append(token)

        recommendations = [
            "Review the earliest error and warning events in the log timeline.",
            "Check the affected dependency or service mentioned in the recurring failure messages.",
            "Verify recent configuration or deployment changes if the problem aligns with a rollout.",
        ]
        if patterns:
            recommendations.append(f"Prioritize investigation of the recurring pattern(s): {', '.join(patterns)}.")

        summary = self._build_log_summary(entries, issues)

        error_groups = []
        for error in self._extract_errors(entries):
            error_groups.append({
                "error_type": error,
                "occurrence_count": 1,
                "first_occurrence": None,
                "last_occurrence": None,
                "short_explanation": "Error event detected in the log.",
            })

        warning_groups = []
        for warning in self._extract_warnings(entries):
            warning_groups.append({
                "warning_type": warning,
                "occurrence_count": 1,
                "first_occurrence": None,
                "last_occurrence": None,
                "short_explanation": "Warning event detected in the log.",
            })

        log_overview = AnalysisReport(
            time_range=overview.get("time_range"),
            total_lines_processed=len(entries),
            log_levels_observed=overview.get("levels", []),
            major_components=[],
            request_identifiers=[],
            thread_names=[],
        )

        result = AnalysisReport(
            kind="log",
            language="log",
            summary=summary,
            executive_summary=summary,
            purpose="This file appears to record application events, operational health, and execution status over time.",
            time_range=overview.get("time_range"),
            levels=overview.get("levels", []),
            important_events=self._extract_important_events(entries),
            errors=self._extract_errors(entries),
            warnings=self._extract_warnings(entries),
            patterns=patterns,
            issues=issues,
            recommendations=recommendations,
            complexity=self._assess_log_complexity(entries),
            log_overview=log_overview,
            timeline=self._extract_important_events(entries),
            error_analysis=error_groups,
            warning_analysis=warning_groups,
        )

        if self.llm_client is not None and hasattr(self.llm_client, "generate"):
            try:
                prompt = self._build_llm_prompt(result, "log")
                result["llm_summary"] = self.llm_client.generate(prompt)
            except Exception:
                result["llm_summary"] = "LLM enrichment unavailable; local analysis was used."

        return result

    def _detect_language(self, file_path: str) -> str:
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cs": "csharp",
            ".rb": "ruby",
            ".php": "php",
        }
        return mapping.get(Path(file_path).suffix.lower(), "text")

    def _extract_python_functions(self, content: str) -> list[str]:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return self._extract_generic_functions(content)

        functions = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)
        return sorted(set(functions))

    def _extract_python_classes(self, content: str) -> list[str]:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return self._extract_generic_classes(content)

        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
        return sorted(set(classes))

    def _extract_generic_functions(self, content: str) -> list[str]:
        return sorted(set(re.findall(r"(?:def|function|fn)\s+([A-Za-z0-9_]+)", content)))

    def _extract_generic_classes(self, content: str) -> list[str]:
        return sorted(set(re.findall(r"(?:class|interface)\s+([A-Za-z0-9_]+)", content)))

    def _extract_imports(self, content: str) -> list[str]:
        imports = re.findall(r"^(?:import|from)\s+([^\n]+)", content, flags=re.MULTILINE)
        return [imp.strip() for imp in imports if imp.strip()]

    def _detect_code_issues(self, content: str) -> list[str]:
        issues = []
        lower = content.lower()
        if "todo" in lower:
            issues.append("Contains TODO markers that may indicate unfinished work.")
        if "fixme" in lower:
            issues.append("Contains FIXME markers that suggest known unresolved issues.")
        if "raise" in lower and "except" in lower:
            issues.append("Error handling is present; inspect exception paths for correctness.")
        if "print(" in lower and "logging" not in lower:
            issues.append("Verbose print-based debugging may be a sign of limited observability.")
        if "pass" in lower and "todo" not in lower:
            issues.append("Some code paths may be intentionally unimplemented or incomplete.")
        if "except" in lower and "pass" in lower:
            issues.append("Exceptions may be swallowed without adequate handling or logging.")
        return issues[:6]

    def _build_code_summary(self, language: str, functions: list[str], classes: list[str], imports: list[str]) -> str:
        parts = [
            f"This appears to be a {language} file.",
        ]
        if functions:
            parts.append(f"It defines {len(functions)} function(s), including {', '.join(functions[:3]) if len(functions) > 1 else functions[0]}.")
        if classes:
            parts.append(f"It also includes {len(classes)} class(es): {', '.join(classes[:3])}.")
        if imports:
            parts.append(f"The file depends on {', '.join(imports[:3])}.")
        return " ".join(parts)

    def _extract_key_logic(self, content: str, functions: list[str]) -> list[str]:
        key_logic = []
        if not functions:
            key_logic.append("The file is mostly data or configuration oriented.")
            return key_logic

        for name in functions[:5]:
            key_logic.append(f"{name} is a likely entry point or helper for the file's main processing logic.")
        if "if " in content and "return" in content:
            key_logic.append("The file includes conditional branches and return paths, which likely determine processing flow.")
        return key_logic

    def _build_code_recommendations(self, issues: list[str], functions: list[str], classes: list[str]) -> list[str]:
        recommendations = []
        if issues:
            recommendations.append("Inspect the flagged error-handling and TODO/FIXME sections before making changes.")
        if functions:
            recommendations.append("Trace the main function entry points and validate their inputs and output contracts.")
        if classes:
            recommendations.append("Review the key classes for lifecycle and dependency assumptions.")
        if not recommendations:
            recommendations.append("Read the core function(s) first and validate the expected inputs/outputs before extending behavior.")
        return recommendations[:4]

    def _summarize_log_entries(self, entries: list) -> dict:
        levels = sorted({entry.level for entry in entries if entry.level})
        timestamps = [entry.timestamp for entry in entries if entry.timestamp is not None]
        time_range = None
        if timestamps:
            time_range = f"{min(timestamps).isoformat()} -> {max(timestamps).isoformat()}"
        return {"levels": levels, "time_range": time_range}

    def _extract_important_events(self, entries: list) -> list[str]:
        events = []
        for entry in entries:
            if entry.level in {"ERROR", "WARNING", "CRITICAL", "FATAL"}:
                label = entry.level.lower()
                events.append(f"[{entry.timestamp.isoformat() if entry.timestamp else 'unknown'}] {label}: {entry.message[:180]}")
        return events[:8]

    def _extract_errors(self, entries: list) -> list[str]:
        return [entry.message for entry in entries if entry.level in {"ERROR", "CRITICAL", "FATAL"}][:8]

    def _extract_warnings(self, entries: list) -> list[str]:
        return [entry.message for entry in entries if entry.level == "WARNING"][:8]

    def _build_log_summary(self, entries: list, issues: list) -> str:
        if not entries:
            return "No log entries were found in the input file."

        levels = sorted({entry.level for entry in entries if entry.level})
        error_count = sum(1 for entry in entries if entry.level in {"ERROR", "CRITICAL", "FATAL"})
        warning_count = sum(1 for entry in entries if entry.level == "WARNING")

        summary = f"This log contains {len(entries)} lines and shows {', '.join(levels) if levels else 'no explicit levels'} across the execution."
        if error_count:
            summary += f" It includes {error_count} error(s) and {warning_count} warning(s)."
        else:
            summary += " It appears to be mostly healthy, with no major error entries detected."
        if issues:
            summary += " The most notable issue is a failure path around the error message(s) recorded in the file."
        return summary

    def _assess_code_complexity(self, function_count: int, class_count: int, line_count: int) -> str:
        score = function_count + class_count + (line_count // 150)
        if score >= 8:
            return "high"
        if score >= 4:
            return "medium"
        return "low"

    def _assess_log_complexity(self, entries: list) -> str:
        total = len(entries)
        if total > 1000:
            return "high"
        if total > 200:
            return "medium"
        return "low"

    def _build_llm_prompt(self, result: dict, kind: str) -> str:
        if kind == "code":
            return (
                "Analyze this file summary and produce a concise engineering explanation. "
                "Explain the file's main purpose, structure, important logic, dependencies, and any risks. "
                "Keep it concise but technical. "
                f"Input: {result}"
            )
        return (
            "Analyze this log summary and produce a concise incident readout. "
            "Describe the overall health, key events, warnings, errors, likely problem patterns, and recommended next steps. "
            "Use only evidence from the log and avoid speculation. "
            f"Input: {result}"
        )
