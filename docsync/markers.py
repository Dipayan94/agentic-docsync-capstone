"""
Marker-based merge module to preserve custom content.
"""
from pathlib import Path
from typing import Optional

from docsync.exceptions import ValidationError

BEGIN_MARKER = "<!-- DOCSYNC:BEGIN GENERATED -->"
END_MARKER = "<!-- DOCSYNC:END GENERATED -->"


def merge_with_markers(existing_content: str, generated_content: str) -> str:
    """
    Merge generated content into existing docs using markers.
    
    Policy:
    - If both markers exist: replace content between markers
    - If no markers exist: append generated block at end
    - If markers are malformed: raise ValidationError
    
    Args:
        existing_content: Current documentation content
        generated_content: New generated content to insert
        
    Returns:
        Merged content string
        
    Raises:
        ValidationError: If markers are malformed
    """
    begin_count = existing_content.count(BEGIN_MARKER)
    end_count = existing_content.count(END_MARKER)
    
    # Check for malformed markers
    if begin_count != end_count:
        raise ValidationError(
            f"Malformed markers: found {begin_count} begin markers and {end_count} end markers. "
            "They must appear in pairs."
        )
    
    if begin_count > 1:
        raise ValidationError(
            f"Malformed markers: found {begin_count} marker pairs. Only one pair is allowed."
        )
    
    # No markers: append at end
    if begin_count == 0:
        if not existing_content.endswith("\n"):
            existing_content += "\n"
        result = existing_content + "\n" + BEGIN_MARKER + "\n" + generated_content + "\n" + END_MARKER + "\n"
        return result
    
    # Both markers exist: replace region
    begin_idx = existing_content.find(BEGIN_MARKER)
    end_idx = existing_content.find(END_MARKER)
    
    # Check if markers are in correct order
    if begin_idx > end_idx:
        raise ValidationError(
            "Malformed markers: end marker appears before begin marker"
        )
    
    # Replace content between markers
    before = existing_content[:begin_idx]
    after = existing_content[end_idx + len(END_MARKER):]
    
    result = before + BEGIN_MARKER + "\n" + generated_content + "\n" + END_MARKER + after
    
    return result


def read_existing_docs(docs_path: str) -> str:
    """
    Read existing documentation file if it exists.
    
    Args:
        docs_path: Path to existing docs
        
    Returns:
        Content of existing docs, or empty string if file doesn't exist
    """
    path = Path(docs_path)
    
    if not path.exists():
        return ""
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except IOError:
        # If we can't read the file, treat as if it doesn't exist
        return ""
