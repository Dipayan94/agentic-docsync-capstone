"""Tests for OpenAPI schema validation and endpoint extraction."""

import json
import pytest
from pathlib import Path
from docsync import ValidationError
from docsync.openapi import load_openapi_schema, extract_endpoints


def test_valid_schema_loads_successfully(tmp_path):
    """Test that a valid OpenAPI 3.x schema loads without errors."""
    schema_file = tmp_path / "valid_schema.json"
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
    
    # Should not raise an exception
    schema = load_openapi_schema(str(schema_file))
    assert schema["openapi"] == "3.0.0"
    assert "paths" in schema


def test_invalid_json_raises_validation_error(tmp_path):
    """Test that invalid JSON content raises ValidationError."""
    schema_file = tmp_path / "invalid.json"
    schema_file.write_text("{invalid json content")
    
    with pytest.raises(ValidationError) as exc_info:
        load_openapi_schema(str(schema_file))
    assert "Invalid JSON" in str(exc_info.value)


def test_missing_openapi_field_raises_validation_error(tmp_path):
    """Test that missing 'openapi' field raises ValidationError."""
    schema_file = tmp_path / "no_openapi.json"
    schema_data = {
        "info": {"title": "Test API"},
        "paths": {}
    }
    schema_file.write_text(json.dumps(schema_data))
    
    with pytest.raises(ValidationError) as exc_info:
        load_openapi_schema(str(schema_file))
    assert "openapi" in str(exc_info.value).lower()


def test_missing_paths_field_raises_validation_error(tmp_path):
    """Test that missing 'paths' field raises ValidationError."""
    schema_file = tmp_path / "no_paths.json"
    schema_data = {
        "openapi": "3.0.0",
        "info": {"title": "Test API"}
    }
    schema_file.write_text(json.dumps(schema_data))
    
    with pytest.raises(ValidationError) as exc_info:
        load_openapi_schema(str(schema_file))
    assert "paths" in str(exc_info.value).lower()


def test_non_3x_version_raises_validation_error(tmp_path):
    """Test that non-3.x OpenAPI versions raise ValidationError."""
    schema_file = tmp_path / "wrong_version.json"
    schema_data = {
        "openapi": "2.0.0",
        "info": {"title": "Test API"},
        "paths": {}
    }
    schema_file.write_text(json.dumps(schema_data))
    
    with pytest.raises(ValidationError) as exc_info:
        load_openapi_schema(str(schema_file))
    assert "3.x" in str(exc_info.value) or "3." in str(exc_info.value)


def test_extract_endpoints_deterministic_ordering(tmp_path):
    """Test that endpoints are extracted in deterministic order (path, then method)."""
    schema_file = tmp_path / "multi_endpoint.json"
    schema_data = {
        "openapi": "3.0.0",
        "info": {"title": "Test API"},
        "paths": {
            "/users": {
                "post": {"summary": "Create user"},
                "get": {"summary": "List users"}
            },
            "/items": {
                "get": {"summary": "List items"},
                "post": {"summary": "Create item"}
            }
        }
    }
    schema_file.write_text(json.dumps(schema_data))
    
    schema = load_openapi_schema(str(schema_file))
    endpoints = extract_endpoints(schema)
    
    # Should be sorted by path first, then method
    assert len(endpoints) == 4
    assert endpoints[0].path == "/items" and endpoints[0].method == "GET"
    assert endpoints[1].path == "/items" and endpoints[1].method == "POST"
    assert endpoints[2].path == "/users" and endpoints[2].method == "GET"
    assert endpoints[3].path == "/users" and endpoints[3].method == "POST"
