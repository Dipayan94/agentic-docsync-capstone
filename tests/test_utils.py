"""Test suite for docsync.utils

Test coverage:
- JSON file operations (read/write)
- Text file operations
- Directory creation and management
"""

import pytest
import json
import tempfile
from pathlib import Path
from docsync.utils import (
    read_json, write_json, read_file, write_file, ensure_dir
)


class TestJsonOperations:
    """Tests for JSON file operations."""
    
    def test_write_and_read_json(self):
        """Test writing and reading JSON files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            data = {"name": "Test", "value": 42, "nested": {"key": "value"}}
            
            write_json(str(test_file), data)
            result = read_json(str(test_file))
            
            assert result == data
            assert result["name"] == "Test"
            assert result["value"] == 42
            assert result["nested"]["key"] == "value"
    
    def test_write_json_creates_parent_directories(self):
        """Test that write_json creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_file = Path(tmpdir) / "a" / "b" / "c" / "test.json"
            data = {"test": "data"}
            
            write_json(str(nested_file), data)
            
            assert nested_file.exists()
            result = read_json(str(nested_file))
            assert result == data
    
    def test_read_json_not_found(self):
        """Test reading non-existent JSON file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            read_json("/nonexistent/path/file.json")
    
    def test_read_json_invalid_json(self):
        """Test reading malformed JSON raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_file = Path(tmpdir) / "bad.json"
            bad_file.write_text("{invalid json content")
            
            with pytest.raises(ValueError, match="Invalid JSON"):
                read_json(str(bad_file))
    
    def test_write_json_custom_indent(self):
        """Test writing JSON with custom indentation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            data = {"key": "value"}
            
            write_json(str(test_file), data, indent=4)
            content = test_file.read_text()
            
            # With indent=4, the file should contain spaces for indentation
            assert "    " in content or len(content.split("\n")) > 1
    
    def test_write_json_complex_data(self):
        """Test writing complex nested JSON structures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "complex.json"
            data = {
                "items": [
                    {"id": 1, "name": "Item 1"},
                    {"id": 2, "name": "Item 2"}
                ],
                "metadata": {
                    "version": "1.0.0",
                    "nested": {
                        "deep": {
                            "value": "found"
                        }
                    }
                }
            }
            
            write_json(str(test_file), data)
            result = read_json(str(test_file))
            
            assert len(result["items"]) == 2
            assert result["metadata"]["nested"]["deep"]["value"] == "found"


class TestFileOperations:
    """Tests for text file operations."""
    
    def test_write_and_read_file(self):
        """Test writing and reading text files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            content = "Hello, World!"
            
            write_file(str(test_file), content)
            result = read_file(str(test_file))
            
            assert result == content
    
    def test_write_file_creates_parent_directories(self):
        """Test that write_file creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_file = Path(tmpdir) / "a" / "b" / "c" / "test.txt"
            content = "nested content"
            
            write_file(str(nested_file), content)
            
            assert nested_file.exists()
            result = read_file(str(nested_file))
            assert result == content
    
    def test_read_file_not_found(self):
        """Test reading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            read_file("/nonexistent/path/file.txt")
    
    def test_write_file_multiline_content(self):
        """Test writing multiline content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "multiline.txt"
            content = "Line 1\nLine 2\nLine 3"
            
            write_file(str(test_file), content)
            result = read_file(str(test_file))
            
            assert result == content
            lines = result.split("\n")
            assert len(lines) == 3
    
    def test_write_file_empty_content(self):
        """Test writing empty content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "empty.txt"
            
            write_file(str(test_file), "")
            result = read_file(str(test_file))
            
            assert result == ""
    
    def test_write_file_special_characters(self):
        """Test writing content with special characters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "special.txt"
            content = "Special chars: !@#$%^&*()_+-=[]{}|;:',.<>?/\nÜñíçödé"
            
            write_file(str(test_file), content)
            result = read_file(str(test_file))
            
            assert result == content


class TestEnsureDir:
    """Tests for directory creation and management."""
    
    def test_ensure_dir_creates_directory(self):
        """Test creating a new directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new_dir"
            result = ensure_dir(str(new_dir))
            
            assert result.exists()
            assert result.is_dir()
    
    def test_ensure_dir_existing_directory(self):
        """Test that ensure_dir works with existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_dir(tmpdir)
            assert result.exists()
            assert result.is_dir()
    
    def test_ensure_dir_nested_path(self):
        """Test creating nested directory paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "a" / "b" / "c" / "d"
            result = ensure_dir(str(nested_dir))
            
            assert result.exists()
            assert result.is_dir()
    
    def test_ensure_dir_returns_path(self):
        """Test that ensure_dir returns Path object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_dir(tmpdir)
            assert isinstance(result, Path)
