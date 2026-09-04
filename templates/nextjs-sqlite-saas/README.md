# Next.js 15 + SQLite SaaS CLAUDE.md

Opinionated drop-in project instructions for a greenfield Next.js 15 App Router SaaS using TypeScript, Drizzle, and SQLite via `better-sqlite3`.

## Setup

1. Copy `CLAUDE.md` to the root of a greenfield Next.js 15 project.
2. Use the documented stack and scripts without changing the architecture defaults.
3. Run `node templates/nextjs-sqlite-saas/validate-template.mjs` in this repository to verify the template contract.

## What is intentionally decided for you

The template chooses Server Components by default, Server Actions for same-app mutations, Node runtime for SQLite access, Drizzle over Prisma, explicit reviewed migrations, tenant scoping at the query boundary, integer minor units for money, Zod at untrusted boundaries, and small client islands. The goal is to remove generic architecture questions so Claude Code can begin implementation from a coherent baseline.

## Validation evidence

`validate-template.mjs` checks that the document contains every bounty-required section, concrete dev commands, explicit migration rules, project structure, component patterns, security/authorization guidance, and a substantial set of reason-bearing rules. It also rejects placeholders such as TODO/TBD and verifies that the file instructs Claude not to claim tests it did not run.

The validator is structural evidence, not a substitute for claiming an external Claude Code runtime test. Runtime behavior should only be claimed when actually executed in that environment.
