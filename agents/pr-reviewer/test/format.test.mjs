import assert from "node:assert/strict";
import { buildHeuristicReview, parsePrUrl } from "../bin/claude-review.mjs";

const parsed = parsePrUrl("https://github.com/owner/repo/pull/123?foo=bar");
assert.deepEqual(parsed, { owner: "owner", repo: "repo", number: 123 });

assert.throws(() => parsePrUrl("https://example.com/not-a-pr"), /GitHub pull request URL/);

const review = buildHeuristicReview({
  pull: {
    number: 123,
    title: "Add payment export",
    html_url: "https://github.com/owner/repo/pull/123",
    user: { login: "dev" },
  },
  files: [
    {
      filename: "src/payments/export.ts",
      additions: 120,
      deletions: 20,
    },
    {
      filename: "README.md",
      additions: 12,
      deletions: 2,
    },
  ],
  diff: "diff --git a/src/payments/export.ts b/src/payments/export.ts\n".repeat(20),
});

assert.equal(review.pr, "#123");
assert.equal(review.confidence, "Medium");
assert.ok(review.summary.length >= 2);
assert.ok(review.risks.some((risk) => risk.includes("No test file changed")));
assert.ok(review.suggestions.some((suggestion) => suggestion.includes("regression test")));

const docsReview = buildHeuristicReview({
  pull: {
    number: 124,
    title: "Update docs",
    html_url: "https://github.com/owner/repo/pull/124",
    user: { login: "docs-dev" },
  },
  files: [
    {
      filename: "docs/setup.md",
      additions: 20,
      deletions: 3,
    },
  ],
  diff: "diff --git a/docs/setup.md b/docs/setup.md\n",
});

assert.equal(docsReview.confidence, "High");
assert.ok(docsReview.summary.join(" ").includes("documentation-focused"));

console.log("format tests passed");
