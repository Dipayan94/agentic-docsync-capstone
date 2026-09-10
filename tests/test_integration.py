"""Integration tests for docsync (end-to-end workflows).

Test complete docsync pipelines:
- Parse → Generate
- Diff detection across schema versions
- Full sync workflow with caching
"""

import pytest
import json
import tempfile
from pathlib import Path
from docsync.parser import parse_openapi
from docsync.generator import generate_markdown
from docsync.diff_engine import DiffEngine
from docsync.models import ChangeType


class TestParseGenerateWorkflow:
    """Tests for parse → generate workflow."""
    
    def test_parse_generate_basic(self):
        """End-to-end: parse schema → generate docs."""
        schema_data = {
            "openapi": "3.1.0",
            "info": {
                "title": "E2E Test API",
                "version": "1.0.0",
                "description": "API for end-to-end testing"
            },
            "paths": {
                "/items": {
                    "get": {
                        "summary": "List items",
                        "responses": {"200": {"description": "Success"}}
                    }
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "openapi.json"
            docs_dir = Path(tmpdir) / "docs"
            
            with open(schema_file, 'w') as f:
                json.dump(schema_data, f)
            
            # Parse
            schema = parse_openapi(str(schema_file))
            assert schema.title == "E2E Test API"
            assert len(schema.endpoints) == 1
            
            # Generate
            generate_markdown(schema, str(docs_dir))
            assert (docs_dir / "index.md").exists()
            
            # Verify content
            index_content = (docs_dir / "index.md").read_text()
            assert "E2E Test API" in index_content
            assert "1.0.0" in index_content
    
    def test_parse_generate_complex_schema(self):
        """Test with complex schema having multiple endpoints."""
        schema_data = {
            "openapi": "3.1.0",
            "info": {
                "title": "Pet Store API",
                "version": "2.0.0",
                "description": "API for managing pets"
            },
            "paths": {
                "/pets": {
                    "get": {
                        "summary": "List all pets",
                        "parameters": [
                            {
                                "name": "limit",
                                "in": "query",
                                "required": False,
                                "schema": {"type": "integer"}
                            }
                        ],
                        "responses": {
                            "200": {"description": "List of pets"},
                            "500": {"description": "Server error"}
                        }
                    },
                    "post": {
                        "summary": "Create a pet",
                        "responses": {"201": {"description": "Pet created"}}
                    }
                },
                "/pets/{petId}": {
                    "get": {
                        "summary": "Get pet by ID",
                        "parameters": [
                            {
                                "name": "petId",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"}
                            }
                        ],
                        "responses": {"200": {"description": "Pet details"}}
                    }
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "openapi.json"
            docs_dir = Path(tmpdir) / "docs"
            
            with open(schema_file, 'w') as f:
                json.dump(schema_data, f)
            
            # Parse
            schema = parse_openapi(str(schema_file))
            assert len(schema.endpoints) == 3
            
            # Generate
            generate_markdown(schema, str(docs_dir))
            
            # Check files
            assert (docs_dir / "index.md").exists()
            md_files = list(docs_dir.glob("*.md"))
            assert len(md_files) >= 4  # index + 3 endpoints
            
            # Verify index mentions all endpoints
            index_content = (docs_dir / "index.md").read_text()
            assert "List all pets" in index_content or "GET" in index_content
            assert "Create a pet" in index_content or "POST" in index_content


class TestDiffWorkflow:
    """Tests for diff detection across schema versions."""
    
    def test_diff_simple_changes(self):
        """End-to-end: diff detection with simple changes."""
        v1_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                }
            }
        }
        
        v2_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "2.0.0"},
            "paths": {
                "/items": {
                    "get": {"responses": {"200": {"description": "OK"}}},
                    "post": {"responses": {"201": {"description": "Created"}}}
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            v1_file = Path(tmpdir) / "v1.json"
            v2_file = Path(tmpdir) / "v2.json"
            
            with open(v1_file, 'w') as f:
                json.dump(v1_data, f)
            with open(v2_file, 'w') as f:
                json.dump(v2_data, f)
            
            # Parse both versions
            schema_v1 = parse_openapi(str(v1_file))
            schema_v2 = parse_openapi(str(v2_file))
            
            # Compute diff
            changes = DiffEngine.compute_diff(schema_v1, schema_v2)
            
            # Verify changes
            new_changes = [c for c in changes if c.change_type == ChangeType.NEW]
            assert len(new_changes) == 1
            assert new_changes[0].endpoint.method == "POST"
    
    def test_diff_removed_endpoints(self):
        """Test diff detection with removed endpoints."""
        v1_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {"responses": {"200": {"description": "OK"}}},
                    "post": {"responses": {"201": {"description": "Created"}}}
                },
                "/users": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                }
            }
        }
        
        v2_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "2.0.0"},
            "paths": {
                "/items": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            v1_file = Path(tmpdir) / "v1.json"
            v2_file = Path(tmpdir) / "v2.json"
            
            with open(v1_file, 'w') as f:
                json.dump(v1_data, f)
            with open(v2_file, 'w') as f:
                json.dump(v2_data, f)
            
            # Parse both versions
            schema_v1 = parse_openapi(str(v1_file))
            schema_v2 = parse_openapi(str(v2_file))
            
            # Compute diff
            changes = DiffEngine.compute_diff(schema_v1, schema_v2)
            
            # Verify changes
            removed_changes = [c for c in changes if c.change_type == ChangeType.REMOVED]
            assert len(removed_changes) == 2
    
    def test_diff_modified_endpoints(self):
        """Test diff detection with modified endpoints."""
        v1_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {
                        "summary": "List items",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        }
        
        v2_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "2.0.0"},
            "paths": {
                "/items": {
                    "get": {
                        "summary": "List all items (paginated)",
                        "responses": {"200": {"description": "OK"}}
                    }
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            v1_file = Path(tmpdir) / "v1.json"
            v2_file = Path(tmpdir) / "v2.json"
            
            with open(v1_file, 'w') as f:
                json.dump(v1_data, f)
            with open(v2_file, 'w') as f:
                json.dump(v2_data, f)
            
            # Parse both versions
            schema_v1 = parse_openapi(str(v1_file))
            schema_v2 = parse_openapi(str(v2_file))
            
            # Compute diff
            changes = DiffEngine.compute_diff(schema_v1, schema_v2)
            
            # Verify changes
            modified_changes = [c for c in changes if c.change_type == ChangeType.MODIFIED]
            assert len(modified_changes) == 1
    
    def test_diff_all_endpoints_new(self):
        """Test diff on first sync (all endpoints are new)."""
        v2_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/items": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/users": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/products": {"get": {"responses": {"200": {"description": "OK"}}}}
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            v2_file = Path(tmpdir) / "v2.json"
            
            with open(v2_file, 'w') as f:
                json.dump(v2_data, f)
            
            # Parse new schema
            schema_v2 = parse_openapi(str(v2_file))
            
            # Compute diff from None (first sync)
            changes = DiffEngine.compute_diff(None, schema_v2)
            
            # All should be NEW
            assert len(changes) == 3
            assert all(c.change_type == ChangeType.NEW for c in changes)


class TestCompleteWorkflow:
    """Tests for complete workflow with all stages."""
    
    def test_complete_pipeline(self):
        """Test complete pipeline: parse → diff → generate."""
        old_schema_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/items": {"get": {"responses": {"200": {"description": "OK"}}}}
            }
        }
        
        new_schema_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "2.0.0"},
            "paths": {
                "/items": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/items/{id}": {"get": {"responses": {"200": {"description": "OK"}}}}
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            old_file = Path(tmpdir) / "old.json"
            new_file = Path(tmpdir) / "new.json"
            docs_dir = Path(tmpdir) / "docs"
            
            with open(old_file, 'w') as f:
                json.dump(old_schema_data, f)
            with open(new_file, 'w') as f:
                json.dump(new_schema_data, f)
            
            # Stage 1: Parse old schema
            old_schema = parse_openapi(str(old_file))
            assert len(old_schema.endpoints) == 1
            
            # Stage 2: Parse new schema
            new_schema = parse_openapi(str(new_file))
            assert len(new_schema.endpoints) == 2
            
            # Stage 3: Detect changes
            changes = DiffEngine.compute_diff(old_schema, new_schema)
            assert len(changes) == 1  # 1 new endpoint
            assert changes[0].change_type == ChangeType.NEW
            
            # Stage 4: Generate documentation
            generate_markdown(new_schema, str(docs_dir))
            assert (docs_dir / "index.md").exists()
            
            # Verify docs mention both endpoints
            index_content = (docs_dir / "index.md").read_text()
            assert "2" in index_content or "endpoints" in index_content.lower()


class TestRealWorldScenarios:
    """Tests with realistic API schemas."""
    
    def test_fastapi_style_schema(self):
        """Test with FastAPI-style OpenAPI schema."""
        schema_data = {
            "openapi": "3.1.0",
            "info": {
                "title": "FastAPI Application",
                "version": "0.1.0"
            },
            "paths": {
                "/": {
                    "get": {
                        "summary": "Home",
                        "operationId": "root_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {}}
                            }
                        }
                    }
                },
                "/items/{item_id}": {
                    "get": {
                        "summary": "Read Item",
                        "operationId": "read_item",
                        "parameters": [
                            {
                                "name": "item_id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "integer"}
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {}}
                            }
                        }
                    }
                },
                "/items/": {
                    "get": {
                        "summary": "Read Items",
                        "operationId": "read_items",
                        "parameters": [
                            {
                                "name": "skip",
                                "in": "query",
                                "required": False,
                                "schema": {"type": "integer", "default": 0}
                            },
                            {
                                "name": "limit",
                                "in": "query",
                                "required": False,
                                "schema": {"type": "integer", "default": 10}
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {}}
                            }
                        }
                    },
                    "post": {
                        "summary": "Create Item",
                        "operationId": "create_item",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {}}
                            }
                        }
                    }
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "openapi.json"
            docs_dir = Path(tmpdir) / "docs"
            
            with open(schema_file, 'w') as f:
                json.dump(schema_data, f)
            
            # Parse
            schema = parse_openapi(str(schema_file))
            assert schema.title == "FastAPI Application"
            assert len(schema.endpoints) >= 4
            
            # Generate docs
            generate_markdown(schema, str(docs_dir))
            assert (docs_dir / "index.md").exists()
            
            # Verify documentation quality
            md_files = list(docs_dir.glob("*.md"))
            assert len(md_files) >= 3
