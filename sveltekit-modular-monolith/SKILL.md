---
name: sveltekit-modular-monolith
description: 'Architecture and design rules for a SvelteKit + Drizzle + Postgres + shadcn-svelte fullstack app built as a modular monolith. Manual use only: /sveltekit-modular-monolith when starting a new project, adding a module or screen, or deciding where code belongs. Asks about tenancy first, then applies backend, frontend, database/auth and testing/operations rules from the references.'
argument-hint: '[new | module <name> | screen <name> | review <path>]'
---

# sveltekit-modular-monolith

One process, one database, modules as folders with a narrow public surface, thin routes, the URL
as the state. Everything below is distilled from a production SvelteKit app; the rules are the
ones that were expensive to retrofit, so they are decided up front.

## Usage

```
/sveltekit-modular-monolith                 apply the rules to whatever is being built now
/sveltekit-modular-monolith new             scaffold a fresh project skeleton
/sveltekit-modular-monolith module <name>   add a server module with its five files
/sveltekit-modular-monolith screen <name>   add a route with load, action and page
/sveltekit-modular-monolith review <path>   check existing code against the rules
```

## Step 1 — ask about tenancy (always, before anything else)

Use `AskUserQuestion`, one question, single select, unless the project already documents its
choice (look for `tenant_id` in migrations or an ADR in `docs/`). Options:

1. **Multi-tenant with Row Level Security (Recommended for SaaS)** — every business table
   carries `tenant_id`, Postgres RLS enforces isolation, tenant slug is a URL prefix.
   Load [references/tenancy.md](references/tenancy.md) and apply it on top of everything else.
2. **Single tenant** — no `tenant_id`, no RLS, no URL prefix. Skip tenancy.md entirely; where the
   other references mention `tenant_id` or `ctx.tenantId`, drop the tenant part (indexes lose
   their leading `tenant_id`, `membershipId` and `tenantSlug` leave the ctx).
3. **Tenant as a plain column** — `tenant_id` on every table and in every `WHERE`, but no RLS and
   no DB role switch. Apply tenancy.md except the "RLS" section.

Naming that follows from the answer: the transaction helper is `withTenant(scope, fn)` plus
`withPlatform(userId, fn)` for cross-tenant work in options 1 and 3, and a single
`withActor(userId, fn)` in option 2. The references use the multi-tenant names.

Record the answer at the top of the project's architecture doc so the question is not asked twice.

## Step 2 — load the references you need

| Working on                                    | Read                                                   |
| --------------------------------------------- | ------------------------------------------------------ |
| Server module, service, repo, permissions     | [references/backend.md](references/backend.md)         |
| Route, page, component, form, URL state, i18n | [references/frontend.md](references/frontend.md)       |
| Table, migration, index, auth, audit          | [references/database-auth.md](references/database-auth.md) |
| Tests, CI, Docker, seeds, health endpoints    | [references/testing-ops.md](references/testing-ops.md) |
| Anything, if multi-tenant                     | [references/tenancy.md](references/tenancy.md)         |

For `new`, read all of them. For `review`, read the ones matching the path and report
violations as a list of `file:line — rule — fix`, nothing else.

## The ten rules that carry the weight

1. **No separate backend.** SvelteKit fullstack, `adapter-node`. Business writes that must be
   atomic run in one `db.transaction()`; an HTTP hop would make that hard. Add versioned
   `/api/v1/*` routes inside SvelteKit if an external client appears, never a second service.
2. **Modules are folders** under `src/lib/server/modules/<module>/` with `schema.ts`, `service.ts`,
   `repo.ts`, `permissions.ts`, `events.ts`. `service.ts` and `permissions.ts` are the public
   surface. Nothing outside the module imports its `repo*` or `schema*`, enforced by ESLint
   `no-restricted-imports`. Schema-to-schema edges are the one permanent exemption (Drizzle
   `references()` needs the table object).
3. **Routes are thin**: auth → parse (Zod) → service → return or redirect. Services never import
   `RequestEvent`; routes never contain business rules.
4. **Every service method takes `ctx` first** and calls `assertPermission(ctx, key)` before doing
   anything. `ctx` is built once per request in `hooks.server.ts` and lives on `locals.ctx`.
5. **Every write goes through the transaction helper.** There is no other way to obtain a
   transaction. It sets the DB role and the actor for audit triggers.
6. **The URL is the state.** Tabs are path segments, filters are query params parsed on the
   server with a Zod schema per list, defaults omitted, invalid values fall back and never 500.
7. **SvelteKit does the work.** `+page.server.ts` `load` for data, form actions with
   `use:enhance` for mutations, works without JavaScript first. No client fetching library,
   no `onMount(fetch)`, no `invalidateAll()`.
8. **shadcn-svelte first, small, testable components.** Props in, handler props out, no fetching
   inside reusable components, one job per component, under ~150 lines, one test each.
9. **Every business table** has UUID v7 id, `version`, `created_at/by`, `updated_at/by`,
   `deleted_at/by/reason`, an audit trigger, and enum CHECK constraints. Migrations are committed
   SQL, run by a separate job before rollout, never edited after merge.
10. **No mocks of the database.** Integration tests run on real Postgres via Testcontainers, one
    container per run, through the same transaction helper production uses.

## Definition of done for a slice

The single checklist; the references do not repeat it.

1. Paste the URL into a new tab → same screen, same filters, same tab, same step.
2. Read and the primary form action work with JavaScript disabled.
3. Back button does what a user expects.
4. Permission-gated actions are absent, not disabled, without the permission.
5. Every string exists in every locale.
6. Every history-relevant mutation appends a typed event in the same transaction.
7. A new table has its standard columns, triggers and (if multi-tenant) RLS policy; the
   table-enumeration test passes.
8. A new reusable component uses shadcn primitives and ships with a component test.

## Things deliberately not built until measured

Counter columns, caches holding business state, read replicas, materialized views, partitioning
of business tables, cross-request permission caches, configuration flags for a gate that is one
line in a route today. Measure first (`pg_stat_statements` on from day one, a p95 gate in the
integration suite), then add.
