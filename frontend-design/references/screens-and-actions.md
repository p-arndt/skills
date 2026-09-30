# Screens and actions

How data apps implement browse, view, create, edit, delete and the states around them.
Reference products: Linear, Attio, Notion, GitHub, Vercel, Stripe. Be decisive: use the
default unless the listed condition for deviating applies.

## Browse (index screens)

**Pick the form from the data, not from taste.**

| Form | Use when | Spec |
|---|---|---|
| Table | Users compare values across items, or a record has 4+ scannable attributes | Sticky header (and first column if wide). A wrapper with `overflow-x: auto` breaks page-level sticky, so use `overflow-x: clip` or make the wrapper the scroll container with its own max-height. Numbers right-aligned, `font-variant-numeric: tabular-nums`. Row 40px, compact 32px. Truncate + tooltip, never wrap. Empty cell = muted `—`. |
| List rows | One primary title + a few properties | 36–44px rows. Title left, metadata right-aligned and muted, as small chips/icons. |
| Cards / grid | The visual *is* the content (files, media, thumbnails) | If a card is a title plus three fields, it should have been a row. |
| Board | Alternate view grouped by status | Never the only view. |

- Whole row is clickable and opens the detail. Links inside cells stay separately clickable.
- **Filters:** a toolbar with search (debounce 200–300ms) and "+ Filter", producing
  removable chips `Status is Active ×`. Each part of a chip is editable. Filters apply
  instantly, with no "Apply" button. Mirror filters, sort and view in the URL. Show
  the result count.
- **Sort:** header click cycles asc → desc → none and shows an arrow on the active column.
  In list views, put sort and grouping in a "Display" popover.
- **Saved views:** filters, sort, grouping and columns together make a view. Views go as
  tabs above the list or in the sidebar. A modified view shows "Save / Save as new / Reset",
  and is never overwritten silently.
- **Bulk selection:** checkbox on row hover (or a leading column in tables). Shift-click
  selects a range. Header checkbox selects the page, then offers "Select all 1,240". Any
  selection brings up a floating bar at bottom center: count, 2–3 main actions, overflow,
  Clear (Esc).
- **Paging:** continuous (virtualized) scroll for lists users work through. Keep the scroll
  position when coming back from a detail. Use cursor pagination with a count for
  audit-style or search lists. Use "Load more" for feeds. Never combine infinite scroll
  with a footer.

## View (detail screens)

- **Two columns:** main content on the left (title, description, activity). A properties
  sidebar of 280–320px on the right, with label/value pairs that are each editable in place.
- The header holds breadcrumb, title, status and one primary action. Everything else sits
  behind a `⋯` menu, which has the same items and order as the row's right-click menu.
- An activity timeline at the bottom: who changed what, when, in relative time with the
  absolute time on hover.
- **Peek:** a side panel (480–640px) that keeps list context. `Space` or a click opens it,
  `↑/↓` moves between records while it stays open, `Esc` closes, and an "expand" control
  opens the full page.
- **Peek width behavior.** From 1280px the peek pushes the list, which narrows. Below that
  it overlays. Under 640px there is no peek, and a tap pushes to the detail. Put the table in
  a container query so it turns into list rows when the peek narrows it.
- **Every detail has a URL**, including in a panel or modal. Back must work.
- Never build a read-only detail page that needs an "Edit" click to change anything.

## Create

| Surface | Use when | Avoid when |
|---|---|---|
| **Inline** (new row in place) | Only a title is required, creation is frequent, list context matters | Several required fields |
| **Modal** | 1–6 fields, quick create from anywhere (`c`) | Long forms, multi-step, needs other data visible |
| **Sheet / side panel** (400–640px, right) | Medium form while looking at the list or parent | Complex, multi-section work |
| **Full page** | Long or complex forms, wizards, rich content, needs a URL mid-flow | Frequent quick creates |

- Pick the lightest surface that fits the **required** fields. Ask for the minimum and let
  users set the rest on the detail view.
- After creating: stay in context with a toast ("Created · View →"), or navigate to the
  new record. If the new item is visible on screen (inline create), skip the toast: highlight
  the row and announce it with `aria-live` instead. Toast only when filters hide the new item. Pick one rule per product and apply it everywhere.
- Offer "Create another" for batch entry. `⌘/Ctrl+Enter` submits. `Esc` on a dirty form
  asks "Discard draft?" or keeps the draft.
- **Wizards:** only when later steps depend on earlier answers. Put them on a full page with
  "Step 2 of 4", keep them to 3–5 steps, and end with a review step. Back never loses data.
  Never put a wizard in a modal, and never stack a modal on a modal.

## Edit

- **Default: always editable, no edit mode.** Click the title to edit it in place. Click a
  property to open a popover picker. Hover shows editability with a background tint.
- **Autosave** for single-value controls (toggle, select, status, date) and document
  bodies. Debounce text 500–1000ms and save on blur. Show a quiet "Saving… / Saved"
  indicator. No autosave without that indicator.
