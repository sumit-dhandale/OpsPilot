from __future__ import annotations

import argparse
import json

from opspilot.services.analysis_service import AnalysisService


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a single code or log file for quick engineering insight.")
    parser.add_argument("file_path", help="Path to the file to inspect.")
    parser.add_argument("--model", default=None, help="LLM model name to use when an API key is available.")
    parser.add_argument("--llm-off", action="store_true", help="Disable LLM enrichment and rely only on local analysis.")
    args = parser.parse_args()

    service = AnalysisService(model_name=args.model, disable_llm=args.llm_off)
    report = service.analyze_file(args.file_path)
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
