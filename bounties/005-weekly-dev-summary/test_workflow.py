#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKFLOW = ROOT / "weekly-dev-summary.json"

data = json.loads(WORKFLOW.read_text(encoding="utf-8"))
nodes = {node["name"]: node for node in data["nodes"]}

required_nodes = {
    "Friday 17:00",
    "Manual test",
    "Config",
    "Build date range",
    "Fetch commits",
    "Fetch closed issues",
    "Fetch merged PRs",
    "Build Claude prompt",
    "Generate summary with Claude",
    "Extract summary",
    "Deliver to Discord",
}
missing = required_nodes - nodes.keys()
assert not missing, f"missing nodes: {sorted(missing)}"

cron = nodes["Friday 17:00"]["parameters"]["rule"]["interval"][0]
assert cron["field"] == "cronExpression"
assert cron["expression"] == "0 17 * * 5"

serialized = json.dumps(data)
for token in [
    "GITHUB_REPO",
    "SUMMARY_LANGUAGE",
    "DESTINATION_WEBHOOK_URL",
    "GITHUB_TOKEN",
    "ANTHROPIC_API_KEY",
    "claude-sonnet-4-20250514",
    "/commits",
    "is:issue is:closed",
    "is:pr is:merged",
]:
    assert token in serialized, f"missing contract token: {token}"

assert "sk-ant-" not in serialized
assert "github_pat_" not in serialized
assert "discord.com/api/webhooks/" not in serialized

connections = data["connections"]
expected_chain = [
    ("Config", "Build date range"),
    ("Build date range", "Fetch commits"),
    ("Fetch commits", "Fetch closed issues"),
    ("Fetch closed issues", "Fetch merged PRs"),
    ("Fetch merged PRs", "Build Claude prompt"),
    ("Build Claude prompt", "Generate summary with Claude"),
    ("Generate summary with Claude", "Extract summary"),
    ("Extract summary", "Deliver to Discord"),
]
for source, target in expected_chain:
    actual = connections[source]["main"][0][0]["node"]
    assert actual == target, f"{source} should connect to {target}, got {actual}"

assert data["active"] is False
print("workflow contract: OK")
