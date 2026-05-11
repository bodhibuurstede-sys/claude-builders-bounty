from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


HOOK_PATH = Path(__file__).resolve().parents[1] / "destructive_bash_guard.py"
SPEC = importlib.util.spec_from_file_location("destructive_bash_guard", HOOK_PATH)
guard = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(guard)


class DestructiveBashGuardTest(unittest.TestCase):
    def test_allows_normal_bash_command(self) -> None:
        self.assertIsNone(guard.find_block_reason("npm test"))

    def test_blocks_rm_rf_variants(self) -> None:
        self.assertIn("recursive remove", guard.find_block_reason("rm -rf /tmp/build"))
        self.assertIn("recursive remove", guard.find_block_reason("sudo rm -r -f ./dist"))
        self.assertIn("recursive remove", guard.find_block_reason("/bin/rm -rf ./dist"))
        self.assertIn("recursive remove", guard.find_block_reason("rm --recursive --force old-cache"))

    def test_blocks_force_push_variants(self) -> None:
        self.assertIn("force-push", guard.find_block_reason("git push --force origin main"))
        self.assertIn("force-push", guard.find_block_reason("git push -f origin main"))
        self.assertIn("force-push", guard.find_block_reason("/usr/bin/git push --force origin main"))

    def test_blocks_drop_truncate_and_delete_without_where(self) -> None:
        self.assertIn("DROP TABLE", guard.find_block_reason('psql -c "DROP TABLE users"'))
        self.assertIn("TRUNCATE", guard.find_block_reason("mysql -e 'TRUNCATE sessions'"))
        self.assertIn("DELETE FROM", guard.find_block_reason('psql -c "DELETE FROM users"'))

    def test_allows_delete_with_where(self) -> None:
        self.assertIsNone(guard.find_block_reason('psql -c "DELETE FROM users WHERE id = 1"'))

    def test_denies_and_logs_blocked_pre_tool_use(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            guard.BLOCKED_LOG = Path(tmpdir) / "blocked.log"
            payload = {
                "cwd": "/workspace/demo",
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf build"},
            }

            stdin = io.StringIO(json.dumps(payload))
            stdout = io.StringIO()
            with mock.patch("sys.stdin", stdin), redirect_stdout(stdout):
                self.assertEqual(guard.main(), 0)

            output = json.loads(stdout.getvalue())
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")

            log_entry = json.loads(guard.BLOCKED_LOG.read_text(encoding="utf-8").strip())
            self.assertEqual(log_entry["project_path"], "/workspace/demo")
            self.assertEqual(log_entry["command"], "rm -rf build")

    def test_ignores_non_bash_tools(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/example"},
        }

        stdin = io.StringIO(json.dumps(payload))
        stdout = io.StringIO()
        with mock.patch("sys.stdin", stdin), redirect_stdout(stdout):
            self.assertEqual(guard.main(), 0)

        self.assertEqual(stdout.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
