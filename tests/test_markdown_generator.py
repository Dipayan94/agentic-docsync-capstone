"""
Tests for markdown generator module.
"""
from pathlib import Path

from docsync.openapi_parser import load_openapi_schema, parse_endpoints
from docsync.markdown_generator import generate_markdown


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_generate_markdown_includes_methods_and_paths():
    """Test generated markdown includes method and path for endpoints."""
    schema_path = FIXTURES_DIR / "sample_openapi.json"
    schema = load_openapi_schema(str(schema_path))
    endpoints = parse_endpoints(schema)
    
    markdown = generate_markdown(endpoints)
    
    # Should contain both endpoints
    assert "GET /items" in markdown
    assert "POST /items/{item_name}/{quantity}" in markdown


def test_generate_markdown_includes_summary():
    """Test generated markdown includes endpoint summaries."""
    schema_path = FIXTURES_DIR / "sample_openapi.json"
    schema = load_openapi_schema(str(schema_path))
    endpoints = parse_endpoints(schema)
    
    markdown = generate_markdown(endpoints)
    
    # Should contain summaries
    assert "Get all items" in markdown
    assert "Create item with quantity" in markdown


def test_generate_markdown_includes_parameters():
    """Test generated markdown includes parameters section."""
    schema_path = FIXTURES_DIR / "sample_openapi.json"
    schema = load_openapi_schema(str(schema_path))
    endpoints = parse_endpoints(schema)
    
    markdown = generate_markdown(endpoints)
    
    # Should contain parameter information
    assert "Parameters:" in markdown
    assert "limit" in markdown
    assert "query" in markdown


def test_generate_markdown_includes_responses():
    """Test generated markdown includes responses section."""
    schema_path = FIXTURES_DIR / "sample_openapi.json"
    schema = load_openapi_schema(str(schema_path))
    endpoints = parse_endpoints(schema)
    
    markdown = generate_markdown(endpoints)
    
    # Should contain response codes
    assert "Responses:" in markdown
    assert "200" in markdown
    assert "201" in markdown


def test_generate_markdown_empty_endpoints():
    """Test generating markdown with no endpoints."""
    markdown = generate_markdown([])
    
    assert "API Documentation" in markdown
    assert "No endpoints found" in markdown
