# Tenancy

Load this file only when the tenancy question was answered with "multi-tenant with RLS" (all
sections) or "tenant as a plain column" (all sections except RLS).

## Data model

- Every business table carries `tenant_id NOT NULL` with a FK to the tenant table (RESTRICT).
- Users are **not** tenant-scoped. `membership (user_id, tenant_id, role, is_tenant_admin)`
  carries the relation; everything hangs off the membership, not the user. A user in N tenants is
  then additive, and cross-tenant access later is a routing change, not a data migration.
- `tenant_id` leads every index and every unique constraint: `(tenant_id, status)`,
  `UNIQUE (tenant_id, code)`. An index that does not start with it is only half usable under RLS.
- Object storage keys start with the tenant id, so per-tenant bucket policies stay possible.
- Referential integrity bypasses RLS: a plain `x_id` FK accepts an id from another tenant.
  Columns filled straight from user input therefore use a composite FK
  `(tenant_id, x_id) → (tenant_id, id)`, which needs `UNIQUE (tenant_id, id)` on the target.
  Where the service already resolved the id through a tenant-scoped read, the plain FK is enough.
  Polymorphic `(owner_type, owner_id)` links cannot be FKs and are checked in the service.
- Rejected alternatives: schema-per-tenant (migration cost), database-per-tenant (ops cost).

## RLS

- `ALTER TABLE t ENABLE ROW LEVEL SECURITY` plus one policy per table:
  `USING (tenant_id = current_setting('app.tenant_id', true))`. A single column comparison, no
  subqueries, no function calls that hide the predicate from the planner. Membership checks
  happen in the app, not in the policy.
- The app sets the tenant per transaction with `set_config('app.tenant_id', $1, true)`
  (equals `SET LOCAL`; parameterizable; PgBouncer-safe). Never session-level `SET`.
- The transaction helper switches to the non-owner role `app_runtime` first, so RLS applies even
  when the connection user owns the tables.
- A forgotten `WHERE tenant_id` cannot leak data. That is the point; the app-level filter is
  still written for the planner, not for safety.
- Platform-level work (tenant provisioning, login) uses `withPlatform(userId, fn)`: same role,
  no tenant set, RLS tables return nothing. Intended.
- A migration helper `enable_tenant_rls(table)` applies both statements. The table-enumeration
  test and the tenant isolation suite (testing-ops.md, mandatory suites 1 and 2) prove it.

## URL prefix

- Tenant slug is a path prefix from day one: `/t/{slug}/...`. `hooks.server.ts` resolves the
  slug, verifies membership, builds `ctx`. A cookie remembers the last tenant so `/` redirects.
- Route groups: `(app)/t/[tenant]/...` for tenant screens, `(auth)/...` for login, invite, reauth,
  `(platform)/admin/...` for the operator.
- Login can be tenant-direct via `/t/{slug}/login` (bookmarks, shared devices) or routed by email
  domain through the tenant's registered IdP.

## Licensing and self-service

- Feature modules per tenant in `tenant_modules (tenant_id, module_key, valid_from, valid_until,
  granted_by, note)`: validity periods, not booleans, so the audit shows when. Enabling requires
  the module's dependencies; disabling hides navigation and 403s routes, never deletes data.
- Tenant admin may within the own tenant: manage non-system roles, assign roles, set per-member
  GRANT/DENY overrides with a reason, invite members, configure SSO, enforce MFA, disable local
  login. May not license modules.
- Platform operator: a global user column, never a tenant role, so no tenant admin can grant
  it. Own admin area; creates tenants, licenses modules, read-only audited support access.
  Bootstrap of the first operator: database-auth.md "Authentication".

Context shape and permission resolution: backend.md "Request context" and database-auth.md
"Authorization".