- **Explicit save** when several fields form one transaction or have side effects
  (billing, permissions, API keys, anything that emails or charges). **Never mix autosave
  and explicit save in one form.**
- **Settings:** one card per section, each with its own Save in the card footer, instead of
  one global Save at the bottom of a long page.
- **Dirty state:** a sticky bar "Unsaved changes · Discard · Save". With per-section saves, the
  bar's button is "Save all" and saves every dirty section. Guard navigation and
  `beforeunload`. Keep Save **enabled** and validate on click. The one exception is type-to-confirm: its
  danger button stays disabled until the typed name matches.
- **Cell edit:** Enter or double-click opens the editor. Enter commits and moves down, Tab
  commits and moves right, Esc reverts. Blur commits. Errors stay inside the cell.
- A failed save keeps the input and shows the error next to it.

## Delete

- **Reversible and frequent** (archive, remove, trash): act immediately, then show an undo
  toast "Deleted · Undo" for 8–10s. Soft-delete on the server.
- **Irreversible or high blast radius:** a confirm dialog.
  - The title names the object: "Delete project 'acme-web'?"
  - The body states the consequence with counts: "This deletes 214 issues. This can't be undone."
  - The buttons are verbs: `Delete project` (danger) and `Cancel`. Initial focus is on Cancel.
- **Most destructive** (repo, workspace, project): type-to-confirm, inside a red-bordered
  "Danger zone" as the last section of settings.
- Never write "Are you sure?" with Yes/No. Never confirm trivial deletes: it trains
  users to click through.

## Feedback states

**Loading.** Show nothing for under ~300ms, and delay indicators by 200ms so they don't flash.
For a page or list, show a **skeleton that matches the real layout**: row heights, column
widths, avatar circles. Use a static skeleton under reduced motion. For one button or
component, show a spinner in place: keep the button width and block double submits. Beyond
10s, show a determinate progress bar and let the user move on.

**Optimistic UI** is the default for low-risk mutations: status, assign, reorder, toggle,
comment. Update the UI at once. On failure, roll back and show an error toast with Retry.
Don't use it for payments or permissions.

**Validation.** Reward early, punish late:
- Validate on blur, and only if the field is non-empty. Once a field is in error,
  re-validate on every keystroke so the error clears as soon as it is fixed.
- Validate everything on submit, then focus the first invalid field. Never show
  "required" before the first submit.
- The message goes under the field with an icon, and the field gets `aria-invalid` and
  `aria-describedby`. Say how to fix it: "Enter an email like name@example.com", not
  "Invalid input".
- Long forms also get an error summary at the top that links to each field.

**Errors.** Show them inline, in the region that failed ("Couldn't load invoices · Retry"),
while the rest of the page keeps working. Use a banner for page-level problems, and a toast
only when the failure has no place on screen. Never clear a form on error.

**Toasts.** Only for results that aren't visible on screen, or to offer Undo.
- Place them bottom-right, stack at most 3, and announce them with `aria-live="polite"`.
- 4–6s, or 8–10s when there is an action. Pause on hover or focus.
- Errors never auto-dismiss.
- Don't toast a change the user can already see.

**Empty states come in three kinds.** Keep the page chrome (toolbar, filters) visible in all
three.
1. *First use:* what this is, why it matters, one primary CTA, optionally Import or docs.
   A preview of the filled UI is fine.
2. *No results:* "No customers match 'acme' and 2 filters", with a Clear filters action.
   No illustration and no first-use CTA.
3. *Done / inbox zero:* short, rewarding copy, no CTA.

## Navigation

- **Left sidebar** of 220–260px, collapsible with `[`. From top to bottom: workspace
  switcher, search / ⌘K, personal items (Inbox, My items), pinned views, main sections, then
  settings and help at the bottom. At most 2 nesting levels. Show counts only on
  actionable items.
- **Top tabs** for sub-views of one object (Overview / Activity / Settings). Tabs change the URL.
- **Breadcrumbs** from 2+ levels deep. The last segment is the page title.
- **Settings:** a left settings nav (Account / Workspace / Members / Billing / API), with a
  content column of 640–720px. Each setting is a label plus a one-line description plus
  the control. The danger zone comes last.
- Never use a hamburger on desktop, and never duplicate the sidebar in tabs.

## Power-user layer

- **⌘K palette.** The same shortcut everywhere. Search is fuzzy.
  - It reaches every action and navigation target, including settings.
  - Actions for the current selection rank first. Each row shows its icon and its
    shortcut, which teaches the shortcut.
  - Recent items appear on open. Arguments open nested pages ("Assign to… → people").
  - About 640px wide, placed about 18% from the top. It must open instantly.
- **Single-key shortcuts,** disabled while an input has focus:
  - `c` create, `e` edit, `/` search, `j/k` move, `Enter` open, `x` select, `Esc` close,
    `?` shortcut sheet.
  - Sequences like `g i`.
  - Show them in tooltips ("Create  C") and in menus.
- **Right-click** on a row opens the same menu as its `⋯` button.
- The keyboard-selected row gets a visible focus ring.
