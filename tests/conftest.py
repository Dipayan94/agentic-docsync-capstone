"""Shared test fixtures and configuration."""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def tmp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
