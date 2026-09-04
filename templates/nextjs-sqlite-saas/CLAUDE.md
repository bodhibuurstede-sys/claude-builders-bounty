# CLAUDE.md — Next.js 15 + SQLite SaaS

This repository is a production-oriented SaaS application. Follow these rules without asking for architecture preferences unless a requested change genuinely conflicts with them.

## Stack and versions

- Use Next.js 15 App Router, React 19, TypeScript 5 in strict mode, Node.js 20+, pnpm, Tailwind CSS, Zod, Drizzle ORM, and SQLite via `better-sqlite3`.
- Use the Node runtime for all routes that touch SQLite. Do not move database code to the Edge runtime because `better-sqlite3` requires Node APIs.
- Keep dependencies minimal. Add a package only when the platform or standard library cannot solve the problem cleanly; every dependency increases upgrade and supply-chain cost.
- Prefer server-native Next.js features before adding client libraries: Server Components for reads, Server Actions for same-app mutations, Route Handlers for external/webhook APIs.

## Project structure

Use this structure:

```text
src/
  app/
    (marketing)/
    (auth)/
    (app)/
      dashboard/
    api/
      webhooks/
  components/
    ui/
    forms/
  db/
    index.ts
    schema.ts
    migrations/
  lib/
    auth/
    validation/
    errors/
  server/
    queries/
    actions/
    services/
  types/
```

Rules:

- Put route-specific components next to their route; put only genuinely reusable components in `src/components`. This prevents a global components folder from becoming an unowned dumping ground.
- Put database access in `src/server/queries` or `src/server/services`, never directly in Client Components. This keeps credentials and authorization logic server-only.
- Keep `src/db/schema.ts` declarative. Do not put business logic in schema definitions because migrations and runtime policy evolve at different speeds.
- Put cross-entity workflows in `src/server/services`. A Server Action should validate, authorize, call a service/query, and return a typed result; it should not contain a large business workflow.
- Do not create barrel `index.ts` exports for large folders. Explicit imports reduce circular dependencies and make ownership visible.

## Naming conventions

- React components and component files: `PascalCase.tsx` only for exported reusable components; route-local component files may use kebab-case when they are implementation details.
- Server Actions: verb-first names such as `createWorkspace`, `inviteMember`, `cancelSubscription` because actions represent commands.
- Queries: noun or intent names such as `getWorkspaceBySlug`, `listInvoicesForAccount`; do not prefix every query with `fetch` because the implementation may be local SQLite, not HTTP.
- Database tables and columns: `snake_case`; TypeScript variables and properties: `camelCase`. Keep the mapping explicit in Drizzle so SQL stays conventional while application code stays idiomatic.
- Boolean columns: positive names such as `is_active`, `email_verified`; avoid double negatives.
- Timestamps: suffix with `_at`, store UTC Unix milliseconds as integers, convert only at presentation boundaries.
- IDs: use opaque text IDs generated in the application. Do not expose sequential row IDs in public URLs because predictable identifiers make enumeration easier.

## Database rules

- All schema changes must be represented by committed migration files. Never edit a production database manually because manual state cannot be reproduced or reviewed.
- Migrations are append-only after merge. Never rewrite a migration that may have run elsewhere; create a new corrective migration instead.
- Wrap multi-statement state changes in a transaction. If all statements are not valid independently, they must commit or roll back together.
- Add foreign keys for ownership relations and enable `PRAGMA foreign_keys = ON`. Application checks are not a substitute for database integrity.
- Add unique constraints for invariants such as normalized email, workspace slug, external provider IDs, and idempotency keys. Race conditions can bypass application-level “check then insert” logic.
- Store money as integer minor units (`amount_cents`, etc.), never floating point. Floating point rounding is unacceptable for billing.
- Never use `SELECT *` in application queries. Select named columns so schema growth does not silently widen data exposure.
- Paginate user-controlled lists. Default limit is 50 and hard maximum is 100 to avoid unbounded memory and rendering work.
- Every user-owned query must include the tenant/account scope in SQL, not filter after fetching. Authorization should fail closed at the data boundary.
- Prefer soft deletion only for records that must be recoverable or retained for audit; otherwise hard-delete inside a transaction. Do not soft-delete everything because stale rows complicate uniqueness and every query.

