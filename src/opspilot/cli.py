from __future__ import annotations

import argparse
import json
import logging
import sys

from opspilot import __version__
from opspilot.exceptions import OpsPilotError
from opspilot.factory import build_log_analysis_agent
from opspilot.logging import configure_logging

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="opspilot",
        description="Analyze a single log file with an LLM-first on-call agent.",
    )
    parser.add_argument("file_path", help="Path to the .log or .txt file to analyze.")
    parser.add_argument("--model", default=None, help="LLM model name when OPENAI_API_KEY is set.")
    parser.add_argument(
        "--llm-off",
        action="store_true",
        help="Skip LLM analysis and use static heuristic fallback only.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    parser.add_argument("--version", action="version", version=f"opspilot {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging("DEBUG" if args.verbose else "INFO")

    try:
        agent = build_log_analysis_agent(disable_llm=args.llm_off, model_name=args.model)
        result = agent.analyze_file(args.file_path)
        print(json.dumps(result.to_output_dict(), indent=2, default=str))
        return 0
    except OpsPilotError as exc:
        logger.error("%s", exc)
        return 1
    except KeyboardInterrupt:
        logger.error("Interrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())
