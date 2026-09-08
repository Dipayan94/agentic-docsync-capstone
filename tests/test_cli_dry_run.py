"""Tests for CLI behavior including dry-run and exit codes."""

import json
import pytest
from pathlib import Path
from docsync.cli import main
from docsync import ValidationError


def test_dry_run_does_not_write_output(tmp_path):
    """Test that --dry-run does not create or modify the output file."""
    schema_file = tmp_path / "schema.json"
    schema_data = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/items": {
                "get": {
                    "summary": "Get items",
                    "responses": {"200": {"description": "Success"}}
                }
            }
        }
    }
    schema_file.write_text(json.dumps(schema_data))
    
    docs_file = tmp_path / "docs.md"
    output_file = tmp_path / "output.md"
    
    # Run with dry-run
    exit_code = main([
        "sync",
        "--schema", str(schema_file),
        "--docs", str(docs_file),
        "--output", str(output_file),
        "--dry-run"
    ])
    
    # Should succeed
    assert exit_code == 0
    
    # Output file should NOT be created
    assert not output_file.exists()


def test_invalid_schema_path_returns_exit_code_1(tmp_path):
    """Test that invalid (non-existent) schema path returns exit code 1 or 2."""
    nonexistent_schema = tmp_path / "nonexistent.json"
    docs_file = tmp_path / "docs.md"
    output_file = tmp_path / "output.md"
    
    exit_code = main([
        "sync",
        "--schema", str(nonexistent_schema),
        "--docs", str(docs_file),
        "--output", str(output_file)
    ])
    
    # Should fail with validation error (exit code 2)
    assert exit_code == 2


def test_invalid_schema_json_returns_exit_code_2(tmp_path):
    """Test that invalid schema JSON/shape returns exit code 2."""
    schema_file = tmp_path / "invalid_schema.json"
    schema_file.write_text("{invalid json")
    
    docs_file = tmp_path / "docs.md"
    output_file = tmp_path / "output.md"
    
    exit_code = main([
        "sync",
        "--schema", str(schema_file),
        "--docs", str(docs_file),
        "--output", str(output_file)
    ])
    
    # Should return validation error exit code
    assert exit_code == 2


def test_missing_openapi_field_returns_exit_code_2(tmp_path):
    """Test that schema missing 'openapi' field returns exit code 2."""
    schema_file = tmp_path / "no_openapi.json"
    schema_data = {
        "info": {"title": "Test API"},
        "paths": {}
    }
    schema_file.write_text(json.dumps(schema_data))
    
    docs_file = tmp_path / "docs.md"
    output_file = tmp_path / "output.md"
    
    exit_code = main([
        "sync",
        "--schema", str(schema_file),
        "--docs", str(docs_file),
        "--output", str(output_file)
    ])
    
    assert exit_code == 2


def test_successful_sync_returns_exit_code_0(tmp_path):
    """Test that successful sync returns exit code 0."""
    schema_file = tmp_path / "schema.json"
    schema_data = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/items": {
                "get": {
                    "summary": "Get items",
                    "responses": {"200": {"description": "Success"}}
                }
            }
        }
    }
    schema_file.write_text(json.dumps(schema_data))
    
    docs_file = tmp_path / "docs.md"
    output_file = tmp_path / "output.md"
    
    exit_code = main([
        "sync",
        "--schema", str(schema_file),
        "--docs", str(docs_file),
        "--output", str(output_file)
    ])
    
    assert exit_code == 0
    assert output_file.exists()


def test_malformed_markers_in_docs_returns_exit_code_2(tmp_path):
    """Test that malformed markers in existing docs returns exit code 2."""
    schema_file = tmp_path / "schema.json"
    schema_data = {
        "openapi": "3.0.0",
        "info": {"title": "Test API"},
        "paths": {
            "/items": {"get": {"summary": "Get items"}}
        }
    }
    schema_file.write_text(json.dumps(schema_data))
    
    docs_file = tmp_path / "docs.md"
    docs_file.write_text("# Docs\n\n<!-- DOCSYNC:BEGIN GENERATED -->\n\nNo end marker!")
    
    output_file = tmp_path / "output.md"
    
    exit_code = main([
        "sync",
        "--schema", str(schema_file),
        "--docs", str(docs_file),
        "--output", str(output_file)
    ])
    
    # Should fail with validation error
    assert exit_code == 2
