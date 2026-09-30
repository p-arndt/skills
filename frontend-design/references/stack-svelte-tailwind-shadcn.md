# SvelteKit + Tailwind v4 + shadcn-svelte

Out of the box, shadcn **is** the generic look: zinc greys, radius 0.625rem, Inter, no motion.
Using it is still right, because bits-ui gives you accessible behavior for free. Shipping its
defaults is wrong. The work is to theme it from the direction, then add the motion and detail
it lacks.

If the repo also follows `sveltekit-modular-monolith`, its rules win where they overlap. For
example: primitives in `$lib/components/ui/*` are edited for tokens and styling only, never
behavior, and codes render in the normal font.

**Overlays: bits-ui wins over raw platform elements.** In this stack, dialog, sheet, popover,
dropdown and tooltip come from shadcn/bits-ui, not from `<dialog>` or `popover`. Use the
platform features from `modern-css.md` only for what shadcn doesn't cover.

Verified against sv 0.17, shadcn-svelte 1.7, bits-ui 2.19 and Tailwind 4.3 (Sept 2026). Check
the generated files and don't trust these paths blindly on newer versions.

## 0. Scaffold facts

- `npx sv create` puts the Tailwind entry at **`src/routes/layout.css`**, imported from
  `+layout.svelte`, not at `src/app.css`. There is no `svelte.config.js`: the config lives in
  `vite.config.ts`.
- `npx shadcn-svelte@latest init` asks for a **preset** (Nova, Vega, Maia…) interactively. Pick
  any of them: you replace the tokens and font afterwards anyway. The preset installs Inter, so
  remove it when you set the direction's font.
- The generated CSS imports **`shadcn-svelte/tailwind.css`**. That import defines the
  `data-open` / `data-closed` variants the components' animation classes use. Keep it, or
  every overlay animation breaks.

## 1. Tokens → shadcn variables → Tailwind

Take the knobs and semantic tokens from `tokens.md`, with **two renames**. shadcn already uses
those names with a different meaning:

- Rename the brand accent `--accent*` from tokens.md to `--brand*` (`--brand`, `--brand-hover`,
  `--brand-fg`, `--brand-soft`, `--brand-text`). In shadcn, `--accent` means the *hover
  background of menu items*.
- `--border` and `--ring` keep their names and meaning. Don't redeclare them as
  `var(--border)`. A custom property that references itself is invalid, and it drops out.

```css
/* src/routes/layout.css */
@import "tailwindcss";
@import "tw-animate-css";
@import "shadcn-svelte/tailwind.css";

@custom-variant dark (&:is(.dark *));

:root {
  /* knobs + semantic tokens from tokens.md (--accent* renamed to --brand*) */

  /* mode-watcher toggles .dark. Pin color-scheme to the class, or light-dark() follows
     the OS while Tailwind's dark: follows the class, and the two disagree. */
  color-scheme: light;

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
:root.dark { color-scheme: dark; }

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);
  --color-brand: var(--brand);
  --color-brand-text: var(--brand-text);
  --color-brand-soft: var(--brand-soft);
  /* the generated components use sm…4xl; define all of them */
  --radius-sm: calc(var(--r-control) * .75);
  --radius-md: var(--r-control);
  --radius-lg: var(--r-card);
  --radius-xl: var(--r-dialog);
  --radius-2xl: calc(var(--r-dialog) * 1.25);
  --radius-3xl: calc(var(--r-dialog) * 1.5);
  --radius-4xl: 9999px;
}

/* Tailwind's own names (fonts, shadows, easings) are set directly here, not in :root,
   because `--font-sans: var(--font-sans)` would reference itself. */
@theme {
  --font-sans: "Hanken Grotesk Variable", ui-sans-serif, system-ui, sans-serif;
  --font-display: "Newsreader Variable", Georgia, serif;
  --font-mono: "Geist Mono Variable", ui-monospace, monospace;
  --ease-out: cubic-bezier(.16, 1, .3, 1);
  --ease-in: cubic-bezier(.7, 0, .84, 0);
  --shadow-md: 0 0 0 1px var(--border), 0 4px 8px -2px oklch(.2 .02 var(--neutral-h) / .08), 0 12px 24px -8px oklch(.2 .02 var(--neutral-h) / .12);
  --shadow-lg: 0 0 0 1px var(--border), 0 12px 24px -6px oklch(.2 .02 var(--neutral-h) / .14), 0 32px 64px -16px oklch(.2 .02 var(--neutral-h) / .22);
}
```

- **Font loading:** `@fontsource-variable/<name>` imports in the root `+layout.svelte`, not a
  Google Fonts `<link>`.
- **Pitfall:** `text-accent` and `bg-accent` give the menu hover grey, not the brand color.
  For the brand, use `bg-primary`, `text-brand-text` or `bg-brand-soft`.
- **Deliberately inverted surfaces** (a dark bulk bar or dirty bar on a light app, a dark
  band on the landing page) get their own semantic tokens (`--inverse-bg`, `--inverse-text`),
  not raw oklch in components.

## 2. Restyle the primitives

