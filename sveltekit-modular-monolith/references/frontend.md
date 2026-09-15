# Frontend: the URL is the state, SvelteKit does the work

If a screen cannot be reproduced by pasting its URL into a new tab, it is a bug.

## Where state lives

| State                          | Where               | Example                                        |
| ------------------------------ | ------------------- | ---------------------------------------------- |
| Tenant (if multi-tenant)       | path prefix         | `/t/acme/orders`                               |
| Object                         | path                | `/t/acme/orders/{id}`                          |
| Active tab                     | path segment        | `/t/acme/orders/{id}/history`                  |
| List search/filter/sort/page   | query               | `?q=pump&status=OPEN,BLOCKED&sort=updatedAt:desc&page=2&size=50` |
| Show deleted                   | query               | `?deleted=1`                                   |
| Wizard step                    | path                | `/…/instances/{id}/steps/{stepKey}`            |
| Create / edit                  | path                | `/…/orders/new`, `/…/orders/{id}/edit`         |
| Dialogs, menus, toasts         | local               | not shareable                                  |
| Locale                         | cookie + profile    | never the URL: a link opens in the reader's language |

Rules:

1. Query params are parsed on the server in `load` with a Zod schema per list; invalid values
   fall back to defaults, never 500. Keep one shared `listParamsSchema({ sortable, defaultSort,
   filters })` helper returning `{ q, page, size, sort, filters }`.
2. Defaults are omitted when serializing (`page=1`, `size=25`, default sort are not written).
3. Filter changes: `goto(url, { replaceState: true, keepFocus: true, noScroll: true })`.
   Pagination and sort: plain `goto` so back returns to the previous page.
4. Multi-value filters are comma-separated in one param, not repeated params.
5. Tabs are path segments with their own `+page.server.ts`, each loading only its data.

## SvelteKit idioms (no exceptions without an ADR)

- Data: `+page.server.ts` `load` only. No client-side data library, no `onMount(fetch)`.
- Mutations: form actions + `use:enhance`. Every create/update/delete works without JavaScript
  first. Validation → `fail(400, { form })`; success → `redirect(303, …)`.
- Forms: `sveltekit-superforms` with the same Zod schema the action validates. Schema lives next
  to the route (`schema.ts`) or in `$lib/schemas` when shared.
- Targeted refresh: `depends('app:orders:{id}')` in `load`, `invalidate(...)` after the action.
  Never `invalidateAll()`.
- Errors: `error(403)` / `error(404)` from `load`; `+error.svelte` per route group keeps the shell.
- Streaming: allowed for slow secondary data via returned promises; never for the primary table.
- Server-only code in `$lib/server/**`; let SvelteKit refuse to bundle it.
- `$app/state`, not `$app/stores`.

Route action template:

```ts
export const actions: Actions = {
  default: async ({ request, locals, params }) => {
    const ctx = requireCtx(locals);
    const form = await superValidate(request, zod4(schema));
    if (!form.valid) return fail(400, { form });
    let id: string;
    try {
      id = (await withTenant(scope(ctx), (tx) => createOrder(ctx, tx, form.data))).id;
    } catch (e) {
      if (e instanceof ConflictError) return setError(form, 'code', m['orders.new.codeTaken']());
      if (isHttpError(e, 403)) throw e;
      return message(form, m['orders.form.failed'](), { status: 400 });
    }
    redirect(303, `/t/${params.tenant}/orders/${id}`);
  }
};
```

## Svelte 5 idioms

- Runes only: `$state`, `$derived`, `$props`, `$bindable`. No `export let`, no `$:`.
- `$effect` is a last resort (DOM measurement, third-party libs). Syncing state → `$derived`.
- Snippets (`{#snippet}` / `{@render}`) instead of slots.
- Global reactive state only for shell concerns (sidebar, toasts) in `$lib/state/*.svelte.ts`,
  never for business data.
- Handlers as props (`onclick`, `onselect`), no `createEventDispatcher`.
- Force runes mode in `vite.config.ts` for everything outside `node_modules`.

## Components

1. **shadcn-svelte before anything else.** If shadcn (bits-ui underneath) has it, use it. A
   custom dropdown, dialog or tab strip is a review blocker. Generated primitives in
   `$lib/components/ui/*` are edited for tokens only, never behaviour, and excluded from lint.
2. **One component, one job.** Renders one thing or coordinates children, not both.
   `OrderTable` renders rows; `OrderListPage` wires URL state, data and toolbar. Under ~150
   lines of markup + script, otherwise split.
3. **Props in, events out, no fetching.** Only route components touch `$app/state`.
4. **Pure logic outside components**: formatting, status mapping, filter parsing in plain TS
   under `$lib/utils` / `$lib/schemas`, unit-tested without a DOM.
5. **Every reusable component has a test** (Vitest browser mode + `@testing-library/svelte`):
   render with props, assert roles/labels, fire the handler. Route pages are covered by E2E.
6. **Compose, don't configure.** Snippets and children over boolean prop explosions. Eight
   props to be useful means it is two components.
7. **Loading and empty states are components**: shadcn `Skeleton`, one shared `EmptyState`.
8. "Editor" means canvas, drag and drop, live preview. A stack of inputs is a form, not an editor.

Layer:

```
$lib/components/ui/*      shadcn primitives (generated)
$lib/components/app/*     shell: Sidebar, AppHeader, Breadcrumbs, PageHeader, EmptyState
$lib/components/data/*    DataTable, Toolbar, StatusBadge, KpiCard   (composed from ui/*)
$lib/components/forms/*   FormField, ConfirmDialog, ReasonDialog, Stepper, WizardFrame
$lib/components/<module>/* module-specific composites
src/routes/**/_components/* route-private
```

`DataTable` contract: `rows`, `total`, `columns`, parsed URL state; emits URL changes via `goto`.
TanStack Table headless underneath.

## Design tokens and typography

Semantic colours only, as CSS custom properties in `app.css` (`--status-success`, `--muted`, …);
Tailwind classes reference tokens. No hex in components. Status badges carry text, never colour
alone. Codes and identifiers render in the normal font, not monospace.

## i18n

- Paraglide messages in `messages/<locale>.json`, base locale `en`, keys namespaced by module
  (`orders.list.title`, `common.actions.cancel`). Strategy: cookie → user profile →
  `Accept-Language` → base. Never the URL.
- Master data has `<table>_translations (owner_id, locale, name, description)` resolved
  server-side for the request locale with fallback to base → key.
- Dates, numbers, units via `Intl` in the request locale; timestamps stored UTC.
- `aria-label`s come from messages, not string literals.

## Accessibility baseline

Focus visible everywhere, dialogs trap and return focus, icon-only buttons have `aria-label`,
tables are real `<table>`. Checked with `@axe-core/playwright` in E2E (see testing-ops.md).

Done criteria for a screen: SKILL.md "Definition of done".
