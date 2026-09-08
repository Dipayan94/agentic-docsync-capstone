"""Tests for marker-based merge behavior."""

import pytest
from docsync import ValidationError
from docsync.merge import split_by_markers, merge_docs
from docsync.markdown import BEGIN_MARKER, END_MARKER


def test_no_markers_preserves_and_appends():
    """Test that existing doc without markers preserves content and appends generated block."""
    existing_content = "# My Custom Documentation\n\nThis is my custom content."
    generated_block = f"{BEGIN_MARKER}\n\n## GET /items\n\n{END_MARKER}"
    
    result = merge_docs(existing_content, generated_block)
    
    # Should preserve existing content and append generated block
    assert "My Custom Documentation" in result
    assert "custom content" in result
    assert BEGIN_MARKER in result
    assert "GET /items" in result


def test_well_formed_markers_replace_generated_section():
    """Test that well-formed markers preserve prefix/suffix and replace generated section."""
    existing_content = f"""# API Docs

Custom intro text.

{BEGIN_MARKER}

## GET /old-endpoint

Old generated content.

{END_MARKER}

Custom footer text."""
    
    generated_block = f"{BEGIN_MARKER}\n\n## POST /new-endpoint\n\nNew generated content.\n\n{END_MARKER}"
    
    result = merge_docs(existing_content, generated_block)
    
    # Should preserve prefix and suffix
    assert "Custom intro text" in result
    assert "Custom footer text" in result
    
    # Should have new generated content
    assert "POST /new-endpoint" in result
    assert "New generated content" in result
    
    # Should NOT have old generated content
    assert "old-endpoint" not in result.lower()
    assert "Old generated content" not in result


def test_malformed_markers_raises_validation_error():
    """Test that malformed markers (BEGIN without END) raise ValidationError."""
    # Only BEGIN marker, no END
    malformed_content = f"""# API Docs

{BEGIN_MARKER}

## GET /items

Some content but no end marker."""
    
    generated_block = f"{BEGIN_MARKER}\n\n## POST /items\n\n{END_MARKER}"
    
    with pytest.raises(ValidationError) as exc_info:
        merge_docs(malformed_content, generated_block)
    assert "malformed" in str(exc_info.value).lower() or "marker" in str(exc_info.value).lower()


def test_markers_out_of_order_raises_validation_error():
    """Test that END marker before BEGIN marker raises ValidationError."""
    malformed_content = f"""# API Docs

{END_MARKER}

Some content.

{BEGIN_MARKER}"""
    
    generated_block = f"{BEGIN_MARKER}\n\n## POST /items\n\n{END_MARKER}"
    
    with pytest.raises(ValidationError):
        merge_docs(malformed_content, generated_block)


def test_multiple_markers_raises_validation_error():
    """Test that multiple BEGIN or END markers raise ValidationError."""
    malformed_content = f"""# API Docs

{BEGIN_MARKER}

Content 1

{END_MARKER}

{BEGIN_MARKER}

Content 2

{END_MARKER}"""
    
    generated_block = f"{BEGIN_MARKER}\n\n## POST /items\n\n{END_MARKER}"
    
    with pytest.raises(ValidationError):
        merge_docs(malformed_content, generated_block)


def test_none_existing_text_creates_new_doc():
    """Test that None existing_text creates new document with just generated block."""
    generated_block = f"{BEGIN_MARKER}\n\n## GET /items\n\n{END_MARKER}"
    
    result = merge_docs(None, generated_block)
    
    # Should just be the generated block
    assert result == generated_block
