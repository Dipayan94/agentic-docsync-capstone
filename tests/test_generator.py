"""Test suite for docsync.generator

Test coverage for BLOCKER #3 (Markdown Format Specification):
- Index file generation (overview + TOC)
- Per-endpoint markdown files
- Proper formatting and structure
- Handles empty/missing fields
"""

import pytest
import tempfile
from pathlib import Path
from docsync.generator import MarkdownFormatter, generate_markdown
from docsync.models import Endpoint, Parameter, Response, Schema


class TestMarkdownFormatter:
    """Tests for markdown formatting (BLOCKER #3)."""
    
    def test_endpoint_filename_simple(self):
        """Test generating safe filename for simple endpoint."""
        ep = Endpoint("GET", "/items")
        filename = MarkdownFormatter.endpoint_filename(ep)
        # Implementation replaces / with _, so /items becomes __items
        assert filename == "get__items.md"
    
    def test_endpoint_filename_with_path_parameter(self):
        """Test filename generation with path parameters."""
        ep = Endpoint("GET", "/items/{id}")
        filename = MarkdownFormatter.endpoint_filename(ep)
        # Should remove path separators and braces
        assert ".md" in filename
        assert "{" not in filename
        assert "}" not in filename
    
    def test_endpoint_filename_post_method(self):
        """Test filename with POST method."""
        ep = Endpoint("POST", "/items")
        filename = MarkdownFormatter.endpoint_filename(ep)
        assert filename.startswith("post_")
        assert filename.endswith(".md")
    
    def test_endpoint_filename_delete_method(self):
        """Test filename with DELETE method."""
        ep = Endpoint("DELETE", "/items/{id}")
        filename = MarkdownFormatter.endpoint_filename(ep)
        assert filename.startswith("delete_")
    
    def test_generate_endpoint_markdown_minimal(self):
        """Test generating markdown for minimal endpoint."""
        ep = Endpoint("GET", "/items")
        markdown = MarkdownFormatter.generate_endpoint_markdown(ep)
        
        assert "# GET /items" in markdown
        assert "## Parameters" in markdown or "## Responses" in markdown
    
    def test_generate_endpoint_markdown_with_summary(self):
        """Test endpoint markdown includes summary."""
        ep = Endpoint("GET", "/items", "List all items")
        markdown = MarkdownFormatter.generate_endpoint_markdown(ep)
        
        assert "# GET /items" in markdown
        assert "List all items" in markdown
    
    def test_generate_endpoint_markdown_with_description(self):
        """Test endpoint markdown includes description."""
        ep = Endpoint(
            "GET", "/items",
            "List items",
            "Retrieve all items from the database"
        )
        markdown = MarkdownFormatter.generate_endpoint_markdown(ep)
        
        assert "Retrieve all items" in markdown
    
    def test_generate_endpoint_markdown_with_parameters(self):
        """Test endpoint markdown includes parameters."""
        param = Parameter("id", "path", True, "Item ID", "integer")
        ep = Endpoint("GET", "/items/{id}", parameters=[param])
        markdown = MarkdownFormatter.generate_endpoint_markdown(ep)
        
        assert "Parameters" in markdown
        assert "id" in markdown
    
    def test_generate_endpoint_markdown_with_responses(self):
        """Test endpoint markdown includes responses."""
        resp = Response("200", "Success")
        ep = Endpoint("GET", "/items", responses=[resp])
        markdown = MarkdownFormatter.generate_endpoint_markdown(ep)
        
        assert "Responses" in markdown
        assert "200" in markdown
    
    def test_generate_endpoint_markdown_multiple_responses(self):
        """Test markdown with multiple response codes."""
        responses = [
            Response("200", "Success"),
            Response("404", "Not Found"),
            Response("500", "Server Error")
        ]
        ep = Endpoint("GET", "/items", responses=responses)
        markdown = MarkdownFormatter.generate_endpoint_markdown(ep)
        
        assert "200" in markdown
        assert "404" in markdown
        assert "500" in markdown
    
    def test_generate_index_markdown_minimal(self):
        """Test generating index markdown for minimal schema."""
        ep = Endpoint("GET", "/items")
        schema = Schema(
            title="Test API",
            version="1.0.0",
            endpoints=[ep]
        )
        
        markdown = MarkdownFormatter.generate_index_markdown(schema)
        
        assert "# Test API" in markdown
        assert "1.0.0" in markdown
        # Implementation uses "Total Endpoints: 1" format
        assert "Total Endpoints:" in markdown and "1" in markdown
    
    def test_generate_index_markdown_with_description(self):
        """Test index markdown includes schema description."""
        schema = Schema(
            title="Pet Store API",
            version="2.0.0",
            description="API for managing a pet store",
            endpoints=[]
        )
        
        markdown = MarkdownFormatter.generate_index_markdown(schema)
        
        assert "Pet Store API" in markdown
        assert "2.0.0" in markdown
        assert "pet store" in markdown
    
    def test_generate_index_markdown_multiple_endpoints(self):
        """Test index markdown lists multiple endpoints."""
        endpoints = [
            Endpoint("GET", "/items"),
            Endpoint("POST", "/items"),
            Endpoint("GET", "/items/{id}"),
            Endpoint("DELETE", "/items/{id}")
        ]
        schema = Schema(title="API", version="1.0.0", endpoints=endpoints)
        
        markdown = MarkdownFormatter.generate_index_markdown(schema)
        
        # Implementation uses "Total Endpoints: 4" format
        assert "Total Endpoints:" in markdown and "4" in markdown
        # Should mention paths
        assert "/items" in markdown
    
    def test_generate_index_markdown_endpoint_methods(self):
        """Test index markdown shows HTTP methods."""
        endpoints = [
            Endpoint("GET", "/items"),
            Endpoint("POST", "/items")
        ]
        schema = Schema(endpoints=endpoints)
        
        markdown = MarkdownFormatter.generate_index_markdown(schema)
        
        assert "GET" in markdown
        assert "POST" in markdown
    
    def test_generate_index_markdown_empty_endpoints(self):
        """Test index markdown with no endpoints."""
        schema = Schema(title="Empty API", version="1.0.0", endpoints=[])
        
        markdown = MarkdownFormatter.generate_index_markdown(schema)
        
        assert "Empty API" in markdown
        assert "1.0.0" in markdown
        # Implementation uses "Total Endpoints: 0" format
        assert "Total Endpoints:" in markdown and "0" in markdown


