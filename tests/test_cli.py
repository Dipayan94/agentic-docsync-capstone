import json
from pathlib import Path

from docsync.cli import main
from docsync.doc_writer import BEGIN_MARKER, END_MARKER

FIXTURES = Path(__file__).parent / "fixtures"


def _run(args):
    return main(args)


def test_sync_first_run_generates_docs_and_exits_zero(tmp_path, capsys):
    output = tmp_path / "api.md"
    exit_code = _run([
        "sync", "--schema", str(FIXTURES / "valid_openapi.json"),
        "--docs", str(output), "--output", str(output),
    ])

    assert exit_code == 0
    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "## GET /users" in content
    assert "## GET /users/{id}" in content

    out = capsys.readouterr().out
    assert "Added: 3" in out


def test_sync_format_json_outputs_added_modified_removed(tmp_path, capsys):
    output = tmp_path / "api.md"
    exit_code = _run([
        "sync", "--schema", str(FIXTURES / "valid_openapi.json"),
        "--docs", str(output), "--output", str(output), "--format", "json",
    ])

    assert exit_code == 0
    data = json.loads(capsys.readouterr().out)
    assert set(data.keys()) == {"added", "modified", "removed"}
    assert len(data["added"]) == 3


def test_sync_dry_run_does_not_write_output(tmp_path, capsys):
    output = tmp_path / "api.md"
    exit_code = _run([
        "sync", "--schema", str(FIXTURES / "valid_openapi.json"),
        "--docs", str(output), "--output", str(output), "--dry-run",
    ])

    assert exit_code == 0
    assert not output.exists()
    assert "DocSync Report" in capsys.readouterr().out


def test_sync_invalid_schema_returns_exit_code_2(tmp_path, capsys):
    output = tmp_path / "api.md"
    exit_code = _run([
        "sync", "--schema", str(FIXTURES / "invalid.json"),
        "--docs", str(output), "--output", str(output),
    ])

    assert exit_code == 2
    assert "Validation error" in capsys.readouterr().err


def test_sync_missing_schema_file_returns_exit_code_1(tmp_path, capsys):
    output = tmp_path / "api.md"
    exit_code = _run([
        "sync", "--schema", str(tmp_path / "nope.json"),
        "--docs", str(output), "--output", str(output),
    ])

    assert exit_code == 1
    assert "Error" in capsys.readouterr().err


def test_sync_missing_openapi_keys_returns_exit_code_2(tmp_path, capsys):
    output = tmp_path / "api.md"
    exit_code = _run([
        "sync", "--schema", str(FIXTURES / "missing_paths_openapi.json"),
        "--docs", str(output), "--output", str(output),
    ])

    assert exit_code == 2


def test_sync_empty_paths_generates_skeleton_with_zero_endpoints(tmp_path, capsys):
    output = tmp_path / "api.md"
    exit_code = _run([
        "sync", "--schema", str(FIXTURES / "empty_paths_openapi.json"),
        "--docs", str(output), "--output", str(output),
    ])

    assert exit_code == 0
    assert "No endpoints found." in output.read_text(encoding="utf-8")
    assert "Added: 0" in capsys.readouterr().out


def test_sync_preserves_custom_content_outside_markers(tmp_path, capsys):
    docs = tmp_path / "api.md"
    docs.write_text(
        f"# Intro\n\nHand-written notes.\n\n{BEGIN_MARKER}\nSTALE\n{END_MARKER}\n\n# Outro\n",
        encoding="utf-8",
    )

    exit_code = _run([
        "sync", "--schema", str(FIXTURES / "valid_openapi.json"),
        "--docs", str(docs), "--output", str(docs),
    ])

    assert exit_code == 0
    content = docs.read_text(encoding="utf-8")
    assert "Hand-written notes." in content
    assert "# Outro" in content
    assert "STALE" not in content
    assert "## GET /users" in content


def test_sync_malformed_markers_returns_exit_code_2(tmp_path, capsys):
    docs = tmp_path / "api.md"
    docs.write_text(f"{BEGIN_MARKER}\nno end marker here\n", encoding="utf-8")

    exit_code = _run([
        "sync", "--schema", str(FIXTURES / "valid_openapi.json"),
        "--docs", str(docs), "--output", str(docs),
    ])

    assert exit_code == 2
    assert "Malformed" in capsys.readouterr().err
