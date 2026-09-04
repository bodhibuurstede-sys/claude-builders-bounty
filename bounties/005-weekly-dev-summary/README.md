# Weekly GitHub dev summary (n8n + Claude)

An importable n8n workflow for bounty #5. Every Friday at 17:00 it gathers the previous seven days of GitHub activity, asks Claude Sonnet 4 for a narrative engineering summary, and posts the result to Discord. A Manual Trigger is included for safe verification before activation.

## What it does

- fetches commits from `GET /repos/{owner}/{repo}/commits`;
- fetches issues closed during the same seven-day window;
- fetches PRs merged during the same window;
- asks `claude-sonnet-4-20250514` to synthesize the activity without inventing work;
- supports `EN` and `FR`;
- posts the finished summary to a configurable Discord webhook;
- keeps repository, destination, language, API endpoints, and secrets outside the workflow file.

## Setup — 5 steps

1. Import `weekly-dev-summary.json` into n8n.
2. Set `GITHUB_REPO=owner/repo`, `SUMMARY_LANGUAGE=EN` (or `FR`), and `DESTINATION_WEBHOOK_URL=https://discord.com/api/webhooks/...` in the n8n environment.
3. Set secrets `GITHUB_TOKEN` and `ANTHROPIC_API_KEY` in the n8n environment; use a read-only GitHub token scoped to the target repository.
4. Run **Manual test** once and confirm the Discord message is correct.
5. Activate the workflow. The Schedule Trigger then runs every Friday at 17:00 in the n8n instance timezone.

Optional test-only overrides `GITHUB_API_BASE_URL` and `ANTHROPIC_API_BASE_URL` let the workflow point to local mock APIs. They default to the real GitHub and Anthropic endpoints.

## Data flow

`Friday 17:00 / Manual test → Config → 7-day range → commits → closed issues → merged PRs → Claude prompt → Claude → Discord`

The three GitHub reads run sequentially on purpose. That makes the workflow deterministic and lets the prompt node reference each prior response by node name without merge-node timing ambiguity.

## Security and failure behavior

- No API keys, tokens, or webhook URLs are committed.
- GitHub data is read only.
- Configuration validation stops early on a malformed repo, unsupported language, or missing destination.
- The prompt explicitly instructs Claude to use only supplied repository activity and not invent work.
- Discord output is capped below the 2,000-character message limit.
- The workflow remains inactive after import so the first execution is deliberate.

## Validation

Run the repository-level static contract test:

```bash
python bounties/005-weekly-dev-summary/test_workflow.py
```

The GitHub Action also imports the JSON into a real n8n CLI and executes the workflow against local deterministic mock endpoints. It saves the successful execution log plus `execution-evidence.png` as a CI artifact, so testing does not require live GitHub, Anthropic, or Discord credentials.

The CLI path follows n8n's supported model: import the workflow first, then execute the imported workflow by ID. Production still uses the same workflow JSON; only the test API base URLs are overridden.
