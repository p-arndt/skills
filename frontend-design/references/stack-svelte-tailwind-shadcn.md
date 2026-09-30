# SvelteKit + Tailwind v4 + shadcn-svelte

shadcn out of the box **is** the generic look: zinc greys, radius 0.625rem, Inter-ish system
font, no motion. Using it is right, because you get accessible behavior (bits-ui) for free.
Shipping its defaults is wrong. The work is to theme it from the direction and then add the
motion and detail it lacks.

If the repo also follows `sveltekit-modular-monolith`, its rules win where they overlap
(for example: primitives in `$lib/components/ui/*` are edited for tokens and styling only,
never behavior, and codes render in the normal font).

## 1. Tokens → shadcn variables → Tailwind

Take the knobs and semantic tokens from `tokens.md`, with **two renames** because shadcn
already uses those names with a different meaning:

- the brand accent `--accent*` from tokens.md becomes `--brand*` (`--brand`, `--brand-hover`,
  `--brand-fg`, `--brand-soft`, `--brand-text`). In shadcn, `--accent` is the *hover
  background of menu items*.
- `--border` and `--ring` keep their names and meaning. Don't redeclare them as
  `var(--border)`: a custom property that references itself is invalid, and the value drops out.

Then point the remaining shadcn names at the semantic tokens in `src/app.css`. Components keep
using `bg-background`, `text-muted-foreground` and so on, and they all follow the direction.

```css
@import "tailwindcss";
@import "tw-animate-css";

@custom-variant dark (&:where(.dark, .dark *));

:root {
  /* knobs + semantic tokens from tokens.md (with --accent* renamed to --brand*) */

  --background: var(--bg);
  --foreground: var(--text);
  --card: var(--surface);               --card-foreground: var(--text);
  --popover: var(--surface);            --popover-foreground: var(--text);
  --primary: var(--brand);              --primary-foreground: var(--brand-fg);
  --secondary: var(--surface-2);        --secondary-foreground: var(--text);
  --muted: var(--surface-2);            --muted-foreground: var(--text-muted);
  --accent: var(--bg-hover);            --accent-foreground: var(--text);
  --destructive: var(--danger);
  --input: var(--border-strong);
  --radius: var(--r-control);
}
:root.dark { color-scheme: dark; }  /* light-dark() tokens flip automatically */

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-popover: var(--popover);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-border: var(--border);
  --color-ring: var(--ring);
  --color-destructive: var(--destructive);
  --color-brand: var(--brand);
  --color-brand-text: var(--brand-text);
  --color-brand-soft: var(--brand-soft);
  --radius-sm: calc(var(--radius) - 2px);
  --radius-md: var(--radius);
  --radius-lg: var(--r-card);
  --radius-xl: var(--r-dialog);
}

/* Names Tailwind itself owns (fonts, shadows, easings) are set here directly,
   not in :root, because `--font-sans: var(--font-sans)` would reference itself. */
@theme {
  --font-sans: "Geist Variable", ui-sans-serif, system-ui, sans-serif;
  --font-display: "Instrument Serif", Georgia, serif;
  --font-mono: "Geist Mono Variable", ui-monospace, monospace;
  --ease-out: cubic-bezier(.16, 1, .3, 1);
  --ease-in: cubic-bezier(.7, 0, .84, 0);
  --shadow-md: 0 0 0 1px var(--border), 0 4px 8px -2px oklch(.2 .02 var(--neutral-h) / .08), 0 12px 24px -8px oklch(.2 .02 var(--neutral-h) / .12);
  --shadow-lg: 0 0 0 1px var(--border), 0 12px 24px -6px oklch(.2 .02 var(--neutral-h) / .14), 0 32px 64px -16px oklch(.2 .02 var(--neutral-h) / .22);
}
```

So from tokens.md, leave out `--font-*`, `--shadow-*` and `--ease-*` in `:root`; they live in
`@theme` above.

**Pitfall:** `text-accent` / `bg-accent` is the menu hover grey, not the brand color. For the
brand color use `bg-primary`, `text-brand-text` or `bg-brand-soft`.

With `light-dark()` tokens and `color-scheme` switched by the `.dark` class, there's no
need to duplicate every variable in a `.dark {}` block.

## 2. Restyle the primitives

The generated files in `src/lib/components/ui/` are yours. Change their classes (the `tv()`
variants), not their behavior. The usual edits:

| Component | Change from default |
|---|---|
| Button | Height from `--control-h`. Add `active:scale-[.97] transition-[background-color,scale] duration-150`. Primary gets an inner top highlight `shadow-[inset_0_1px_0_oklch(1_0_0/.15)]`. |
| Input / Textarea | `field-sizing-content` on textarea. Focus ring `ring-2 ring-ring/50` + `border-ring`. 16px text under `pointer-coarse`. |
| Card | No shadow, `border` only, radius `lg`. Padding from `--card-p`. |
| Dialog | Radius `xl`, `shadow-lg`. Enter `zoom-in-95 fade-in-0` (~240ms), exit faster. Becomes a `Drawer` (vaul-svelte) under 640px. |
| DropdownMenu / Popover / Select | `shadow-md` + ring. `origin-(--bits-*-transform-origin)` so they grow from the trigger. Item hover uses `bg-accent`. |
| Tabs | Replace the default pill-in-box with an underline or pill indicator that **slides** (a `Spring`-driven element positioned from the active trigger's rect). |
| Table | Row height from `--row-h`. `hover:bg-accent/60`. Sticky header with `bg-background/90 backdrop-blur`. `tabular-nums` on numeric cells. |
| Badge | Status variants from the soft/text semantic pairs (`bg-(--success-soft) text-(--success-text)`), each with an icon or dot, never color alone. |
| Sonner (toasts) | `position="bottom-right"`, `richColors` off, custom classes from the tokens. The undo action gets `duration={8000}`. |
| Command (⌘K) | Width 640px, 18vh from the top, `shadow-xl`. Shortcuts shown in `<Kbd>`. |

Add the fonts with `@fontsource-variable/<name>` imports in the root `+layout.svelte`,
not with a Google Fonts `<link>`.

## 3. Motion in Svelte

See the Svelte section in `motion.md`. The minimum for an app:

- `animate:flip={{ duration: 250 }}` + `in:fly={{ y: 8 }}` / `out:fade={{ duration: 120 }}` on
  every keyed list that changes.
- `transition:slide` for collapsible sections and inline create rows.
- A `Spring` for the tab indicator, the sidebar width and number ticks.
- Route transitions: in the root layout,
  ```ts
  onNavigate((nav) => {
    if (!document.startViewTransition) return;
    return new Promise((resolve) => document.startViewTransition(async () => { resolve(); await nav.complete; }));
  });
  ```
  plus `view-transition-name` on the main content and on the row title → detail title.

## 4. What shadcn doesn't give you

Build these yourself, from the specs in `screens-and-actions.md`:
- the filter chip bar
- saved-view tabs
- the bulk action bar
- the peek panel (a `Sheet` with `modal={false}` and ↑/↓ handling)
- the inline-edit property rows
- the "Saving… / Saved" indicator
- the three kinds of empty state
- the dirty-state save bar
- the danger zone

These components, not the primitives, are what make the app feel designed.
