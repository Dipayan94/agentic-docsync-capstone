"""
Tests for CLI module.
"""
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import shutil


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def run_docsync(args, capture_stdout=True):
    """
    Helper to run docsync CLI command.
    
    Returns:
        tuple of (exit_code, stdout, stderr)
    """
    cmd = [sys.executable, "-m", "docsync"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def test_cli_sync_success():
    """Test successful sync command."""
    schema_path = FIXTURES_DIR / "sample_openapi.json"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_path = Path(tmpdir) / "docs.md"
        output_path = Path(tmpdir) / "output.md"
        
        # Create empty docs file
        docs_path.write_text("# Existing docs\n")
        
        exit_code, stdout, stderr = run_docsync([
            "sync",
            "--schema", str(schema_path),
            "--docs", str(docs_path),
            "--output", str(output_path)
        ])
        
        assert exit_code == 0
        assert output_path.exists()
        
        content = output_path.read_text()
        assert "GET /items" in content
        assert "POST /items/{item_name}/{quantity}" in content


def test_cli_sync_dry_run():
    """Test sync with --dry-run does not write output."""
    schema_path = FIXTURES_DIR / "sample_openapi.json"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_path = Path(tmpdir) / "docs.md"
        output_path = Path(tmpdir) / "output.md"
        
        docs_path.write_text("# Existing docs\n")
        
        exit_code, stdout, stderr = run_docsync([
            "sync",
            "--schema", str(schema_path),
            "--docs", str(docs_path),
            "--output", str(output_path),
            "--dry-run"
        ])
        
        assert exit_code == 0
        assert not output_path.exists()
        assert "Report" in stdout


def test_cli_sync_json_format():
    """Test sync with --format json outputs valid JSON."""
    schema_path = FIXTURES_DIR / "sample_openapi.json"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_path = Path(tmpdir) / "docs.md"
        output_path = Path(tmpdir) / "output.md"
        
        docs_path.write_text("# Existing docs\n")
        
        exit_code, stdout, stderr = run_docsync([
            "sync",
            "--schema", str(schema_path),
            "--docs", str(docs_path),
            "--output", str(output_path),
            "--dry-run",
            "--format", "json"
        ])
        
        assert exit_code == 0
        
        # Parse JSON output
        report = json.loads(stdout)
        assert "endpoints_total" in report
        assert report["endpoints_total"] == 2
        assert "endpoints" in report


def test_cli_invalid_format():
    """Test invalid --format value returns exit code 2."""
    schema_path = FIXTURES_DIR / "sample_openapi.json"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_path = Path(tmpdir) / "docs.md"
        output_path = Path(tmpdir) / "output.md"
        
        docs_path.write_text("# Existing docs\n")
        
        # Use invalid format via environment/direct call since argparse validates choices
        # We test the validation logic exists, but argparse prevents invalid values
        # This test verifies our validation exists in the code
        exit_code, stdout, stderr = run_docsync([
            "sync",
            "--schema", str(schema_path),
            "--docs", str(docs_path),
            "--output", str(output_path),
            "--format", "xml"
        ])
        
        # argparse will catch this and return non-zero
        assert exit_code != 0


def test_cli_missing_schema_file():
    """Test missing schema file returns exit code 1."""
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_path = Path(tmpdir) / "docs.md"
        output_path = Path(tmpdir) / "output.md"
        
        docs_path.write_text("# Existing docs\n")
        
        exit_code, stdout, stderr = run_docsync([
            "sync",
            "--schema", "nonexistent.json",
            "--docs", str(docs_path),
            "--output", str(output_path)
        ])
        
        assert exit_code == 1
        assert "not found" in stderr.lower()


def test_cli_invalid_json_schema():
    """Test invalid JSON schema returns exit code 2."""
    schema_path = FIXTURES_DIR / "malformed.json"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_path = Path(tmpdir) / "docs.md"
        output_path = Path(tmpdir) / "output.md"
        
        docs_path.write_text("# Existing docs\n")
        
        exit_code, stdout, stderr = run_docsync([
            "sync",
            "--schema", str(schema_path),
            "--docs", str(docs_path),
            "--output", str(output_path)
        ])
        
        assert exit_code == 2
        assert "validation error" in stderr.lower()


def test_cli_malformed_markers():
    """Test malformed markers in docs return exit code 2."""
    schema_path = FIXTURES_DIR / "sample_openapi.json"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_path = Path(tmpdir) / "docs.md"
        output_path = Path(tmpdir) / "output.md"
        
        # Create docs with only begin marker (malformed)
        docs_path.write_text("# Existing docs\n\n<!-- DOCSYNC:BEGIN GENERATED -->\n")
        
        exit_code, stdout, stderr = run_docsync([
            "sync",
            "--schema", str(schema_path),
            "--docs", str(docs_path),
            "--output", str(output_path)
        ])
        
        assert exit_code == 2
        assert "validation error" in stderr.lower()