The generated files in `src/lib/components/ui/` belong to you. Change their classes (the
`tv()` variants), not their behavior.

| Component | Change from default |
|---|---|
| Button | Height from `--control-h`. Add `active:scale-[.97] transition-[background-color,scale] duration-150`. Primary gets an inner top highlight `shadow-[inset_0_1px_0_oklch(1_0_0/.15)]`. |
| Input / Textarea | `field-sizing-content` on the textarea. Focus ring `ring-2 ring-ring/50` + `border-ring`. 16px text under `pointer-coarse`. |
| Card | No shadow, `border` only, radius `lg`, padding from `--card-p`. |
| Dialog | Radius `xl`, `shadow-lg`. Enter `zoom-in-95 fade-in-0` over ~240ms; exit is faster. Becomes a `Drawer` below **the same breakpoint where the sidebar hides** (usually `md`, 768px). |
| DropdownMenu / Popover / Select | `shadow-md` plus a ring. `origin-(--bits-*-transform-origin)` so they grow from the trigger. |
| Tabs | Replace the default pill-in-box with an underline or pill indicator that **slides**. Drive it with a `Spring`, positioned from the active trigger's rect. |
| Table | Row height from `--row-h`. `hover:bg-accent/60`. Sticky header with `bg-background/90 backdrop-blur`. `tabular-nums` on numeric cells. |
| Badge | Status variants from the soft/text semantic pairs (`bg-(--success-soft) text-(--success-text)`), each with an icon or dot. Never color alone. |
| Sonner (toasts) | `position="bottom-right"`, `richColors` off, custom classes from the tokens. The undo action gets `duration={8000}`. |
| Command (⌘K) | 640px wide, 18vh from the top, `shadow-xl`. Shortcuts shown in `<Kbd>`. On phones it becomes a drawer, with the input autofocused. |

**Enter/exit speed** of tw-animate classes comes from `--tw-duration` and `--tw-ease`. To make
exits faster than enters, set them per state:
`data-[state=closed]:[--tw-duration:120ms] data-[state=open]:[--tw-duration:200ms]`.

## 3. Motion in Svelte

See the Svelte section in `motion.md`. The minimum for an app:

- Every keyed list that changes gets `animate:flip={{ duration: 250 }}`, `in:fly={{ y: 8 }}` and
  `out:fade={{ duration: 120 }}`. `animate:` needs the element to be the **direct child** of
  the keyed `{#each}`. Don't wrap `<tr>` in a ContextMenu trigger (see §4).
- `transition:slide` for collapsible sections and inline create rows.
- A `Spring` for the tab indicator, the sidebar width and number ticks.
- Route transitions go in the root layout:
  ```ts
  onNavigate((nav) => {
    if (!document.startViewTransition) return;
    return new Promise((resolve) => document.startViewTransition(async () => { resolve(); await nav.complete; }));
  });
  ```
  For list → detail, set `view-transition-name` **only on the clicked row** (on
  `pointerdown`). Otherwise every row carries the same name and the transition aborts.
  Photos with different aspect ratios need
  `::view-transition-old(photo), ::view-transition-new(photo) { object-fit: cover; height: 100%; }`.
  Morph the photo and the container; crossfade text between very different sizes instead of
  morphing it.
- **Reduced motion.** Svelte transitions run on the Web Animations API, and the global CSS
  duration kill doesn't reach them. Use `prefersReducedMotion` from `svelte/motion`:
  `in:fly={{ y: prefersReducedMotion.current ? 0 : 8 }}`. For tw-animate, zero the movement
  and keep the fade:
  ```css
  @media (prefers-reduced-motion: reduce) {
    * { --tw-enter-scale: 1; --tw-exit-scale: 1; --tw-enter-translate-x: 0; --tw-enter-translate-y: 0;
        --tw-exit-translate-x: 0; --tw-exit-translate-y: 0; }
  }
  ```

## 4. What shadcn doesn't give you

Build these yourself, from the specs in `screens-and-actions.md`:

- **Peek panel:** a plain fixed `<aside>` with `transition:fly={{ x: 24 }}`. Not a Sheet: the
  bits-ui Sheet is dialog-based and fights being non-modal. ↑/↓ moves between records, Esc
  closes, and the panel's state lives in the URL.
- **Right-click = ⋯ menu on table rows:** a single DropdownMenu with `customAnchor` set to
  the pointer position, opened from `oncontextmenu`. Don't use ContextMenu, because its
  wrapper trigger breaks `animate:flip` on rows.
- The rest: the filter chip bar, saved-view tabs, the bulk action bar, the inline-edit property
  rows, the "Saving… / Saved" indicator, the three kinds of empty state, the dirty-state save
  bar, and the danger zone.

These composites are what make the app feel designed. The primitives don't.

## 5. Images

Unsplash's search API is blocked without a key, and remembered photo IDs are often dead (11 of
58 were 404 in one run). Before you use a URL, check it with
`curl -sI "https://images.unsplash.com/photo-<id>?w=64" | head -1`. Then look at what it
actually shows: fetch a small version, or screenshot a contact sheet of candidates. If the
user has their own photos, those always win.
