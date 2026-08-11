"""OpsPilot — LLM-first on-call log analysis agent."""

__version__ = "0.1.0"

__all__ = [
    "AnalysisService",
    "LogAnalysisAgent",
    "LogEntry",
    "StructuredReport",
    "AnalysisResult",
    "build_log_analysis_agent",
]

from opspilot.agent.log_analysis_agent import LogAnalysisAgent
from opspilot.domain.models import AnalysisResult, LogEntry, StructuredReport
from opspilot.factory import build_log_analysis_agent
from opspilot.services.analysis_service import AnalysisService
