#!/usr/bin/env python3
"""Install the destructive Bash guard into the current user's Claude settings."""

from __future__ import annotations

import json
import shlex
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_HOOK = ROOT / "destructive_bash_guard.py"
CLAUDE_DIR = Path.home() / ".claude"
HOOK_DIR = CLAUDE_DIR / "hooks"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"
INSTALLED_HOOK = HOOK_DIR / "destructive_bash_guard.py"
HOOK_COMMAND = f"{shlex.quote(sys.executable)} {shlex.quote(str(INSTALLED_HOOK))}"


def main() -> int:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HOOK, INSTALLED_HOOK)

    settings = _load_settings()
    pre_tool_hooks = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
    hook_group = _bash_hook_group(pre_tool_hooks)
    hooks = hook_group.setdefault("hooks", [])

    if not any(hook.get("command") == HOOK_COMMAND for hook in hooks):
        hooks.append({"type": "command", "command": HOOK_COMMAND})

    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed hook at {INSTALLED_HOOK}")
    print(f"Updated settings at {SETTINGS_PATH}")
    return 0


def _load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return {}
    backup = SETTINGS_PATH.with_suffix(".json.bak")
    shutil.copy2(SETTINGS_PATH, backup)
    return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))


def _bash_hook_group(pre_tool_hooks: list[dict]) -> dict:
    for group in pre_tool_hooks:
        if group.get("matcher") == "Bash":
            return group
    group = {"matcher": "Bash", "hooks": []}
    pre_tool_hooks.append(group)
    return group


if __name__ == "__main__":
    raise SystemExit(main())
