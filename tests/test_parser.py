"""Test suite for docsync.parser

Test coverage for BLOCKER #1 (Schema Validation):
- SchemaValidator validates OpenAPI 3.0/3.1 structure
- Explicit validation errors for malformed input
- OpenAPI parser extracts endpoints from valid schemas
- Error handling for invalid JSON and missing fields
"""

import pytest
import json
import tempfile
from pathlib import Path
from docsync.parser import OpenAPIParser, SchemaValidator, parse_openapi
from docsync.models import ValidationError


class TestSchemaValidator:
    """Tests for OpenAPI schema validation (BLOCKER #1)."""
    
    def test_validate_minimal_valid_schema(self):
        """Test validation of minimal valid OpenAPI schema."""
        schema = {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {}
        }
        errors = SchemaValidator.validate_openapi_structure(schema)
        assert len(errors) == 0
    
    def test_validate_missing_openapi_version(self):
        """Test validation fails when 'openapi' field is missing."""
        schema = {"info": {"title": "Test", "version": "1.0.0"}, "paths": {}}
        errors = SchemaValidator.validate_openapi_structure(schema)
        assert len(errors) > 0
        assert any("openapi" in str(e).lower() for e in errors)
    
    def test_validate_unsupported_openapi_version(self):
        """Test validation fails with unsupported OpenAPI version."""
        schema = {
            "openapi": "2.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {}
        }
        errors = SchemaValidator.validate_openapi_structure(schema)
        assert len(errors) > 0
    
    def test_validate_missing_info(self):
        """Test validation fails when 'info' field is missing."""
        schema = {"openapi": "3.1.0", "paths": {}}
        errors = SchemaValidator.validate_openapi_structure(schema)
        assert len(errors) > 0
        assert any("info" in str(e).lower() for e in errors)
    
    def test_validate_invalid_info_type(self):
        """Test validation fails when 'info' is not an object."""
        schema = {"openapi": "3.1.0", "info": "not an object", "paths": {}}
        errors = SchemaValidator.validate_openapi_structure(schema)
        assert len(errors) > 0
    
    def test_validate_invalid_paths_type(self):
        """Test validation fails when 'paths' is not an object."""
        schema = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": ["not", "an", "object"]
        }
        errors = SchemaValidator.validate_openapi_structure(schema)
        assert len(errors) > 0
    
    def test_validate_valid_openapi_3_0(self):
        """Test validation accepts OpenAPI 3.0.x."""
        schema = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {}
        }
        errors = SchemaValidator.validate_openapi_structure(schema)
        assert len(errors) == 0
    
    def test_validate_valid_openapi_3_1(self):
        """Test validation accepts OpenAPI 3.1.x."""
        schema = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {}
        }
        errors = SchemaValidator.validate_openapi_structure(schema)
        assert len(errors) == 0
    
    def test_validate_with_valid_paths(self):
        """Test validation passes with valid paths object."""
        schema = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                }
            }
        }
        errors = SchemaValidator.validate_openapi_structure(schema)
        assert len(errors) == 0


