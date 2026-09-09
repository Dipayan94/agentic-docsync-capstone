"""
Tests for marker-based merge module.
"""
import pytest

from docsync.markers import merge_with_markers, BEGIN_MARKER, END_MARKER
from docsync.exceptions import ValidationError


def test_merge_no_markers_appends():
    """Test merging with no markers appends generated content."""
    existing = "# My Docs\n\nSome custom content.\n"
    generated = "Generated content here"
    
    result = merge_with_markers(existing, generated)
    
    assert "My Docs" in result
    assert "Some custom content" in result
    assert BEGIN_MARKER in result
    assert END_MARKER in result
    assert "Generated content here" in result
    # Generated content should be at the end
    assert result.index(BEGIN_MARKER) > result.index("Some custom content")


def test_merge_both_markers_replaces():
    """Test merging with both markers replaces content between them."""
    existing = f"""# My Docs

Custom intro.

{BEGIN_MARKER}
Old generated content
{END_MARKER}

Custom outro.
"""
    generated = "New generated content"
    
    result = merge_with_markers(existing, generated)
    
    assert "My Docs" in result
    assert "Custom intro" in result
    assert "Custom outro" in result
    assert "New generated content" in result
    assert "Old generated content" not in result


def test_merge_mismatched_marker_count_raises():
    """Test mismatched marker counts raise ValidationError."""
    existing = f"""# My Docs

{BEGIN_MARKER}
Generated content
"""
    generated = "New content"
    
    with pytest.raises(ValidationError) as exc_info:
        merge_with_markers(existing, generated)
    assert "malformed markers" in str(exc_info.value).lower()


def test_merge_inverted_markers_raises():
    """Test inverted markers (end before begin) raise ValidationError."""
    existing = f"""# My Docs

{END_MARKER}
Some content
{BEGIN_MARKER}
"""
    generated = "New content"
    
    with pytest.raises(ValidationError) as exc_info:
        merge_with_markers(existing, generated)
    assert "malformed markers" in str(exc_info.value).lower()


def test_merge_multiple_marker_pairs_raises():
    """Test multiple marker pairs raise ValidationError."""
    existing = f"""# My Docs

{BEGIN_MARKER}
Content 1
{END_MARKER}

{BEGIN_MARKER}
Content 2
{END_MARKER}
"""
    generated = "New content"
    
    with pytest.raises(ValidationError) as exc_info:
        merge_with_markers(existing, generated)
    assert "malformed markers" in str(exc_info.value).lower()
