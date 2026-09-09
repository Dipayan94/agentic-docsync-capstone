"""
Tests for OpenAPI parser module.
"""
import pytest
from pathlib import Path

from docsync.openapi_parser import load_openapi_schema, parse_endpoints
from docsync.exceptions import ValidationError, DocSyncError


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_load_valid_openapi_schema():
    """Test loading a valid OpenAPI schema."""
    schema_path = FIXTURES_DIR / "sample_openapi.json"
    schema = load_openapi_schema(str(schema_path))
    
    assert isinstance(schema, dict)
    assert "openapi" in schema
    assert "paths" in schema


def test_load_nonexistent_file():
    """Test loading a non-existent file raises DocSyncError."""
    with pytest.raises(DocSyncError) as exc_info:
        load_openapi_schema("nonexistent.json")
    assert "not found" in str(exc_info.value).lower()


def test_load_malformed_json():
    """Test loading malformed JSON raises ValidationError."""
    schema_path = FIXTURES_DIR / "malformed.json"
    with pytest.raises(ValidationError) as exc_info:
        load_openapi_schema(str(schema_path))
    assert "invalid json" in str(exc_info.value).lower()


def test_load_invalid_schema_missing_openapi():
    """Test schema missing 'openapi' field raises ValidationError."""
    schema_path = FIXTURES_DIR / "invalid_openapi.json"
    with pytest.raises(ValidationError) as exc_info:
        load_openapi_schema(str(schema_path))
    assert "openapi" in str(exc_info.value).lower()


def test_parse_endpoints_sorted():
    """Test endpoints are sorted by path then method."""
    schema_path = FIXTURES_DIR / "sample_openapi.json"
    schema = load_openapi_schema(str(schema_path))
    endpoints = parse_endpoints(schema)
    
    # Should have 2 endpoints: GET /items and POST /items/{item_name}/{quantity}
    assert len(endpoints) == 2
    
    # Check sorting: /items comes before /items/{item_name}/{quantity}
    assert endpoints[0].path == "/items"
    assert endpoints[0].method == "GET"
    assert endpoints[1].path == "/items/{item_name}/{quantity}"
    assert endpoints[1].method == "POST"


def test_parse_endpoints_parameters():
    """Test endpoint parameters are parsed correctly."""
    schema_path = FIXTURES_DIR / "sample_openapi.json"
    schema = load_openapi_schema(str(schema_path))
    endpoints = parse_endpoints(schema)
    
    # GET /items should have query parameter 'limit'
    get_items = endpoints[0]
    assert len(get_items.parameters) == 1
    assert get_items.parameters[0].name == "limit"
    assert get_items.parameters[0].location == "query"
    assert get_items.parameters[0].required is False
    assert get_items.parameters[0].schema_type == "integer"


def test_parse_endpoints_responses():
    """Test endpoint responses are parsed correctly."""
    schema_path = FIXTURES_DIR / "sample_openapi.json"
    schema = load_openapi_schema(str(schema_path))
    endpoints = parse_endpoints(schema)
    
    # POST endpoint should have 201 and 400 responses
    post_items = endpoints[1]
    assert len(post_items.responses) == 2
    status_codes = {r.status_code for r in post_items.responses}
    assert "201" in status_codes
    assert "400" in status_codes
