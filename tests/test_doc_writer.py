import pytest

from docsync.doc_writer import atomic_write, merge_with_markers, read_existing_docs
from docsync.exceptions import DocSyncError, ValidationError
from docsync.markdown_generator import BEGIN_MARKER, END_MARKER, generate_markdown
from docsync.models import Endpoint


def test_read_existing_docs_missing_file_returns_empty_string(tmp_path):
    assert read_existing_docs(str(tmp_path / "missing.md")) == ""


def test_read_existing_docs_reads_file(tmp_path):
    docs = tmp_path / "docs.md"
    docs.write_text("hello", encoding="utf-8")
    assert read_existing_docs(str(docs)) == "hello"


def test_merge_no_markers_appends_and_preserves_existing_content():
    existing = "# Custom Intro\n\nSome hand-written notes.\n"
    generated = generate_markdown([Endpoint(path="/a", method="GET")])

    merged = merge_with_markers(existing, generated)

    assert merged.startswith(existing.rstrip("\n"))
    assert BEGIN_MARKER in merged
    assert "Some hand-written notes." in merged


def test_merge_existing_markers_replaces_only_between_markers():
    existing = (
        "# Custom Intro\n\n"
        f"{BEGIN_MARKER}\nOLD CONTENT\n{END_MARKER}\n\n"
        "# Custom Outro\n"
    )
    generated = generate_markdown([Endpoint(path="/a", method="GET")])

    merged = merge_with_markers(existing, generated)

    assert "Custom Intro" in merged
    assert "Custom Outro" in merged
    assert "OLD CONTENT" not in merged
    assert "## GET /a" in merged


def test_merge_mismatched_marker_counts_raises_validation_error():
    existing = f"{BEGIN_MARKER}\nno end marker\n"
    with pytest.raises(ValidationError):
        merge_with_markers(existing, generate_markdown([]))


def test_merge_end_before_begin_raises_validation_error():
    existing = f"{END_MARKER}\nstuff\n{BEGIN_MARKER}\n"
    with pytest.raises(ValidationError):
        merge_with_markers(existing, generate_markdown([]))


def test_atomic_write_creates_file_with_content(tmp_path):
    output = tmp_path / "out" / "docs.md"
    atomic_write(str(output), "hello world")
    assert output.read_text(encoding="utf-8") == "hello world"


def test_atomic_write_failure_leaves_original_untouched(tmp_path):
    output = tmp_path / "docs.md"
    output.write_text("original", encoding="utf-8")

    # Point the parent dir at a path component that is actually a file,
    # so mkdir/open fail and atomic_write must raise without touching `output`.
    blocked_parent = tmp_path / "docs.md" / "nested"

    with pytest.raises(DocSyncError):
        atomic_write(str(blocked_parent / "out.md"), "new content")

    assert output.read_text(encoding="utf-8") == "original"
