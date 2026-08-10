from opspilot.services.analysis_service import AnalysisService


def test_analysis_service_generates_report(tmp_path):
    log_file = tmp_path / "sample.log"
    log_file.write_text(
        "2024-01-01 10:00:00 INFO Application started\n"
        "2024-01-01 10:00:05 WARN Slow response observed\n"
        "2024-01-01 10:00:10 ERROR Database connection timeout\n",
        encoding="utf-8",
    )

    report = AnalysisService().analyze_file(str(log_file))

    assert report.executive_summary
    assert report.log_overview.total_lines_processed == 3
    assert report.timeline
    assert report.error_analysis
