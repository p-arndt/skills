# Database and authentication

Postgres does the work: constraints, triggers, RLS, jsonb, ltree, trigram, recursive CTEs.
Drizzle stays thin; migrations are SQL files, committed and reviewed.

## Standard columns (every business table)

```
id            uuid        PK, UUID v7 (time-ordered, append-friendly B-tree)
tenant_id     text/uuid   NOT NULL, FK tenant RESTRICT      (multi-tenant only, see tenancy.md)
version       int         NOT NULL DEFAULT 1                (optimistic locking, bumped by trigger)
created_at    timestamptz NOT NULL DEFAULT now()
created_by    uuid        NOT NULL DEFAULT current_setting('app.user_id', true)
updated_at    timestamptz NOT NULL DEFAULT now()
updated_by    uuid        NOT NULL DEFAULT current_setting('app.user_id', true)   (set by trigger on update)
deleted_at    timestamptz NULL
deleted_by    uuid        NULL
delete_reason text        NULL
```

Plus: audit trigger, `updated_at/version` trigger, RLS if multi-tenant. One migration helper
(`attach_standard_triggers(table)`) applies them; an integration test enumerates `pg_tables` and
fails when any table lacks them.

Rules:

- Drizzle `text({ enum })` is a TypeScript type only. Every enum column gets a CHECK constraint
  via a shared `enumCheck()` helper, so the database rejects a bad value, not just the service.
- All timestamps `timestamptz`, stored UTC, rendered in the user locale. Pin the connection
  `TimeZone` to UTC because third-party tables (auth) may use `timestamp without time zone`.
- Business ids (`order_no`, `sku`) are separate from the PK, unique per tenant, immutable.
  `UNIQUE (tenant_id, code)` is **not** partial on `deleted_at`: a soft-deleted row keeps its
  code reserved so restore cannot collide.
- Standard partial index for active rows: `(tenant_id, …filter cols) WHERE deleted_at IS NULL`.
- Denormalize what lists display (current status, current location on the row); normalize what
  history proves (event tables). One row per result, not one blob per parent; anything you will
  filter by gets its own column.
- Never `SELECT *` into the app for lists; select what the table shows.

## Audit trail: trigger plus application events

- **Row layer**: one generic PL/pgSQL `AFTER INSERT/UPDATE/DELETE` trigger writes old/new row as
  jsonb, actor from `current_setting('app.user_id')`, tx id, into `audit_row_changes`. Cannot be
  bypassed by application code. Credential-like columns (`password`, `*token*`, `secret`,
  `*_config`) are replaced with `[redacted]`; `changed_cols` is computed first so a rotated secret
  still shows as a change.
- **Business layer**: `history_events (event_type, subject_type, subject_id, payload jsonb,
  reason, actor, occurred_at)` written by `appendHistory(tx, …)` inside the same transaction.
  This is what the UI shows.
- Both tables append-only (app role has no UPDATE/DELETE), partitioned monthly by
  `occurred_at` with a DEFAULT partition, BRIN on `occurred_at`, no foreign keys to business
  tables. `ensure_audit_partitions()` creates current month + 12, run by the migration job and
  once on boot. Retention is `DROP PARTITION`.

## Hierarchies: materialized path from day one

```
parent_id   uuid NULL
root_id     uuid NOT NULL   (= id for roots)
path        ltree NOT NULL  (ids as labels)
depth       smallint NOT NULL
```

`GIST (path)` for subtrees, `(tenant_id, parent_id) WHERE deleted_at IS NULL` for children.
Move rewrites `path`, `root_id`, `depth` for the subtree in one `UPDATE … WHERE path <@ old`.
Descendants `path <@ root.path`, ancestors `path @> node.path`, cycle check
`new_parent.path <@ moving.path`.

## Search

