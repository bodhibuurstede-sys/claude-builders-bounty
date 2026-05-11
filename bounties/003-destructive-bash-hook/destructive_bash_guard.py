#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


def find_block_reason(command: str) -> str | None:
    normalized = " ".join(command.split())

    if _contains_forced_recursive_rm(command):
        return "Blocked destructive recursive remove command (rm with recursive and force flags)."

    if _contains_git_force_push(command):
        return "Blocked force-push command. Use a reviewed non-force push workflow instead."

    if re.search(r"\bdrop\s+table\b", normalized, flags=re.IGNORECASE):
        return "Blocked SQL DROP TABLE statement."

    if re.search(r"\btruncate\b", normalized, flags=re.IGNORECASE):
        return "Blocked SQL TRUNCATE statement."

    if _contains_delete_without_where(normalized):
        return "Blocked SQL DELETE FROM statement without a WHERE clause."

    return None


def build_denial(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def log_block(input_data: dict[str, Any], command: str, reason: str) -> None:
    project_path = input_data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project_path,
        "command": command,
        "reason": reason,
    }
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, separators=(",", ":")) + "\n")


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if input_data.get("tool_name") != "Bash":
        return 0

    tool_input = input_data.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    log_block(input_data, command, reason)
    print(json.dumps(build_denial(reason)))
    return 0


def _contains_forced_recursive_rm(command: str) -> bool:
    for argv in _split_command_words(command):
        if not argv:
            continue
        try:
            rm_index = next(i for i, arg in enumerate(argv) if _is_command_name(arg, "rm"))
        except StopIteration:
            continue

        flags = argv[rm_index + 1 :]
        has_recursive = False
        has_force = False
        for flag in flags:
            if flag == "--":
                break
            if flag in {"-r", "-R", "--recursive", "-d"}:
                has_recursive = True
            if flag in {"-f", "--force"}:
                has_force = True
            if flag.startswith("-") and not flag.startswith("--"):
                has_recursive = has_recursive or "r" in flag.lower()
                has_force = has_force or "f" in flag.lower()

        if has_recursive and has_force:
            return True

    return False


def _contains_git_force_push(command: str) -> bool:
    for argv in _split_command_words(command):
        if len(argv) < 3:
            continue
        try:
            git_index = next(i for i, arg in enumerate(argv) if _is_command_name(arg, "git"))
        except StopIteration:
            continue
        if len(argv) <= git_index + 2 or argv[git_index + 1] != "push":
            continue
        if any(arg in {"--force", "-f", "--force-with-lease"} for arg in argv[git_index + 2 :]):
            return True
    return False


def _contains_delete_without_where(command: str) -> bool:
    for statement in re.split(r";|&&|\|\|", command):
        if re.search(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE) and not re.search(
            r"\bwhere\b",
            statement,
            flags=re.IGNORECASE,
        ):
            return True
    return False


def _split_command_words(command: str) -> list[list[str]]:
    commands: list[list[str]] = []
    for segment in re.split(r";|&&|\|\|", command):
        try:
            commands.append(shlex.split(segment, posix=True))
        except ValueError:
            commands.append(segment.split())
    return commands


def _is_command_name(arg: str, name: str) -> bool:
    return arg == name or arg.endswith(f"/{name}")


if __name__ == "__main__":
    raise SystemExit(main())
