"""Test suite for docsync.cli

Test coverage:
- parse command
- generate command
- diff command
- sync command
- validate command
- CLI argument parsing
"""

import pytest
import json
import tempfile
from pathlib import Path
from io import StringIO
from unittest.mock import patch
from docsync.cli import DocsyncCLI
from docsync.models import Endpoint


class FakeArgs:
    """Mock args object for testing CLI commands."""
    pass


class TestParseCommand:
    """Tests for parse command."""
    
    def test_parse_valid_schema(self):
        """Test parse command with valid schema."""
        schema_data = {
            "openapi": "3.1.0",
            "info": {"title": "Test", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "openapi.json"
            with open(schema_file, 'w') as f:
                json.dump(schema_data, f)
            
            args = FakeArgs()
            args.schema_file = str(schema_file)
            
            # Should not raise exception
            with patch('sys.stdout', StringIO()):
                DocsyncCLI.parse_command(args)
    
    def test_parse_shows_endpoint_count(self):
        """Test that parse command displays endpoint information."""
        schema_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/items": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/users": {"get": {"responses": {"200": {"description": "OK"}}}}
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "openapi.json"
            with open(schema_file, 'w') as f:
                json.dump(schema_data, f)
            
            args = FakeArgs()
            args.schema_file = str(schema_file)
            
            output = StringIO()
            with patch('sys.stdout', output):
                DocsyncCLI.parse_command(args)
            
            output_str = output.getvalue()
            assert "2" in output_str or "Endpoints" in output_str
    
    def test_parse_missing_file(self):
        """Test parse command with missing file."""
        args = FakeArgs()
        args.schema_file = "/nonexistent/openapi.json"
        
        with pytest.raises(SystemExit):
            with patch('sys.stdout', StringIO()):
                DocsyncCLI.parse_command(args)


class TestGenerateCommand:
    """Tests for generate command."""
    
    def test_generate_creates_docs(self):
        """Test that generate command creates documentation files."""
        schema_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/items": {
                    "get": {"responses": {"200": {"description": "OK"}}}
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "openapi.json"
            output_dir = Path(tmpdir) / "docs"
            
            with open(schema_file, 'w') as f:
                json.dump(schema_data, f)
            
            args = FakeArgs()
            args.schema_file = str(schema_file)
            args.output_dir = str(output_dir)
            
            with patch('sys.stdout', StringIO()):
                DocsyncCLI.generate_command(args)
            
            # Check files were created
            assert (output_dir / "index.md").exists()
    
    def test_generate_invalid_schema(self):
        """Test generate with invalid schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "bad.json"
            output_dir = Path(tmpdir) / "docs"
            
            schema_file.write_text("{invalid}")
            
            args = FakeArgs()
            args.schema_file = str(schema_file)
            args.output_dir = str(output_dir)
            
            with pytest.raises(SystemExit):
                with patch('sys.stdout', StringIO()):
                    DocsyncCLI.generate_command(args)


class TestDiffCommand:
    """Tests for diff command."""
    
    def test_diff_no_changes(self):
        """Test diff with identical schemas."""
        schema_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/items": {"get": {"responses": {"200": {"description": "OK"}}}}
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "openapi.json"
            
            with open(schema_file, 'w') as f:
                json.dump(schema_data, f)
            
            args = FakeArgs()
            args.old_schema = str(schema_file)
            args.new_schema = str(schema_file)
            
            output = StringIO()
            with patch('sys.stdout', output):
                DocsyncCLI.diff_command(args)
            
            output_str = output.getvalue()
            # Should show 0 changes detected
            assert "0" in output_str or "changes" in output_str.lower()
    
    def test_diff_detects_new_endpoint(self):
        """Test diff detects new endpoint."""
        old_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/items": {"get": {"responses": {"200": {"description": "OK"}}}}
            }
        }
        
        new_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/items": {"get": {"responses": {"200": {"description": "OK"}}}},
                "/users": {"get": {"responses": {"200": {"description": "OK"}}}}
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            old_file = Path(tmpdir) / "old.json"
            new_file = Path(tmpdir) / "new.json"
            
            with open(old_file, 'w') as f:
                json.dump(old_data, f)
            with open(new_file, 'w') as f:
                json.dump(new_data, f)
            
            args = FakeArgs()
            args.old_schema = str(old_file)
            args.new_schema = str(new_file)
            
            output = StringIO()
            with patch('sys.stdout', output):
                DocsyncCLI.diff_command(args)
            
            output_str = output.getvalue()
            assert "1" in output_str or "changes" in output_str.lower()


class TestValidateCommand:
    """Tests for validate command."""
    
    def test_validate_valid_docs_directory(self):
        """Test validate with valid documentation directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_dir = Path(tmpdir)
            (docs_dir / "index.md").write_text("# API Docs")
            (docs_dir / "endpoints.md").write_text("# Endpoints")
            
            args = FakeArgs()
            args.docs_dir = str(docs_dir)
            
            output = StringIO()
            with patch('sys.stdout', output):
                DocsyncCLI.validate_command(args)
            
            output_str = output.getvalue()
            assert "valid" in output_str.lower()
            assert "2" in output_str
    
    def test_validate_missing_docs_directory(self):
        """Test validate with missing docs directory."""
        args = FakeArgs()
        args.docs_dir = "/nonexistent/docs"
        
        with pytest.raises(SystemExit):
            with patch('sys.stdout', StringIO()):
                DocsyncCLI.validate_command(args)
    
    def test_validate_empty_docs_directory(self):
        """Test validate with empty docs directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            args = FakeArgs()
            args.docs_dir = str(tmpdir)
            
            with pytest.raises(SystemExit):
                with patch('sys.stdout', StringIO()):
                    DocsyncCLI.validate_command(args)
    
    def test_validate_multiple_files(self):
        """Test validate with multiple markdown files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_dir = Path(tmpdir)
            for i in range(5):
                (docs_dir / f"file{i}.md").write_text(f"# File {i}")
            
            args = FakeArgs()
            args.docs_dir = str(docs_dir)
            
            output = StringIO()
            with patch('sys.stdout', output):
                DocsyncCLI.validate_command(args)
            
            output_str = output.getvalue()
            assert "5" in output_str


class TestSyncCommand:
    """Tests for sync command."""
    
    def test_sync_workflow(self):
        """Test full sync workflow."""
        schema_data = {
            "openapi": "3.1.0",
            "info": {"title": "API", "version": "1.0.0"},
            "paths": {
                "/items": {"get": {"responses": {"200": {"description": "OK"}}}}
            }
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "openapi.json"
            docs_dir = Path(tmpdir) / "docs"
            
            with open(schema_file, 'w') as f:
                json.dump(schema_data, f)
            
            args = FakeArgs()
            args.schema_file = str(schema_file)
            args.docs_dir = str(docs_dir)
            
            output = StringIO()
            with patch('sys.stdout', output):
                DocsyncCLI.sync_command(args)
            
            # Check that docs were created
            assert (docs_dir / "index.md").exists()