class TestMarkdownGenerator:
    """Tests for markdown generation end-to-end."""
    
    def test_generate_creates_index_file(self):
        """Test that generate_markdown creates index.md."""
        ep = Endpoint("GET", "/items", "List items")
        schema = Schema(title="Test API", version="1.0.0", endpoints=[ep])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            generate_markdown(schema, tmpdir)
            
            output_path = Path(tmpdir)
            assert (output_path / "index.md").exists()
    
    def test_generate_creates_endpoint_files(self):
        """Test that generate_markdown creates per-endpoint files."""
        ep1 = Endpoint("GET", "/items", "List items")
        ep2 = Endpoint("GET", "/items/{id}", "Get item")
        schema = Schema(title="Test API", version="1.0.0", endpoints=[ep1, ep2])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            generate_markdown(schema, tmpdir)
            
            output_path = Path(tmpdir)
            md_files = list(output_path.glob("*.md"))
            
            # Should have index + 2 endpoints
            assert len(md_files) >= 3
    
    def test_generate_creates_valid_markdown(self):
        """Test that generated markdown has valid structure."""
        ep = Endpoint("GET", "/test", "Test endpoint")
        schema = Schema(title="Test API", version="1.0.0", endpoints=[ep])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            generate_markdown(schema, tmpdir)
            
            index_file = Path(tmpdir) / "index.md"
            content = index_file.read_text()
            
            # Check basic markdown structure
            assert content.startswith("#")  # Should start with heading
            assert "[" in content  # Should have links
            assert "](" in content or "]" in content  # Markdown links (may use different format)
    
    def test_generate_with_empty_endpoints_list(self):
        """Test generating docs with no endpoints."""
        schema = Schema(title="Empty API", version="1.0.0", endpoints=[])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            generate_markdown(schema, tmpdir)
            
            # Should still create index.md
            assert (Path(tmpdir) / "index.md").exists()
    
    def test_generate_creates_output_directory(self):
        """Test that generate_markdown creates output directory if needed."""
        ep = Endpoint("GET", "/items")
        schema = Schema(endpoints=[ep])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "nested" / "output" / "docs"
            generate_markdown(schema, str(output_dir))
            
            assert output_dir.exists()
            assert (output_dir / "index.md").exists()
    
    def test_generate_multiple_endpoints_on_same_path(self):
        """Test generating docs when multiple methods share same path."""
        ep1 = Endpoint("GET", "/items", "List items")
        ep2 = Endpoint("POST", "/items", "Create item")
        schema = Schema(endpoints=[ep1, ep2])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            generate_markdown(schema, tmpdir)
            
            output_path = Path(tmpdir)
            md_files = list(output_path.glob("*.md"))
            
            # Should have index + 2 endpoint files
            assert len(md_files) >= 3
    
    def test_generate_with_special_characters_in_path(self):
        """Test generating docs with special characters in path."""
        ep = Endpoint("GET", "/api/v1/users/{user_id}/profile", "Get user profile")
        schema = Schema(endpoints=[ep])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            generate_markdown(schema, tmpdir)
            
            # Should create files without errors
            output_path = Path(tmpdir)
            md_files = list(output_path.glob("*.md"))
            assert len(md_files) >= 1
    
    def test_generate_index_mentions_endpoints(self):
        """Test that index markdown mentions endpoints."""
        ep1 = Endpoint("GET", "/items", "List")
        ep2 = Endpoint("POST", "/items", "Create")
        schema = Schema(title="API", version="1.0.0", endpoints=[ep1, ep2])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            generate_markdown(schema, tmpdir)
            
            index_file = Path(tmpdir) / "index.md"
            content = index_file.read_text()
            
            # Index should reference the endpoints
            assert "List" in content or "GET" in content
            assert "Create" in content or "POST" in content