`search_text text GENERATED ALWAYS AS (code || ' ' || name || ' ' || coalesce(description,'')) STORED`
with `GIN (search_text gin_trgm_ops)`. Trigram, not `ILIKE`; no `tsvector` for id-and-name search.
When searching across joined tables, union one id set per source table so each leg uses its index.

## Pagination

Tables: `LIMIT/OFFSET`, sizes 25/50/100, `count(*)` over the same filtered index; offset > 10k
is rejected with a hint to narrow the filter. Timelines (history, revisions): keyset on
`(occurred_at, id)`.

## Migrations

- Drizzle SQL migrations under `drizzle/`, committed, never edited after merge. CI fails if a
  merged migration changes.
- Run by a separate `migrate` job before rollout, never on app boot. `/readyz` fails when the
  schema version is behind.
- Expand/contract for breaking changes: add column → deploy code writing both → backfill →
  remove old. Never destructive in the same release as the code that stops using the column.
- RLS policies and triggers ship in the migration that creates the table.
- Ops-only extensions (`pg_stat_statements`) are not migrations; the app never reads them.

## Roles and privileges

- `app_runtime`: runtime role, not owner, RLS enforced, no DELETE on business tables (soft
  delete only), no UPDATE/DELETE on audit tables, no SELECT on credential tables.
- `migrator`: owns tables, runs migrations.
- `readonly_audit`: SELECT on audit tables for QA.
- The transaction helper does `set local role app_runtime` so dev connections that own the
  tables still get RLS.
- Pool 10 per instance; `instances × pool` under `max_connections − 20`; PgBouncer transaction
  mode above 5 instances (everything uses `set_config(…, true)`, so it is config only).
  Statement timeout 30 s for the app role, 0 for the migrator.

## Authentication (better-auth, no mandatory IdP)

- better-auth is the only auth layer: sessions in Postgres, email + password with policy, magic
  link, TOTP, and per-tenant OIDC via the SSO plugin. Tenant admins register their IdP in
  Settings; no global OIDC env vars. A test IdP container exists only for dev/E2E.
- An IdP provides subject, email, name. Nothing else is read from it: no roles, no groups. All
  authorization data lives in our DB.
- Login routing: email → domain lookup → IdP redirect; else local. A direct `/t/{slug}/login`
  skips the lookup.
- Local sign-in can be disabled per tenant; enforce it in better-auth `hooks.before` for every
  local endpoint, not per login page. Strictest membership wins.
- Onboarding by invitation only: single-use link, token hashed at rest, 7-day expiry; accept
  creates membership and roles in one transaction. Nothing is auto-granted by email domain.
- The first platform operator is bootstrapped from env on an empty database, no-op afterwards
  (operator model in tenancy.md).
- `ORIGIN` is the public URL the browser uses; required for mails and CSRF. Auth cookies are
  non-secure only when `ORIGIN` is `http://`.

## Authorization

- Permission keys `<resource>.<action>`, catalog in `core/permissions.ts` in better-auth
  `createAccessControl` shape; each module owns its keys in `permissions.ts`.
- Roles per tenant (system roles seeded: admin = everything except platform, viewer = every
  `read`). Per-member GRANT/DENY overrides with a mandatory reason, audited.
- Effective permissions, resolved once per request into `ctx.permissions` (shape in backend.md):

  ```
  licensedModules ∩ (⋃ permissions(roles) ∪ overrides(GRANT)) \ overrides(DENY)
  ```

  DENY always wins. Module licensing is described in tenancy.md; without sold modules the first
  term is the full catalog.

## Step-up re-authentication

Critical actions re-verify credentials in the same request flow: password for local accounts,
`prompt=login` at the IdP for SSO. The server action verifies a fresh proof issued seconds
earlier, bound to the user and one action key, single use, handed back in a short-lived HttpOnly
cookie, never on the query string. `reauth_proofs (user_id, action, expires_at, used_at)`; the
audit rows of the transaction carry the consumed proof id. No grace window. Which actions are
gated: backend.md "Service shape".
