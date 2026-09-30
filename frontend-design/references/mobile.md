# Mobile and responsive

Web and native both. Most numbers come from Apple HIG (iOS 26), Material 3 Expressive, and NN/g.

## Shell by width

| Window | Width | Primary nav |
|---|---|---|
| Compact | < 640px | Bottom tab bar |
| Medium | 640–839px | Rail, or tab bar with labels beside the icons |
| Expanded+ | ≥ 840px | Sidebar or rail |

Use media queries only for the shell. Components adapt to their slot with `@container`.

## Navigation

- Use a **bottom tab bar** for 3–5 top-level destinations.
  - Label every tab with one word. Don't add a "More" tab, because it hides content.
  - The tab bar is for navigation only. Page actions go in a toolbar.
  - Keep it visible across top-level sections.
- **Current look:** a floating, inset capsule (iOS 26 Liquid Glass, M3 flexible nav bar 64dp)
  with a pill-shaped active indicator. It may shrink into a small pill on scroll-down and
  come back on scroll-up. Content scrolls under it, so pad the bottom of the page.
- Use a hamburger or drawer only for secondary destinations (settings, accounts,
  workspaces). Primary nav behind a hamburger hurts discoverability.
- **Top bar:** a large title that collapses to an inline title on scroll. Back on the
  leading edge, 1–2 actions on the trailing edge.

## Sheets and modals

- Use a **bottom sheet** for short tasks that need the parent context: filters, pickers,
  share, quick create, row actions.
- Use a **full-screen modal** for long or multi-step flows, editors, and anything with a
  lot of keyboard input.
- **Detents:** medium (~50%) and large.
  - Show a grabber (36×5px) on resizable sheets.
  - Always add a visible close button as well, and close the sheet on browser Back.
- **Buttons:** Cancel on the leading edge, Done or Save on the trailing edge. In later
  steps of a multi-step sheet, Back replaces Cancel.
- **Dismissal:** swiping down dismisses. If there are unsaved changes, confirm first.
- **One sheet at a time.** Never stack sheets.
- **Scrim:** a dim scrim of 30–40% black. A non-modal tool sheet has no scrim.

## Lists and actions

- **Touch targets:** 44×44px minimum, and 48px on Android. Keep ≥ 8px between targets. A 20px
  icon is fine if its hit area is padded out.
- **Thumb zone:** primary actions go in the bottom third (tab bar, FAB, sticky CTA, bottom
  search). Destructive and rare actions go at the top.
- **Rows:** 44–56px for one line, 64–72px for two lines.
  - Layout: leading avatar or icon, then title and secondary text, then trailing metadata
    or chevron.
  - Separators are inset to start at the text. The whole row is tappable.
- **Swipe actions:**
  - Trailing swipe for destructive or archive actions. Leading swipe for status (done, pin).
  - 1–3 actions per side, and a full swipe runs the first one.
  - Swipes are invisible, so **always mirror them** in a long-press menu or a `⋯` button.
  - Offer Undo instead of a confirm.
- **FAB:** one per screen, only for the single primary creative action. 56px, placed 16px
  from the corner. An extended FAB collapses to icon-only on scroll.
- **Pull to refresh:** only on remote or chronological lists.

## Forms

- Set the input type, `inputmode`, `autocomplete` and `enterkeyhint` on every field. Use
  `inputmode="numeric"` rather than `type=number` for codes and card numbers.
- Input font size must be **≥ 16px**, or iOS zooms in on focus.
- Single column, labels above fields, inputs 44–48px tall. Use a segmented control instead
  of a select for ≤ 5 options. Use native date pickers.
- The primary button is pinned at the bottom, full width, with padding for the safe area,
  and rides above the keyboard.

## Desktop → mobile

| Desktop | Mobile |
|---|---|
| Sidebar | Tab bar (≤ 5), with secondary items under a profile or More screen |
| Table | Two-line list rows: title, 2–3 key fields as meta, a status badge. Tap opens the detail. |
| Table that must stay a table | Horizontal scroll, sticky first column, visible scroll hint |
| Modal dialog | Bottom sheet (short) or full-screen (long) |
| Dropdown or action menu | Bottom sheet list or action sheet |
| Hover-revealed actions, tooltips | Always-visible icon, long-press menu, swipe |
| Right-click menu | Long-press menu |
| List + detail side by side | Push navigation (list → detail) |
| Filter sidebar | "Filter (2)" button → full-height sheet with a sticky "Show 24 results" |
| Inline cell edit | Tap the row → edit sheet |
| ⌘K palette | Search tab or search field |
| Breadcrumbs | Back button labeled with the parent title |
| Drag to reorder | Long-press to lift, or an explicit Reorder mode |

## Motion

- Motion shows where things come from: sheets slide up, pushes slide in from the trailing
  edge, and a card morphs into its detail.
- **Durations:** micro 100–200ms, sheets and navigation 250–400ms. Use a spring-like
  ease-out, never linear.
- **Pressed state** within 100ms: `scale(.97)` or a tint.
- Every gesture has a visible button equivalent. Never hijack the edge swipe.
- **Celebration** only at real milestones.

## Web implementation

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, interactive-widget=resizes-content">
```

```css
html { background: var(--bg); }            /* Safari 26 tints its chrome from this */
.app { min-height: 100dvh; }                /* never bare 100vh on mobile */
.tabbar, .sticky-cta, .sheet {
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
}
.sheet, .modal-body, .scroller { overscroll-behavior: contain; }
button, a { touch-action: manipulation; -webkit-tap-highlight-color: transparent; }
@media (hover: hover) and (pointer: fine) { .row:hover { background: var(--bg-hover); } }
@media (pointer: coarse) { .icon-btn { min-width: 44px; min-height: 44px; } }

/* <dialog> as bottom sheet on compact screens */
@media (width < 640px) {
  dialog.sheet {
    margin: auto 0 0; width: 100%; max-width: none; max-height: 90dvh;
    border-radius: 20px 20px 0 0;
  }
}
```

- **Glass (`backdrop-filter`) costs** performance and contrast. Give it an opaque fallback
  under `@media (prefers-reduced-transparency: reduce)`.
- **Safari 26:** put glass on an absolutely positioned child of the fixed bar, not on the
  bar itself. Keep the document scrollable instead of `body { overflow: hidden }`.
