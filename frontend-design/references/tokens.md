# Tokens

The default foundation: a 4px grid, 12-step OKLCH ramps (Radix semantics), semantic variables
that components consume, one tinted neutral, and one accent. Tokens are a starting point. The
brief sets the **knobs**: neutral hue and temperature, accent hue, fonts, radius personality,
and whether the base is dark or light. Never ship the knobs at their example values without
choosing them.

## Spacing

- The base unit is 4px. Steps: 2, 4, 6, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128. Don't
  use in-between values for layout.
- Space inside a group is at most half the space between groups. For example, label→input is
  6–8px and field→field is 20–24px.
- Section padding: 24–32px in apps, 64–128px on marketing pages. Marketing pages can use
  a fluid value: `clamp(4rem, 2.5rem + 6.5vw, 8rem)`.
- Card padding: 16–24px. Control padding-x: 12–16px.
- Content widths: prose `65ch`, settings column 640–720px, app max 1280–1440px, and a
  marketing container of 1200–1280px with a 20–24px mobile gutter.

## Type

**Fonts (all free).**
- Default for product UI: **Geist + Geist Mono**.
- Other neutral sans with more character than Inter: Hanken Grotesk, Figtree, Onest,
  Instrument Sans, Manrope, IBM Plex Sans.
- Editorial display: Instrument Serif, Newsreader, Fraunces, Source Serif 4. Use these
  for headings only, over a grotesk body.
- Expressive display: Bricolage Grotesque, Familjen Grotesk, Space Grotesk (sparingly).
- Mono: Geist Mono, JetBrains Mono, IBM Plex Mono.
- Inter is fine, but it's the most common choice, so it signals "default" unless something
  else carries identity.

**Rules.**
- At most 2 families plus a mono.
- Weights: 400/500/600, occasionally 700. Never 300 for UI text.
- Build hierarchy with weight and color before size.
- `tabular-nums` for tables, prices, and timers.
- `text-wrap: balance` on headings.

**App scale.** Fixed, not fluid, because dense UI shouldn't scale with the viewport:

| Token | px / line-height | Tracking | Use |
|---|---|---|---|
| xs | 12 / 16 | +.01em | badges, meta |
| sm | 13 / 20 | 0 | table cells, secondary |
| base | **14 / 20** | 0 | app body |
| md | 16 / 24 | 0 | prose, mobile inputs |
| lg | 18 / 26 | −.005em | card titles, lead |
| xl | 20 / 28 | −.01em | section titles |
| 2xl | 24 / 32 | −.015em | page titles |
| 3xl–6xl | 30 / 36 → 60 / 64 | −.02 → −.03em | marketing |

**Marketing display.** Fluid, and always mixes `rem` into the value so zoom keeps working:
`font-size: clamp(2.75rem, 1.6rem + 5vw, 6rem); line-height: 1.0; letter-spacing: -0.03em;`.
Real sites go down to −.06em (Vercel). The headline should be ≥ 4× the body size. A light
or regular weight at huge size reads calm and expensive. Semibold with tight tracking reads
engineered.

## Color

**Ramps.**
- Keep the hue fixed and walk L down through the steps.
- Chroma peaks around steps 8–10 and tapers at both ends.
- Neutrals are tinted toward a hue with C 0.003–0.015. Hue 260 gives a cool tint, 60–85 a
  warm one. Pure grey looks dead. Pure `#000` / `#fff` almost never appear on well-made sites.

**The 12 steps (Radix).**

| Step | Role |
|---|---|
| 1 | app background |
| 2 | subtle background |
| 3 | element background |
| 4 | hover |
| 5 | active / selected |
| 6 | subtle border |
| 7 | element border |
| 8 | strong border, focus ring |
| 9 | solid brand fill |
| 10 | solid hover |
| 11 | muted / accent text |
| 12 | high-contrast text |

- Step 9 is the only step that should look like "the brand color".
- Components consume **semantic** tokens only, never raw steps.

**Accent.**
- Exactly one accent, and it has a job: the primary action, selection, focus. It doesn't
  decorate.
- Status colors are semantic, not brand: danger h≈25, warning h≈75, success h≈150,
  info h≈250.
- Secondary text can be the foreground at alpha, e.g. `color-mix(in oklab, var(--text) 66%, transparent)`.

**Dark mode.**
- Background L 0.14–0.18, tinted, not `#000`.
- Higher surfaces get **lighter** (+0.02–0.04 L per level), and raised surfaces get a 1px top
  highlight `inset 0 1px 0 oklch(1 0 0 / .05)`.