## Migration workflow

1. Change `src/db/schema.ts`.
2. Generate a new migration and inspect the SQL before committing.
3. Run migrations against a disposable database and the local development database.
4. Run type-check, tests, and a production build.

Migration safety rules:

- Destructive column/table removal requires a two-step rollout when deployed data matters: first stop reading/writing the field, then remove it in a later release. This preserves rollback safety.
- Backfills must be explicit and bounded. For large datasets, do not hide expensive backfills in startup code.
- Never auto-run arbitrary schema synchronization in production. Production uses reviewed migrations so deployment behavior is deterministic.

## Database connection

Use one server-only module for the connection and Drizzle instance. In development, cache the connection on `globalThis` to avoid hot-reload connection churn. Do not import the database module from any file containing `"use client"`.

The deployment target must provide a persistent filesystem and a single writable application instance for `better-sqlite3`. If the product later requires multi-region or horizontally scaled writers, migrate the adapter intentionally rather than pretending a local SQLite file is distributed storage.

## Server Components and Client Components

- Components are Server Components by default. Add `"use client"` only when the component requires browser state, effects, event handlers, or browser-only APIs. This keeps JavaScript bundles small and server-only data off the client.
- Fetch database data in Server Components or server modules, not `useEffect`. Client-side fetching for initial page data adds a waterfall and duplicates loading/error states.
- Pass the minimum serializable data from Server to Client Components. Do not pass complete database rows when the client needs three fields.
- Keep interactive client islands small. A parent does not become a Client Component just because one child is interactive.

## Server Actions

Every mutation follows this order:

1. Parse and validate untrusted input with Zod.
2. Resolve the authenticated user on the server.
3. Authorize the user against the affected tenant/resource.
4. Execute the database change, using a transaction when needed.
5. Revalidate affected paths/tags.
6. Return a typed, serializable result with safe user-facing errors.

Never trust hidden form inputs, URL parameters, or client-provided account IDs for authorization. They are user-controlled data.

Do not return raw database or provider errors to the browser. Log diagnostic context server-side and return a stable public error code/message because raw errors may leak SQL, paths, or credentials.

## Route Handlers

Use Route Handlers for public APIs, webhooks, file callbacks, OAuth callbacks, and integrations. Prefer Server Actions for mutations initiated by this application's own UI because they preserve end-to-end types and reduce duplicate API plumbing.

Webhook rules:

- Verify signatures before parsing business intent.
- Persist the provider event ID under a unique constraint and make processing idempotent. Providers retry deliveries.
- Return success only after durable acceptance of the event.
- Never log full authorization headers, signatures, cookies, or payment payloads.

## Authentication and authorization

- Authentication answers “who are you”; every data mutation/query must separately answer “may you act on this resource”.
- Perform authorization on the server at the query/service boundary. Hiding a button is UX, not security.
- Session cookies must be `HttpOnly`, `Secure` in production, and use an appropriate `SameSite` policy.
- Never store authorization decisions only in client state.
- Rate-limit high-risk operations such as login, password reset, invitations, and externally exposed mutation endpoints.

## Validation

- Treat form data, search params, request JSON, headers, cookies, webhook payloads, and database JSON/text from external providers as untrusted.
- Parse at boundaries with Zod and pass typed values inward. Do not scatter `as SomeType` casts to silence uncertainty.
- Use `.safeParse` when validation failure is part of normal user flow; use `.parse` for internal invariants that should fail loudly.

## Error handling

- Expected domain errors use typed results or domain error classes.
- Unexpected errors are logged with an operation name and non-secret identifiers, then surfaced as generic user-safe messages.
- Do not catch an exception only to ignore it. Either recover deliberately, translate it, or let the framework error boundary handle it.
- Use `notFound()` for genuinely missing route resources and redirects for expected navigation, not as generic exception handling.

## Forms

- Progressive enhancement is preferred. Forms submit to Server Actions and remain understandable without JavaScript where practical.
- Validate on both client for UX and server for trust; server validation is authoritative.
- Disable duplicate submissions or enforce idempotency for operations with external side effects such as billing, invitations, and email sending.

