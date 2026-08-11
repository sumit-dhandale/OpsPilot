from __future__ import annotations

import argparse
import json

from opspilot.services.analysis_service import AnalysisService


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a single log file with LLM-first incident triage.")
    parser.add_argument("file_path", help="Path to the .log or .txt file to analyze.")
    parser.add_argument("--model", default=None, help="LLM model name when OPENAI_API_KEY is set.")
    parser.add_argument(
        "--llm-off",
        action="store_true",
        help="Skip LLM analysis and use static heuristic fallback only.",
    )
    args = parser.parse_args()

    service = AnalysisService(model_name=args.model, disable_llm=args.llm_off)
    report = service.analyze_file(args.file_path)
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
