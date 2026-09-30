# Modern CSS toolbox (status late 2026)

**Widely** and **Newly** Baseline features can be used freely. **Limited** features go behind
`@supports` so the fallback still works. Most of these replace a JS library, so prefer them.

| Feature | Status | Use for |
|---|---|---|
| `<dialog>` + `showModal()` | Widely | Modals and sheets: native focus trap, Esc, `::backdrop`, inert background |
| Popover API | Newly | Menus, pickers, toasts. Top layer, light dismiss, no z-index fights |
| Anchor positioning | Newly | Tooltips and dropdowns without Floating UI |
| `@starting-style` + `allow-discrete` | Newly | Enter/exit animation on dialogs and popovers |
| View Transitions (same-document) | Newly | List→detail morphs, reorders, theme switch |
| View Transitions (cross-document) | Limited | MPA page transitions, as progressive enhancement |
| Container queries (`@container`, `cqi`) | Widely | Components that adapt to their slot |
| Style queries (`@container style(--x: y)`) | Newly | Variant switches via custom properties |
| `:has()` | Widely | Parent state: `.field:has(:invalid)`, `body:has(dialog[open])` |
| OKLCH, `color-mix()` | Widely | Even palettes, tints, hover states from one token |
| Relative color syntax | Newly | `oklch(from var(--accent) calc(l - .08) c h)` |
| `light-dark()` | Newly | One-line light/dark tokens |
| `text-wrap: balance` | Newly | Headlines |
| `text-wrap: pretty` | Limited | Body text (degrades harmlessly) |
| `field-sizing: content` | Newly | Auto-growing textareas |
| `interpolate-size: allow-keywords` | Limited | Animating to `height: auto` (snaps elsewhere, which is fine) |
| Scroll-driven animations | Limited | Reading progress, reveal on scroll. Wrap in `@supports (animation-timeline: view())` |
| `@layer`, native nesting, subgrid, `@property` | Widely / Newly | Cascade control, scoped CSS, aligned card internals, animatable custom props |
| Customizable `<select>` (`appearance: base-select`) | Limited | Styled native select, falls back to a normal select |

## Snippets

```css
/* dialog / popover enter + exit without JS */
dialog, [popover] {
  opacity: 0; translate: 0 8px;
  transition: opacity .18s var(--ease-out), translate .18s var(--ease-out),
              display .18s allow-discrete, overlay .18s allow-discrete;
}
dialog[open], [popover]:popover-open {
  opacity: 1; translate: 0 0;
  @starting-style { opacity: 0; translate: 0 8px; }
}
dialog::backdrop { background: oklch(0.2 0.01 260 / .4); }

/* anchored menu */
.menu-trigger { anchor-name: --menu; }
.menu { position: absolute; position-anchor: --menu; position-area: bottom span-right;
        position-try-fallbacks: flip-block; margin-top: 4px; }

/* list → detail morph */
.row[data-id="42"] .title { view-transition-name: record-title; }
/* JS: document.startViewTransition(() => render(detail)) */

/* component adapts to its container */
.card-slot { container: card / inline-size; }
@container card (width > 32rem) { .card { grid-template-columns: 8rem 1fr; } }

/* validation styling without JS */
.field:has(input[aria-invalid="true"]) label { color: var(--danger-text); }

textarea { field-sizing: content; min-block-size: 3lh; max-block-size: 12lh; }
h1, h2, h3 { text-wrap: balance; }

/* blunt global fallback. Better: write movement inside
   @media (prefers-reduced-motion: no-preference) and keep plain fades outside it (motion.md) */
@media (prefers-reduced-motion: reduce) {
  *, ::before, ::after { animation-duration: .01ms !important; transition-duration: .01ms !important; }
  ::view-transition-group(*) { animation: none !important; }
}
```

Toast region: `<div popover="manual" aria-live="polite">`, opened with `showPopover()`, puts
toasts in the top layer. The top layer stacks in the order things opened, so a toast only sits
above a modal dialog opened *before* it. Call `hidePopover(); showPopover()` on each toast to
keep it on top.
