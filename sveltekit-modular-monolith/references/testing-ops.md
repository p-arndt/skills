# Testing and operations

## Test layers

| Layer       | Tool                                        | Runs against                   | Covers                                                        |
| ----------- | ------------------------------------------- | ------------------------------ | ------------------------------------------------------------- |
| Unit        | Vitest (`server` project)                   | nothing                        | Zod schemas, permission resolution, transition tables, helpers |
| Integration | Vitest + Testcontainers Postgres            | real DB, migrated              | services, repos, RLS, triggers, transactions, history events   |
| Component   | Vitest browser mode (`client` project)      | chromium headless              | reusable components: props, roles, handler props               |
| E2E         | Playwright                                  | full compose stack             | journeys per module, permissions in UI, i18n, a11y smoke       |

Ratio: many integration tests, focused unit tests, one component test per reusable component,
one E2E journey per feature. shadcn primitives are not re-tested. No mocks of the database.

Vitest projects in `vite.config.ts`: `client` (`*.svelte.test.ts`, browser provider playwright),
`server` (`*.test.ts` minus integration), `integration` (`*.integration.test.ts`, `globalSetup`
starts the container, `fileParallelism: false`, `testTimeout` 30 s, `hookTimeout` 180 s).
`expect.requireAssertions: true`.

## Integration harness

- One Postgres container per run, migrations applied once from the same files as production.
- Tenant-per-test by default (RLS tests need real commits): `uniqueScope()` returns fresh
  tenant/user ids; `runAs(scope, fn)` wraps the production transaction helper; `rawSql(fn)` runs
  as the owner for fixtures and assertions.
- Factories (`createTenant`, `createMembership`, `createOrder`, …) return typed rows and a ctx.
  Never share seeds between integration tests.

## Mandatory suites (exist before the first release)

1. **Tenant isolation** (multi-tenant): per business table, insert as A, read as B → 0; update
   and delete as B → 0 affected; raw select without the tenant setting → 0.
2. **Table completeness**: enumerate `public` tables; every non-system table has the audit
   trigger, the standard columns and (if multi-tenant) RLS. Fails the build when a table is
   added without them.
3. **Append-only**: app role cannot UPDATE/DELETE audit and history tables.
4. **Permission resolution**: role grant, GRANT override, DENY beats both, unlicensed module
   removes keys, expired membership yields empty set.
5. **Transaction atomicity**: force a failure after the business write; neither row nor history
   event exists.
6. **Step-up re-auth**: every critical service rejects a call without a valid, unexpired,
   action-bound proof; a proof cannot be reused.
7. **Optimistic locking**: stale version → conflict, no silent overwrite.
8. **Status machines**: every allowed and forbidden transition, including a direct insert that
   bypasses the service and must be rejected by the trigger.

## Performance gate

`perf/list-p95.integration.test.ts` runs every list/search function 30× with typical filters
through the production transaction path and fails at p95 ≥ 300 ms. Skipped unless `LOAD_TENANT`
is set; then the harness starts no container and targets the `.env` database, which a load seed
script (`--scale`, `--tenant`, `--reset`, `--no-audit`) has filled with the target profile. Let
autovacuum settle a minute before measuring. `pg_stat_statements` is on from day one.

## E2E

- Stack: `docker compose --env-file .env.test -f compose.yaml -f compose.e2e.yaml up -d --wait`,
  tmpfs storage, own project name (`-p`) so it does not recreate the dev containers.
- `global-setup.ts` migrates and seeds. `E2E_DEV=1` runs `vite dev` instead of build + preview
  for fix cycles; commits and CI use the build. `E2E_PORT` moves the preview off the dev port.
- Seeded users: platform operator, tenant admin, a restricted role, a viewer, a second tenant.
- Each journey: login → action → assert UI → assert history entry visible.
- Negative journeys: viewer sees no create button and gets 403 on the direct URL; unlicensed
  module hidden and 403.
- Mail-dependent journeys read the mail sink's JSON API and skip when unreachable.
- a11y smoke with `@axe-core/playwright` on shell, list, detail, dialog, wizard; one journey
  runs in the second locale.
- Gotcha: bits-ui `Select` renders as `role=button`, not `combobox`.

## Traceability (regulated domains)

Requirement ids appear in test titles (`it('REQ-ORD-41 rejects …')`) or in a `// REQ:` comment.
A script collects titles from all test files into `reports/traceability.{md,csv}` with a
kind column; the E2E pipeline step publishes it. Unmapped tests are listed; the list must be
empty or explicitly waived for release.

## Coverage and gates

Services and repos ≥ 90% lines, overall ≥ 80%, reported not worshipped. CI red on: any
mandatory suite failing, a table lacking trigger/RLS, a merged migration modified, unwaived
traceability gaps.

## Runtime topology

```
reverse proxy (TLS)
  └── app ×N (adapter-node, :3000, /healthz /readyz)
postgres
s3-compatible object store (bucket versioning on)
smtp relay
migrate   one-shot job from the same image, runs before rollout
worker    optional, same image, pg-boss consumers
```

Stateless app, no sticky sessions, no in-process caches of business state. Sessions in Postgres.
Graceful shutdown on SIGTERM. `/healthz` = process alive; `/readyz` = DB reachable, schema
current, storage reachable.

## Dev compose

Single-binary local stand-ins for S3, mail sink and (behind a profile) a test IdP. Images without
a shell have no healthcheck; use `depends_on` without `condition` and let clients retry. The
seed creates the bucket. `.env` is the git-ignored local copy of `.env.example` with secrets;
`.env.test` is tracked with fixed non-secret values. Keep values unquoted in both, as Docker and
Node `--env-file` do not strip quotes.

## Seeds

Idempotent code (`skip when exists`, run twice = no-op), not SQL dumps. Creates tenants, users
with printed credentials, master data, a realistic object tree, generated sample documents (a
real one-page PDF and PNG built in code, no binary fixtures). Bundled into the image with esbuild
as `seed.js` next to `migrate.js`, SvelteKit virtual modules replaced by shims. Demo data, never
for production.

## Dockerfile

Multi-stage: build with pnpm, runtime distroless or slim Node as non-root, one image serving
`app`, `migrate.js`, `seed.js` and `worker` by command.

## Configuration

Everything in env, documented in `.env.example`, no defaults for secrets. `ORIGIN` is the public
URL. Structured JSON logs with `requestId`, `tenantId`, `userId`; never log payloads of audited
tables. OpenTelemetry hooks in place, no exporter until needed.

## Backup and release

Daily base backup plus WAL archiving, retention per domain requirement. Object store: versioning
plus replication or volume snapshots. Restore rehearsal into a scratch environment, run
`/readyz` and the isolation suite, as part of every release checklist. Release: CI green with
traceability artifact → changelog and tag → migration dry-run on a snapshot → deploy `migrate`
→ roll app instances → smoke → archive artifacts.