## Caching and freshness

- Do not cache authenticated tenant-specific data globally.
- Cache only data whose ownership, staleness tolerance, and invalidation strategy are explicit.
- After a mutation, revalidate the smallest affected path/tag rather than calling broad application-wide revalidation.
- Do not add caching merely to improve synthetic benchmarks; stale authorization or billing data is worse than a modest database read.

## Security rules

- Secrets live in environment variables and server-only modules. Never prefix secrets with `NEXT_PUBLIC_`.
- Never commit `.env*` files containing credentials.
- Never interpolate untrusted values into raw SQL. Use Drizzle parameters/prepared statements.
- Sanitize any user-generated HTML before rendering and avoid `dangerouslySetInnerHTML` unless the input has an explicit sanitization pipeline.
- Validate redirect destinations against an allowlist or same-origin rule to prevent open redirects.
- Protect state-changing external endpoints against CSRF when cookie authentication is used.
- Do not weaken TypeScript, lint, authentication, validation, or security checks to make a failing implementation pass.

## Observability

- Log structured events with operation, request/correlation ID when available, entity IDs, and error code.
- Never log passwords, reset tokens, session cookies, API keys, full payment data, or raw authorization headers.
- Log business transitions such as subscription state changes and invitation acceptance when they are useful for support/audit.

## Testing rules

- Unit-test pure domain/validation functions.
- Integration-test database queries and transactions against a temporary SQLite database.
- Test authorization with both allowed and denied users; a happy-path-only authorization test is incomplete.
- Test every migration chain from an empty database in CI.
- For a bug fix, add a regression test that fails before the fix when practical.
- Mock network providers at the HTTP/provider boundary, not the service under test, so application behavior still executes.

## Development commands

Assume these package scripts exist and keep them working:

```bash
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm db:generate
pnpm db:migrate
pnpm build
```

Before considering a code change complete, run the narrowest relevant test first, then `pnpm lint`, `pnpm typecheck`, relevant tests, and `pnpm build` for changes that affect runtime/build configuration.

## Patterns to follow

- Prefer small server modules with explicit inputs and outputs because they are easier to test and authorize.
- Prefer database constraints plus application validation for invariants because each layer protects against different failure modes.
- Prefer explicit transactions for multi-record workflows because partial business state is costly to repair.
- Prefer composition over giant configurable components because feature-specific props become difficult to reason about.
- Prefer stable public error codes over exposing internal exceptions because clients should not depend on implementation details.
- Prefer idempotent provider/webhook operations because retries are normal in distributed systems.

## What we do not do — and why

- No Prisma by default: Drizzle keeps SQL visible and has less runtime machinery for this SQLite-first stack.
- No Pages Router: mixing routing models creates duplicate conventions in a greenfield Next.js 15 application.
- No global client state library by default: URL state, Server Components, forms, and local state cover most SaaS needs; add a store only for demonstrated cross-tree client state.
- No REST layer for internal page reads by default: Server Components can call server queries directly without an HTTP hop.
- No ORM-generated schema push in production: reviewed migrations are reproducible and auditable.
- No `any`: it suppresses the type system at exactly the boundaries where bugs accumulate. Use `unknown` and narrow it.
- No non-null assertions to bypass missing-state handling unless an invariant is proven immediately nearby.
- No user-controlled raw SQL, dynamic column names, or dynamic table names.
- No business logic in React effects. Effects synchronize with external browser systems; business workflows belong on the server.
- No secrets in client bundles, logs, fixtures, snapshots, or example code.
- No silent catches and no “temporary” security bypasses.

## How Claude should work in this repository

- First inspect the smallest relevant files and existing patterns; do not rewrite unrelated architecture.
- Make the smallest coherent change that preserves these conventions.
- Do not ask generic preference questions already answered by this file.
- If a requested change conflicts with a rule here, state the conflict and choose the safer compatible interpretation unless the user explicitly overrides the architecture.
- Never claim a test, migration, build, external API call, or browser check passed unless it was actually run.
- When uncertain about data ownership or authorization, fail closed and inspect the relevant query/service before modifying behavior.
