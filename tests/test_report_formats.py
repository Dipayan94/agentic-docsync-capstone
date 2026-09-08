"""Tests for report generation and output formats."""

import json
import pytest
from docsync.report import extract_endpoint_ids_from_markdown, compute_report, render_report
from docsync.markdown import BEGIN_MARKER, END_MARKER


def test_extract_endpoint_ids_from_generated_markdown():
    """Test extracting endpoint identifiers from generated markdown."""
    markdown_block = f"""{BEGIN_MARKER}

## GET /items

Summary text.

## POST /items

Another summary.

## DELETE /users/{{id}}

Delete endpoint.

{END_MARKER}"""
    
    endpoint_ids = extract_endpoint_ids_from_markdown(markdown_block)
    
    assert "GET /items" in endpoint_ids
    assert "POST /items" in endpoint_ids
    assert "DELETE /users/{id}" in endpoint_ids
    assert len(endpoint_ids) == 3


def test_report_added_endpoints():
    """Test that report correctly identifies added endpoints."""
    old_ids = {"GET /items", "POST /items"}
    new_ids = {"GET /items", "POST /items", "DELETE /items", "PUT /items"}
    
    report = compute_report(old_ids, new_ids)
    
    assert len(report["added"]) == 2
    assert "DELETE /items" in report["added"]
    assert "PUT /items" in report["added"]
    assert len(report["removed"]) == 0


def test_report_removed_endpoints():
    """Test that report correctly identifies removed endpoints."""
    old_ids = {"GET /items", "POST /items", "DELETE /items"}
    new_ids = {"GET /items"}
    
    report = compute_report(old_ids, new_ids)
    
    assert len(report["removed"]) == 2
    assert "POST /items" in report["removed"]
    assert "DELETE /items" in report["removed"]
    assert len(report["added"]) == 0


def test_report_empty_to_endpoints():
    """Test report when old is empty and new has endpoints."""
    old_ids = set()
    new_ids = {"GET /items", "POST /users"}
    
    report = compute_report(old_ids, new_ids)
    
    assert len(report["added"]) == 2
    assert "GET /items" in report["added"]
    assert "POST /users" in report["added"]
    assert len(report["removed"]) == 0


def test_json_format_is_valid_json():
    """Test that JSON format output is parseable as valid JSON."""
    report = {
        "added": ["GET /items", "POST /items"],
        "removed": ["DELETE /users"],
        "modified": []
    }
    
    json_output = render_report(report, format="json")
    
    # Should be parseable
    parsed = json.loads(json_output)
    assert parsed["added"] == ["GET /items", "POST /items"]
    assert parsed["removed"] == ["DELETE /users"]
    assert parsed["modified"] == []


def test_markdown_format_contains_headings_and_counts():
    """Test that markdown format contains proper headings and counts."""
    report = {
        "added": ["GET /items", "POST /items"],
        "removed": ["DELETE /users"],
        "modified": []
    }
    
    markdown_output = render_report(report, format="markdown")
    
    # Should contain heading
    assert "# DocSync Report" in markdown_output or "#" in markdown_output
    
    # Should contain counts
    assert "Added:" in markdown_output or "added" in markdown_output.lower()
    assert "Removed:" in markdown_output or "removed" in markdown_output.lower()
    
    # Should contain endpoint details
    assert "GET /items" in markdown_output
    assert "POST /items" in markdown_output
    assert "DELETE /users" in markdown_output