- Text L ≈ 0.95, muted text L ≈ 0.72–0.76.
- Borders are translucent white (8–14%).
- Accent text goes up to L ≈ 0.78, and tints lose chroma.

**Contrast.**
- Body text ≥ 4.5:1 (APCA Lc 75). Large text, UI borders, and focus rings ≥ 3:1.
- Placeholder and muted text still need 4.5:1. They are the usual failure.

## Radius

Pick one personality:

| Personality | Controls / cards / dialogs | Fits |
|---|---|---|
| Sharp | 4 / 6 / 8 | dev tools, editorial |
| Default | 8 / 12 / 16 | most products |
| Soft | 12 / 16 / 24 | consumer, iOS-like |

- Pills (`9999px`) go on chips, avatars, and switches.
- Nested radius: inner = outer − padding.
- Don't mix sharp and pill corners on one screen.

## Elevation

- App UI uses **borders, not shadows**: a card is `surface` plus a 1px border.
- Shadows are reserved for things that float: menus and popovers (`md`), dialogs (`lg`), and the
  palette or drag ghost (`xl`).
- Shadows are layered, tinted with the neutral hue, and paired with a 1px ring so the edge
  stays crisp.
- Glass (`backdrop-filter`) is for the floating navigation layer only: a sticky nav, tab bar,
  or menus. Never on cards, buttons, or content. Keep ≥ 72% background opacity and add a
  reduced-transparency fallback.

## Motion

| Token | ms | Use |
|---|---|---|
| instant | 75 | hover color, press |
| fast | 150 | tooltip, toggle, dropdown |
| base | 200 | popover, tabs, accordion |
| slow | 300 | dialog, sheet |
| slower | 450 | page / hero transition |

- Exits run about 30% faster than enters.
- Animate only `transform`, `opacity`, `filter`, `clip-path`, and `grid-template-rows`.
- Default easing is expo-out `cubic-bezier(.16, 1, .3, 1)`. Linear uses `cubic-bezier(.32,.72,0,1)`.
- No bounce on marketing chrome. Springs (≤ 5% overshoot) only for drag, sheets, and
  toggles.
- A good entrance: `opacity 0 → 1`, `translateY(8px) → 0`, `filter: blur(4px) → 0`, over
  400–600ms, staggered 40–60ms per item. Use it once per view.

## Density

| Token | compact | default | comfortable / touch |
|---|---|---|---|
| `--control-h` | 28 | **36** | 44 |
| `--row-h` | 32 | **40** | 52 |
| `--gap` | 8 | **12** | 16 |
| `--card-p` | 12 | **20** | 24 |

Switch to comfortable under `@media (pointer: coarse)`.

## Starter block

Set the four knobs at the top. Everything else derives from them.

