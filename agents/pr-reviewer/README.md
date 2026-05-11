# Claude PR Reviewer Agent

This bounty submission adds a Claude Code PR review agent plus a zero-dependency Node CLI:

```bash
claude-review --pr https://github.com/owner/repo/pull/123
```

The CLI fetches GitHub PR metadata, changed files, and the diff, then returns structured Markdown with:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score: Low, Medium, or High

If `ANTHROPIC_API_KEY` is set, the CLI asks Claude Sonnet 4 to write the review. If no key is present, it falls back to deterministic diff-metadata review so the tool remains testable in CI and local development.

## Setup

1. Install or link the package:

   ```bash
   cd agents/pr-reviewer
   npm install
   npm link
   ```

2. Optional: configure credentials:

   ```bash
   export GITHUB_TOKEN=github_pat_or_token
   export ANTHROPIC_API_KEY=sk-ant-api-key
   ```

3. Review a pull request:

   ```bash
   claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/908
   ```

## Usage

Write the review to a file:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --out review.md
```

Run without Claude API calls:

```bash
claude-review --pr https://github.com/owner/repo/pull/123 --no-ai
```

Post the review as a PR comment:

```bash
GITHUB_TOKEN=github_pat_or_token claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
```

## Claude Code Agent

The sub-agent prompt is included at:

```text
agents/pr-reviewer/.claude/agents/pr-reviewer.md
```

Copy it into a project-level `.claude/agents/pr-reviewer.md` or into your Claude Code agent directory. The agent is intentionally narrow: it produces a review comment draft and does not approve, merge, or request changes automatically.

## Validation

Run the format test:

```bash
npm test
```

On Windows environments with custom enterprise root certificates, Node may need the system certificate store:

```bash
NODE_OPTIONS=--use-system-ca node bin/claude-review.mjs --pr https://github.com/owner/repo/pull/123 --no-ai
```

Generate the checked sample outputs:

```bash
node bin/claude-review.mjs --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/908 --no-ai --out samples/pr-908-review.md
node bin/claude-review.mjs --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/909 --no-ai --out samples/pr-909-review.md
```

Sample outputs from two real PRs are included in `samples/`.