class TestOpenAPIParser:
    """Tests for OpenAPI parser (BLOCKER #1 validation)."""
    
    def test_parse_minimal_schema(self):
        """Test parsing minimal valid schema."""
        schema_data = {
            "openapi": "3.1.0",
            "info": {
                "title": "Minimal API",
                "version": "1.0.0",
                "description": "Test API"
            },
            "paths": {
                "/items": {
                    "get": {
                        "summary": "List items",
                        "responses": {
                            "200": {"description": "Success"}
                        }
                    }
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "openapi.json"
            with open(schema_file, 'w') as f:
                json.dump(schema_data, f)
            
            schema = parse_openapi(str(schema_file))
            assert schema.title == "Minimal API"
            assert schema.version == "1.0.0"
            assert len(schema.endpoints) == 1
            assert schema.endpoints[0].method == "GET"
            assert schema.endpoints[0].path == "/items"
    
    def test_parse_empty_paths(self):
        """Test parsing schema with no endpoints."""
        schema_data = {
            "openapi": "3.1.0",
            "info": {"title": "Empty API", "version": "1.0.0"},
            "paths": {}
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "openapi.json"
            with open(schema_file, 'w') as f:
                json.dump(schema_data, f)
            
            schema = parse_openapi(str(schema_file))
            assert len(schema.endpoints) == 0
    
    def test_parse_multiple_methods(self):
        """Test parsing multiple HTTP methods on same path."""
        schema_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {"responses": {"200": {"description": "List items"}}},
                    "post": {"responses": {"201": {"description": "Item created"}}}
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "openapi.json"
            with open(schema_file, 'w') as f:
                json.dump(schema_data, f)
            
            schema = parse_openapi(str(schema_file))
            assert len(schema.endpoints) == 2
            methods = {ep.method for ep in schema.endpoints}
            assert "GET" in methods
            assert "POST" in methods
    
    def test_parse_with_parameters(self):
        """Test parsing endpoint with parameters."""
        schema_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/items/{id}": {
                    "get": {
                        "summary": "Get item",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "description": "Item ID",
                                "schema": {"type": "integer"}
                            }
                        ],
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "openapi.json"
            with open(schema_file, 'w') as f:
                json.dump(schema_data, f)
            
            schema = parse_openapi(str(schema_file))
            ep = schema.endpoints[0]
            assert len(ep.parameters) == 1
            assert ep.parameters[0].name == "id"
            assert ep.parameters[0].param_type == "path"
            assert ep.parameters[0].required is True
            assert ep.parameters[0].schema_type == "integer"
    
    def test_parse_with_multiple_parameters(self):
        """Test parsing endpoint with multiple parameters."""
        schema_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {
                        "parameters": [
                            {"name": "id", "in": "query", "required": True, "schema": {"type": "integer"}},
                            {"name": "filter", "in": "query", "required": False, "schema": {"type": "string"}},
                            {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}}
                        ],
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "openapi.json"
            with open(schema_file, 'w') as f:
                json.dump(schema_data, f)
            
            schema = parse_openapi(str(schema_file))
            ep = schema.endpoints[0]
            assert len(ep.parameters) == 3
    
    def test_parse_with_responses(self):
        """Test parsing endpoint with multiple responses."""
        schema_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {"application/json": {}}
                            },
                            "404": {"description": "Not found"},
                            "500": {"description": "Server error"}
                        }
                    }
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "openapi.json"
            with open(schema_file, 'w') as f:
                json.dump(schema_data, f)
            
            schema = parse_openapi(str(schema_file))
            ep = schema.endpoints[0]
            assert len(ep.responses) == 3
            status_codes = {r.status_code for r in ep.responses}
            assert "200" in status_codes
            assert "404" in status_codes
            assert "500" in status_codes
    
    def test_parse_with_tags(self):
        """Test parsing endpoint with tags."""
        schema_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {
                        "tags": ["items", "inventory"],
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "openapi.json"
            with open(schema_file, 'w') as f:
                json.dump(schema_data, f)
            
            schema = parse_openapi(str(schema_file))
            ep = schema.endpoints[0]
            assert len(ep.tags) == 2
            assert "items" in ep.tags
    
    def test_parse_malformed_json(self):
        """Test that malformed JSON raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "bad.json"
            schema_file.write_text("{invalid json content")
            
            with pytest.raises(ValueError, match="Invalid JSON"):
                parse_openapi(str(schema_file))
    
    def test_parse_missing_file(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_openapi("/nonexistent/path/openapi.json")
    
    def test_parse_invalid_schema_structure(self):
        """Test that invalid OpenAPI structure raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "openapi.json"
            # Missing required 'openapi' field
            with open(schema_file, 'w') as f:
                json.dump({"info": {"title": "Test"}}, f)
            
            with pytest.raises(ValueError, match="Invalid OpenAPI"):
                parse_openapi(str(schema_file))
    
    def test_parse_with_description(self):
        """Test parsing endpoint with description."""
        schema_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {
                        "summary": "List all items",
                        "description": "Returns a paginated list of all available items",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "openapi.json"
            with open(schema_file, 'w') as f:
                json.dump(schema_data, f)
            
            schema = parse_openapi(str(schema_file))
            ep = schema.endpoints[0]
            assert ep.summary == "List all items"
            assert "paginated" in ep.description
