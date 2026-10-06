"""Tests for the Copilot pre-tool secret guard hook."""

import json
import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = REPOSITORY_ROOT / ".github/hooks/scripts/check_staged_secrets.py"


def initialize_repository(path: Path) -> None:
    """Create a temporary Git repository for hook integration tests."""
    subprocess.run(["git", "init", "-q", str(path)], check=True)


def invoke_hook(repo_path: Path, command: str) -> dict[str, str]:
    """Send a synthetic Copilot PreToolUse event to the hook."""
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(repo_path),
    }
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def stage_file(repo_path: Path, name: str, content: str) -> None:
    """Write and stage a file in the temporary repository."""
    (repo_path / name).write_text(content, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo_path), "add", name], check=True)


def test_denies_commit_with_staged_github_token(tmp_path: Path) -> None:
    initialize_repository(tmp_path)
    secret = "ghp_" + "A" * 36
    stage_file(tmp_path, "settings.py", f'api_token = "{secret}"\n')

    decision = invoke_hook(tmp_path, "git commit -m 'add settings'")

    assert decision["permissionDecision"] == "deny"
    assert "settings.py:1" in decision["permissionDecisionReason"]
    assert "GitHub token" in decision["permissionDecisionReason"]
    assert secret not in decision["permissionDecisionReason"]


def test_denies_commit_with_staged_aws_access_key(tmp_path: Path) -> None:
    initialize_repository(tmp_path)
    stage_file(tmp_path, "settings.py", 'AWS_ACCESS_KEY_ID = "AKIA1234567890ABCDEF"\n')

    decision = invoke_hook(tmp_path, "git commit -m 'add settings'")

    assert decision["permissionDecision"] == "deny"
    assert "AWS access key" in decision["permissionDecisionReason"]


def test_commit_all_scans_unstaged_tracked_changes(tmp_path: Path) -> None:
    initialize_repository(tmp_path)
    stage_file(tmp_path, "settings.py", 'AWS_SECRET_ACCESS_KEY = "example"\n')
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Hook Test"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "hook-test@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "add safe baseline"],
        check=True,
        capture_output=True,
    )
    (tmp_path / "settings.py").write_text(
        'AWS_SECRET_ACCESS_KEY = "a-secret-value-for-testing"\n',
        encoding="utf-8",
    )

    decision = invoke_hook(tmp_path, "git commit -am 'update settings'")

    assert decision["permissionDecision"] == "deny"
    assert "settings.py:1" in decision["permissionDecisionReason"]
    assert "credential assignment" in decision["permissionDecisionReason"]


def test_allows_commit_with_safe_staged_changes(tmp_path: Path) -> None:
    initialize_repository(tmp_path)
    stage_file(tmp_path, "README.md", "This documents the safe setup.\n")

    decision = invoke_hook(tmp_path, "git commit -m 'add documentation'")

    assert decision == {}


def test_allows_non_commit_bash_commands(tmp_path: Path) -> None:
    initialize_repository(tmp_path)
    secret = "AKIA1234567890ABCDEF"
    stage_file(tmp_path, "settings.py", f'access_key = "{secret}"\n')

    decision = invoke_hook(tmp_path, "git status --short")

    assert decision == {}


def test_does_not_flag_common_placeholder_credentials(tmp_path: Path) -> None:
    initialize_repository(tmp_path)
    stage_file(tmp_path, "config.py", 'api_key = "YOUR_API_KEY_HERE"\n')

    decision = invoke_hook(tmp_path, "git commit -m 'add config'")

    assert decision == {}


def test_fails_closed_on_invalid_hook_input() -> None:
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input="{not-json",
        capture_output=True,
        text=True,
        check=True,
    )

    decision = json.loads(result.stdout)
    assert decision["permissionDecision"] == "deny"
