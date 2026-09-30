"""Apply the locked marker policy to existing docs and write atomically."""
import os
import tempfile
from pathlib import Path

from docsync.exceptions import DocSyncError, ValidationError
from docsync.markdown_generator import BEGIN_MARKER, END_MARKER


def read_existing_docs(docs_path: str) -> str:
    """Return the current contents of docs_path, or "" if it doesn't exist yet."""
    path = Path(docs_path)
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as e:
        raise DocSyncError(f"Cannot read docs file {docs_path}: {e}")


def merge_with_markers(existing_content: str, generated_block: str) -> str:
    """Merge generated_block (already wrapped in BEGIN/END markers) into existing_content.

    - markers_exist: replace content strictly between begin/end; preserve content outside
    - no_markers: append the generated block at the end; preserve entire existing content
    - malformed_markers: raise ValidationError (exit 2) with an actionable message
    """
    begin_count = existing_content.count(BEGIN_MARKER)
    end_count = existing_content.count(END_MARKER)

    if begin_count != end_count or begin_count > 1:
        raise ValidationError(
            "Malformed DocSync markers in existing docs: found "
            f"{begin_count} '{BEGIN_MARKER}' and {end_count} '{END_MARKER}'. "
            "Expected exactly one matching pair, or none. Fix or remove the markers and retry."
        )

    if begin_count == 0:
        prefix = existing_content
        if prefix and not prefix.endswith("\n"):
            prefix += "\n"
        if prefix:
            prefix += "\n"
        return prefix + generated_block

    begin_idx = existing_content.find(BEGIN_MARKER)
    end_idx = existing_content.find(END_MARKER)
    if begin_idx > end_idx:
        raise ValidationError(
            "Malformed DocSync markers in existing docs: end marker appears before begin marker. "
            "Fix the marker order and retry."
        )

    before = existing_content[:begin_idx]
    after = existing_content[end_idx + len(END_MARKER):]
    if after.startswith("\n"):
        after = after[1:]
    return before + generated_block + after


def atomic_write(output_path: str, content: str) -> None:
    """Write content to output_path atomically (temp file + os.replace).

    On failure, the original file is left untouched and DocSyncError (exit 1) is raised.
    """
    path = Path(output_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp_path, path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except OSError as e:
        raise DocSyncError(f"Failed to write output file {output_path}: {e}")
