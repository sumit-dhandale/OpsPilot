from __future__ import annotations

import argparse
import json

from opspilot.services.analysis_service import AnalysisService


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a single log file for operational insights.")
    parser.add_argument("file_path", help="Path to a .log or .txt file to analyze.")
    args = parser.parse_args()

    service = AnalysisService()
    report = service.analyze_file(args.file_path)

    print(json.dumps(report.__dict__, indent=2, default=str))


if __name__ == "__main__":
    main()
