"""Marker-based merge logic for preserving custom documentation content."""

import re
from typing import Tuple, Optional
from docsync import ValidationError
from docsync.markdown import BEGIN_MARKER, END_MARKER


def split_by_markers(text: str) -> Tuple[str, str, str]:
    """
    Split document by markers into prefix, generated content, and suffix.
    
    Args:
        text: Document content
        
    Returns:
        Tuple of (prefix, generated_content, suffix)
        
    Raises:
        ValidationError: If markers are malformed (e.g., BEGIN without END)
    """
    begin_count = text.count(BEGIN_MARKER)
    end_count = text.count(END_MARKER)
    
    if begin_count == 0 and end_count == 0:
        # No markers present
        raise ValidationError("No markers found")
    
    if begin_count != 1 or end_count != 1:
        raise ValidationError(
            f"Malformed markers: expected 1 BEGIN and 1 END marker, "
            f"found {begin_count} BEGIN and {end_count} END"
        )
    
    begin_idx = text.find(BEGIN_MARKER)
    end_idx = text.find(END_MARKER)
    
    if begin_idx >= end_idx:
        raise ValidationError("Malformed markers: BEGIN marker must come before END marker")
    
    prefix = text[:begin_idx].rstrip()
    # Include markers in the generated content extraction
    generated_start = begin_idx
    generated_end = end_idx + len(END_MARKER)
    generated = text[generated_start:generated_end]
    suffix = text[generated_end:].lstrip()
    
    return prefix, generated, suffix


def merge_docs(existing_text: Optional[str], generated_block: str) -> str:
    """
    Merge generated documentation with existing content using marker-based strategy.
    
    Args:
        existing_text: Existing document content (None if file doesn't exist)
        generated_block: New generated markdown block (includes markers)
        
    Returns:
        Merged document content
        
    Raises:
        ValidationError: If existing document has malformed markers
    """
    # Case 1: No existing document - create new with header
    if existing_text is None or existing_text.strip() == "":
        return generated_block
    
    # Case 2: Try to split by markers
    try:
        prefix, old_generated, suffix = split_by_markers(existing_text)
        # Markers exist and are well-formed - replace generated section
        result_parts = [prefix, generated_block]
        if suffix:
            result_parts.append(suffix)
        return "\n\n".join(result_parts)
    except ValidationError as e:
        if "No markers found" in str(e):
            # Case 3: No markers - preserve entire existing content and append
            return existing_text.rstrip() + "\n\n" + generated_block
        else:
            # Case 4: Malformed markers - fail validation
            raise
