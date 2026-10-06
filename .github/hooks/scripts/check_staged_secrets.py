#!/usr/bin/env python3
"""Block Copilot Bash git commits when staged changes contain likely secrets."""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Pattern


COMMIT_COMMAND = re.compile(
    r"\b(?:sudo\s+)?git\s+(?:[^\s;&|]+\s+)*commit(?:\s|$|[;&|])"
)
HUNK_HEADER = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
PLACEHOLDER_VALUES = (
    "change-me",
    "changeme",
    "dummy",
    "example",
    "insert",
    "none",
    "null",
    "placeholder",
    "replace",
    "test",
    "your",
)
SECRET_PATTERNS: tuple[tuple[str, Pattern[str]], ...] = (
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    (
        "GitHub token",
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    ),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    (
        "credential assignment",
        re.compile(
            r"\b(?:api[_-]?(?:key|token)|access[_-]?(?:key|token)|auth[_-]?token|"
            r"aws[_-]?secret[_-]?access[_-]?key|aws[_-]?session[_-]?token|"
            r"client[_-]?secret|password|passwd|secret(?:[_-]?key)?|token)\b\s*[:=]\s*"
            r"""["']?([^"' \t,;}{]{8,})""",
            re.IGNORECASE,
        ),
    ),
)


def emit(decision: str, reason: str | None = None) -> None:
    """Write one preToolUse decision object to stdout."""
    result: dict[str, str] = {"permissionDecision": decision}
    if reason is not None:
        result["permissionDecisionReason"] = reason
    print(json.dumps(result))


def staged_diff(repo_path: str, include_worktree: bool) -> str:
    """Return staged changes and optionally tracked worktree changes."""
    root = subprocess.run(
        ["git", "-C", repo_path, "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if root.returncode != 0:
        raise RuntimeError("the working directory is not a Git repository")

    diff_arguments = [
        "git",
        "-C",
        root.stdout.strip(),
        "diff",
        "--no-ext-diff",
        "--no-textconv",
        "--no-color",
        "--unified=0",
        "--",
    ]
    diff_text = ""
    diff_kinds = (True, False) if include_worktree else (True,)
    for cached in diff_kinds:
        arguments = diff_arguments.copy()
        if cached:
            arguments.insert(4, "--cached")
        result = subprocess.run(
            arguments,
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError("unable to inspect staged changes")
        diff_text += result.stdout
    return diff_text


def commit_includes_tracked_worktree(command: str) -> bool:
    """Detect git commit -a/--all options that also commit unstaged tracked edits."""
    try:
        arguments = shlex.split(command)
    except ValueError:
        return True

    for index, argument in enumerate(arguments):
        if argument != "commit":
            continue
        for option in arguments[index + 1 :]:
            if option in {"&&", "||", ";", "|"}:
                break
            if option == "--all" or (
                option.startswith("-")
                and not option.startswith("--")
                and "a" in option[1:]
            ):
                return True
            if not option.startswith("-"):
                break
    return False


def is_placeholder(value: str) -> bool:
    """Recognize common template values to avoid flagging example credentials."""
    normalized = value.strip().strip("\"'").lower()
    return (
        normalized.startswith(PLACEHOLDER_VALUES)
        or normalized.startswith("<")
        or bool(re.fullmatch(r"(.)\1{7,}", normalized))
    )


def scan_added_lines(diff: str) -> list[tuple[str, int, str]]:
    """Find likely credentials only in added lines of the staged diff."""
    findings: list[tuple[str, int, str]] = []
    current_file = "unknown file"
    current_line = 0

    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            continue
        hunk = HUNK_HEADER.match(line)
        if hunk:
            current_line = int(hunk.group(1))
            continue
        if not line.startswith("+") or line.startswith("+++"):
            if line.startswith(" "):
                current_line += 1
            continue

        added_line = line[1:]
        for label, pattern in SECRET_PATTERNS:
            match = pattern.search(added_line)
            if match is None:
                continue
            if label == "credential assignment" and is_placeholder(match.group(1)):
                continue
            findings.append((current_file, current_line, label))
            break
        current_line += 1

    return findings


def handle_event(event: object) -> None:
    """Inspect a Copilot PreToolUse event and allow or deny the pending tool call."""
    if not isinstance(event, dict):
        emit("deny", "Cannot inspect this tool call; refusing to run it.")
        return

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        emit("deny", "Cannot inspect this tool call; refusing to run it.")
        return
    command = tool_input.get("command", "")
    if tool_name != "Bash" or not isinstance(command, str):
        emit("deny", "Cannot inspect this tool call; refusing to run it.")
        return
    if COMMIT_COMMAND.search(command) is None:
        print("{}")
        return

    repo_path = event.get("cwd")
    if not isinstance(repo_path, str) or not repo_path or not Path(repo_path).is_dir():
        emit("deny", "Cannot inspect staged changes; refusing to commit.")
        return

    try:
        findings = scan_added_lines(
            staged_diff(repo_path, commit_includes_tracked_worktree(command))
        )
    except (OSError, RuntimeError, subprocess.SubprocessError):
        emit("deny", "Unable to inspect staged changes; refusing to commit.")
        return

    if findings:
        summary = "; ".join(
            f"{path}:{line_number} ({label})"
            for path, line_number, label in findings[:5]
        )
        extra = f" and {len(findings) - 5} more" if len(findings) > 5 else ""
        emit(
            "deny",
            f"Potential secret(s) detected in staged changes: {summary}{extra}. "
            "Remove or replace them before committing.",
        )
        return

    print("{}")


def main() -> int:
    """Read the hook event from stdin and emit a decision."""
    try:
        event = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        emit("deny", "Cannot parse the tool event; refusing to run it.")
        return 0
    handle_event(event)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
