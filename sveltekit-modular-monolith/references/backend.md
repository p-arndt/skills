# Backend: modular monolith on SvelteKit

## Layout

```
src/lib/server/
  db/
    index.ts        drizzle client (postgres.js pool, max 10, TimeZone pinned to UTC)
    schema.ts       barrel re-exporting every module's tables (only place allowed to import all)
    columns.ts      standard column helpers, enumCheck()
    tenant.ts       withTenant / withPlatform — the only way to get a transaction
    history.ts      appendHistory(tx, event)
    migrate.ts      migration runner, built into the image as migrate.js
  ctx.ts            RequestCtx, can(), assertPermission(), forbidden(), requireCtx()
  modules/
    core/           ctx resolution, permission catalog, module registry
    auth/           sign-in policy, step-up re-auth proofs
    <module>/
      schema.ts     drizzle tables (internal)
      service.ts    business logic, no HTTP awareness (public)
      repo.ts       queries incl. hand-written SQL / recursive CTEs (internal)
      permissions.ts  permission keys owned by this module (public)
      events.ts     history event types + subject constants owned by this module
      *.test.ts     unit tests for pure logic
      *.integration.test.ts  real-DB tests
  seed/             idempotent dev/E2E seed as code, bundled as seed.js
  storage/          Storage interface: s3 | fs | memory drivers
  test/             globalSetup (Testcontainers), setup, testDb helpers
src/hooks.server.ts session → tenant → ctx → locals
src/routes/...      thin
```

## Module boundaries (ESLint, not convention)

`eslint.config.js` restricts imports of `**/modules/<m>/repo*` and `**/modules/<m>/schema*` for
everything outside module `<m>`. Start at `error` in a new project. Exempt: the schema barrel,
`modules/*/schema.ts` (foreign keys), seeds, `*.test.ts`.

```js
const MODULES = ['core', 'auth', 'orders', ...];
const internals = (m) => [`**/modules/${m}/repo`, `**/modules/${m}/repo.*`,
  `**/modules/${m}/schema`, `**/modules/${m}/schema.*`, `../${m}/repo`, `../${m}/repo.*`,
  `../${m}/schema`, `../${m}/schema.*`];
// outside modules: all internals forbidden; inside module m: every other module's internals forbidden
```

Cross-module needs go through the other module's `service.ts`. If two modules need each other's
services in both directions, one of them is the wrong module; move the shared part down into
`core` or merge them.

Svelte components declare their own row types instead of `typeof table.$inferSelect`, so a
column rename is a migration plus a `load`, not a component change.

## Request context

The one definition; tenancy.md and database-auth.md refer here.

```ts
export interface RequestCtx {
  userId: string;
  tenantId: string;        // multi-tenant only
  tenantSlug: string;      // multi-tenant only
  membershipId: string;    // multi-tenant only
  isTenantAdmin: boolean;
  permissions: ReadonlySet<string>;
  modules: ReadonlySet<string>;   // licensed feature modules, if you sell modules
  locale: string;
}
export const can = (ctx, key) => ctx.permissions.has(key);
export function assertPermission(ctx, key) { if (!can(ctx, key)) throw forbidden(`Missing permission ${key}`); }
export const scope = (ctx) => ({ tenantId: ctx.tenantId, userId: ctx.userId });
```

`forbidden()` produces a SvelteKit `error(403)` with a message so loads and actions render the 403
page, not a 500, and logs still see the reason. `requireCtx(locals)` replaces `locals.ctx!` at
call sites. Built once per request in `hooks.server.ts` from the resolution in
database-auth.md "Authorization"; no cross-request cache until measured.

A platform-operator context (works across tenants, minted only from a global user column) is a
separate type so it cannot be passed where a tenant ctx is expected.

## Transaction helper

```ts
export async function withTenant<T>(scope: { tenantId; userId; reauthProofId? }, fn: (tx: Tx) => Promise<T>) {
  return db.transaction(async (tx) => {
    await tx.execute(sql`set local role app_runtime`);          // non-owner role so RLS applies
    await tx.execute(sql`select set_config('app.tenant_id', ${scope.tenantId}, true),
                                set_config('app.user_id', ${scope.userId}, true)`);
    return fn(tx);
  });
}
```

`set_config(..., true)` equals `SET LOCAL` but is parameterizable and survives PgBouncer
transaction pooling. `withPlatform(userId, fn)` is the same without a tenant, for provisioning
and login flows. Services receive `(ctx, tx, input)`; they never open transactions themselves,
so a route can compose several service calls into one atomic unit.

## Service shape

```ts
// service.ts
// ---- pure: exported, unit-tested without DB
export const TRANSITIONS: Record<Status, readonly Status[]> = { DRAFT: ['ACTIVE'], ACTIVE: ['ARCHIVED'], ARCHIVED: [] };
export function assertTransition(from, to) { if (!TRANSITIONS[from].includes(to)) throw new ConflictError(...); }

// ---- public: (ctx, tx, input) → typed row; permission check first, history event inside the tx
export async function createOrder(ctx: RequestCtx, tx: Tx, input: NewOrder) {
  assertPermission(ctx, P.create);
  const row = await repo.insertOrder(tx, ...);
  await appendHistory(tx, { eventType: E.ORDER_CREATED, subjectType: SUBJECT_ORDER, subjectId: row.id });
  return row;
}
```

- Typed error classes (`ConflictError`, `NotFoundError`) for outcomes the route maps to form
  errors; permission failures throw the 403 directly.
- Optimistic locking: mutable entities carry `version`; update takes the version the caller read
  and fails with a conflict when stale. No silent overwrite.
- Soft delete only: `deleted_at`, `deleted_by`, `delete_reason`. Default reads filter
  `deleted_at IS NULL`; restore is a separate permission.
- Status machines are a transition table plus a DB trigger that rejects anything not in it, so
  no code path (import, job, manual) can skip a state.
- Hierarchies: the service maintains the materialized `path` on insert and move (schema in
  database-auth.md). Recursive CTEs stay hand-written in `repo.ts`, never forced through the
  query builder.
- Revisions of a document-like entity: immutable jsonb snapshots, diff computed at read time.
  A DB trigger freezes the snapshot once the revision leaves DRAFT.
- Critical actions (approve, delete, permission overrides, auth settings) are gated by one line
  in the route action, `requireReauth(event, 'orders.approve')`; mechanics in database-auth.md
  "Step-up re-authentication". Keep the gated list short and in one place; a quick shop-floor
  path is never gated per step.

## Permissions and events per module

```ts
// permissions.ts — keys are <resource>.<action>; the catalog in core maps resource → module
export const ORDER_PERMISSIONS = { read: 'orders.read', create: 'orders.create', ... } as const;
// events.ts
export const ORDER_EVENTS = { ORDER_CREATED: 'ORDER_CREATED', ORDER_SHIPPED: 'ORDER_SHIPPED' } as const;
export const SUBJECT_ORDER = 'order';
```

UI hides what the user cannot do; the server check is the real one.

## Background work

pg-boss in Postgres, no Redis. Long imports/exports run in a worker using the same image. Chunks
of 1–5k rows, one transaction per chunk, `INSERT … ON CONFLICT` keyed by business id, one history
event per chunk.

## Files

`Storage` interface (`put`, `get`, `head`, `presignGet`, `delete`) with S3 as the production
driver and `fs` / `memory` for dev and tests. Object key `{ownerType}/{ownerId}/{docId}`, prefixed
with the tenant id when multi-tenant. SHA-256 on upload stored with the row.
