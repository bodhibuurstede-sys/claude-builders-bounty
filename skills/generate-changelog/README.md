# Generate Changelog

Create a structured `CHANGELOG.md` from commits since the most recent git tag.

## Setup

1. Copy `changelog.sh` and `skills/generate-changelog/` into the repository you want to document.
2. Run `bash changelog.sh --output CHANGELOG.md`.
3. Review the categories, then commit the generated `CHANGELOG.md`.

## Usage

Local git repository:

```bash
bash changelog.sh --output CHANGELOG.md
```

Public GitHub repository, useful for testing or CI without a clone:

```bash
bash changelog.sh --repo owner/name --dry-run
```

Useful options:

- `--since-tag v1.2.3` uses a specific tag instead of auto-detecting the latest tag.
- `--max-commits 50` limits the number of commits included.
- `--dry-run` prints the changelog instead of writing a file.
- `GITHUB_TOKEN` raises the GitHub API rate limit for `--repo` mode.

## Categorization

The generator maps commits into Keep a Changelog-style sections:

- `Added`: `feat:`, `feature:`, and add/create/introduce subjects.
- `Fixed`: `fix:`, `bugfix:`, `security:`, and repair/prevent/correct subjects.
- `Removed`: `remove:`, `delete:`, `drop:`, and deprecate subjects.
- `Changed`: refactors, chores, docs, tests, and anything that is not clearly one of the above.
