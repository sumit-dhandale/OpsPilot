from opspilot.parsers.log_parser import LogParser


def test_parse_common_log_line():
    content = "2024-01-01 10:00:00,123 INFO Application started\n"
    entries = LogParser().parse(content)

    assert len(entries) == 1
    assert entries[0].level == "INFO"
    assert "Application started" in entries[0].message
    assert entries[0].timestamp is not None


def test_parse_error_message():
    content = "2024-01-01 10:05:30 ERROR Database connection timeout\n"
    entries = LogParser().parse(content)

    assert entries[0].level == "ERROR"
    assert "Database connection timeout" in entries[0].message
