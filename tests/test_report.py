import json

from docsync.models import Endpoint
from docsync.report import build_report, format_report_json, format_report_markdown


def test_build_report_marks_all_endpoints_as_added():
    endpoints = [Endpoint(path="/a", method="GET"), Endpoint(path="/b", method="POST")]
    report = build_report(endpoints)

    assert report.added == [{"method": "GET", "path": "/a"}, {"method": "POST", "path": "/b"}]
    assert report.modified == []
    assert report.removed == []


def test_build_report_empty_endpoints():
    report = build_report([])
    assert report.added == []
    assert report.total == 0


def test_format_report_markdown_shows_counts():
    report = build_report([Endpoint(path="/a", method="GET")])
    text = format_report_markdown(report)
    assert "Added: 1" in text
    assert "Modified: 0" in text
    assert "Removed: 0" in text


def test_format_report_json_has_added_modified_removed_keys():
    report = build_report([Endpoint(path="/a", method="GET")])
    data = json.loads(format_report_json(report))
    assert set(data.keys()) == {"added", "modified", "removed"}
    assert data["added"] == [{"method": "GET", "path": "/a"}]