```css
@layer tokens {
:root {
  /* ── knobs: choose these from the brief ── */
  --neutral-h: 260;  --neutral-c: 0.008;   /* hue + tint strength of the greys */
  --accent-h: 150;   --accent-c: 0.16;     /* the one accent */
  --font-sans: "Geist", ui-sans-serif, system-ui, sans-serif;
  --font-display: var(--font-sans);        /* or "Instrument Serif", serif */
  --font-mono: "Geist Mono", ui-monospace, monospace;
  --r-control: 8px; --r-card: 12px; --r-dialog: 16px;

  color-scheme: light dark;

  /* neutral ramp (light, dark) */
  --n1:  light-dark(oklch(.991 calc(var(--neutral-c)*.3) var(--neutral-h)), oklch(.160 calc(var(--neutral-c)*.6) var(--neutral-h)));
  --n2:  light-dark(oklch(.982 calc(var(--neutral-c)*.4) var(--neutral-h)), oklch(.185 calc(var(--neutral-c)*.7) var(--neutral-h)));
  --n3:  light-dark(oklch(.960 calc(var(--neutral-c)*.6) var(--neutral-h)), oklch(.220 calc(var(--neutral-c)*.8) var(--neutral-h)));
  --n4:  light-dark(oklch(.940 calc(var(--neutral-c)*.8) var(--neutral-h)), oklch(.250 var(--neutral-c) var(--neutral-h)));
  --n5:  light-dark(oklch(.920 var(--neutral-c) var(--neutral-h)), oklch(.280 var(--neutral-c) var(--neutral-h)));
  --n6:  light-dark(oklch(.895 var(--neutral-c) var(--neutral-h)), oklch(.310 var(--neutral-c) var(--neutral-h)));
  --n7:  light-dark(oklch(.860 calc(var(--neutral-c)*1.2) var(--neutral-h)), oklch(.360 calc(var(--neutral-c)*1.2) var(--neutral-h)));
  --n8:  light-dark(oklch(.780 calc(var(--neutral-c)*1.5) var(--neutral-h)), oklch(.440 calc(var(--neutral-c)*1.5) var(--neutral-h)));
  --n9:  light-dark(oklch(.640 calc(var(--neutral-c)*1.7) var(--neutral-h)), oklch(.540 calc(var(--neutral-c)*1.6) var(--neutral-h)));
  --n11: light-dark(oklch(.500 calc(var(--neutral-c)*1.7) var(--neutral-h)), oklch(.740 calc(var(--neutral-c)*1.2) var(--neutral-h)));
  --n12: light-dark(oklch(.210 calc(var(--neutral-c)*1.2) var(--neutral-h)), oklch(.950 calc(var(--neutral-c)*.5) var(--neutral-h)));

  /* semantic */
  --bg:            var(--n1);
  --surface:       light-dark(oklch(.997 calc(var(--neutral-c)*.2) var(--neutral-h)), var(--n2));
  --surface-2:     light-dark(var(--n2), var(--n3));
  --bg-hover:      var(--n3);
  --bg-active:     var(--n4);
  --border:        light-dark(var(--n6), oklch(1 0 0 / .09));
  --border-strong: light-dark(var(--n7), oklch(1 0 0 / .15));
  --text:          var(--n12);
  --text-muted:    var(--n11);
  --text-subtle:   var(--n9);   /* ~3.3:1: icons, borders, disabled only, never readable text */

  --accent:        light-dark(oklch(.55 var(--accent-c) var(--accent-h)), oklch(.62 var(--accent-c) var(--accent-h)));
  --accent-hover:  light-dark(oklch(.50 var(--accent-c) var(--accent-h)), oklch(.67 var(--accent-c) var(--accent-h)));
  --accent-fg:     light-dark(oklch(.99 0 0), oklch(.99 0 0));   /* dark side: use oklch(.16 …) when the dark accent is light (L ≥ .62) or yellow/lime/cyan */
  --accent-soft:   light-dark(oklch(.95 calc(var(--accent-c)*.2) var(--accent-h)), oklch(.27 calc(var(--accent-c)*.4) var(--accent-h)));
  --accent-text:   light-dark(oklch(.48 var(--accent-c) var(--accent-h)), oklch(.80 calc(var(--accent-c)*.7) var(--accent-h)));
  --ring:          light-dark(oklch(.55 var(--accent-c) var(--accent-h)), oklch(.72 var(--accent-c) var(--accent-h)));   /* opaque: focus rings need 3:1 */

  --danger:      light-dark(oklch(.577 .215 27), oklch(.64 .2 25));
  --danger-soft: light-dark(oklch(.96 .025 27), oklch(.26 .07 25));
  --danger-text: light-dark(oklch(.50 .19 27), oklch(.78 .13 25));
  --success-text: light-dark(oklch(.46 .12 150), oklch(.80 .13 150));
  --success-soft: light-dark(oklch(.965 .03 150), oklch(.26 .05 150));
  --warning-text: light-dark(oklch(.50 .12 60), oklch(.85 .12 80));
  --warning-soft: light-dark(oklch(.97 .04 85), oklch(.28 .06 75));

  --shadow-md: 0 0 0 1px var(--border), 0 4px 8px -2px oklch(.2 .02 var(--neutral-h) / .08), 0 12px 24px -8px oklch(.2 .02 var(--neutral-h) / .12);
  --shadow-lg: 0 0 0 1px var(--border), 0 12px 24px -6px oklch(.2 .02 var(--neutral-h) / .14), 0 32px 64px -16px oklch(.2 .02 var(--neutral-h) / .22);

  --ease-out: cubic-bezier(.16, 1, .3, 1);
  --ease-in: cubic-bezier(.7, 0, .84, 0);
  --dur-fast: 150ms; --dur-base: 200ms; --dur-slow: 300ms;

  --control-h: 36px; --row-h: 40px; --gap: 12px; --card-p: 20px;
}
:root[data-theme="light"] { color-scheme: light; }
:root[data-theme="dark"]  { color-scheme: dark; }
@media (pointer: coarse) { :root { --control-h: 44px; --row-h: 52px; } }
}
```

Don't feed a `light-dark()` value into relative color syntax (`oklch(from var(--x) …)`): support
is unreliable. Write both sides out explicitly, as above.

White text on a mid-lightness accent often lands just under 4.5:1 (e.g. L .62 measured 4.18:1).
Check the result, don't assume it: verify gamut in oklch.com and contrast for `--text-muted`
on `--surface` and `--accent-fg` on `--accent` in **both** themes. Yellow, lime, and cyan
accents need a dark `--accent-fg`.
