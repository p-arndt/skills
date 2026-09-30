# Motion

A UI feels smooth when **everything that changes state moves**, fast and physically. Nothing
should blink into place. One hero animation doesn't make an interface smooth. What does is
fifty small transitions that each take 150–300ms and that nobody consciously notices. Here's
what goes wrong in practice:

- things appear but never animate out
- lists jump when an item is added or removed
- tab indicators teleport
- numbers swap without ticking
- skeletons hard-cut to content

The rule is **functional motion everywhere, decorative motion once.** Functional motion shows
where something came from, where it went, and what changed. Decorative motion, such as a hero
stagger or scroll reveals, is the part you ration.

## Physics

| Kind | Duration | Easing |
|---|---|---|
| Hover color/bg, press | 75–120ms | `ease-out` |
| Small enter (tooltip, menu, popover) | 150–180ms | `--ease-out` expo `cubic-bezier(.16,1,.3,1)` |
| Exit of anything | ~70% of its enter | `--ease-in` `cubic-bezier(.7,0,.84,0)` or just a fast fade |
| Dialog, sheet, drawer, peek panel | 240–320ms | spring or `--ease-out` |
| Layout change (reorder, resize, list insert/remove) | 200–300ms | spring (no/low bounce) |
| Page / view transition | 250–400ms | `--ease-out`, crossfade + small translate |
| Hero entrance stagger | 500–700ms per item, 40–70ms stagger | `--ease-out` |

**Springs in plain CSS.** Use `linear()` to get spring-like curves without JS:

```css
:root {
  /* gentle spring, ~0 overshoot: panels, layout */
  --spring: linear(0, 0.009, 0.035 2.1%, 0.141 4.4%, 0.723 12.9%, 0.938 16.7%, 1.017 20.5%, 1.043 24.5%, 1.035 28.4%, 1.007 38.1%, 0.998 45.6%, 1);
  --spring-dur: 450ms;
  /* snappy spring with a hint of overshoot: toggles, press release, tab indicator */
  --spring-snappy: linear(0, 0.14 4%, 0.55 11%, 0.9 18%, 1.05 25%, 1.06 30%, 1.02 38%, 0.995 50%, 1);
  --spring-snappy-dur: 380ms;
}
```

**What to animate.** Only `transform` (`translate`/`scale`/`rotate` as individual properties),
`opacity`, `filter`, `clip-path`, and `grid-template-rows` (for accordions). Never animate
`width`, `height`, `top` or `left`. Use FLIP or view transitions for those instead.

**Reduced motion.** Under `prefers-reduced-motion: reduce`, keep the opacity crossfades and
drop the translation, scale and stagger. Removing all feedback is worse.

## The catalogue: every one of these should be in an app

**Controls**
- **Button press:** `scale: .97` on `:active` over 80ms, release with `--spring-snappy`.
  Primary buttons also shift background over 120ms.
- **Hover** on rows, cards and nav items: background fades in over 100ms. Cards may lift by
  `translate: 0 -2px` and gain shadow. Rows never lift.
- **Toggle / switch:** the thumb slides with `--spring-snappy` and the track color crossfades.
- **Checkbox:** the check mark draws in (`stroke-dashoffset`, 150ms) and the box scales to
  1.1 and back.
- **Tab / segmented control / nav indicator:** the pill or underline **slides** to the new item
  (animate `translate` + `width` via a transform scale, or anchor it with a view-transition-name).
  It never teleports.
- **Copy / save / success:** the icon morphs (copy → check) with a crossfade and scale 0.8 → 1,
  then reverts after 1.5s.

**Overlays**
- **Menu / popover / tooltip:** enter with opacity 0 → 1 plus `scale .96 → 1` and 4px of
  translate from the anchor side, with `transform-origin` at the anchor. Exit with a fast
  fade. Tooltips get a 300–500ms open delay, and when moving between tooltips the next one
  opens instantly.
- **Dialog:** backdrop fades in over 200ms. The panel scales `.96 → 1` with opacity over
  240ms using `--ease-out`. It exits faster.
- **Sheet / drawer / peek:** slides in from its edge with `--spring` (`translate: 100% 0 → 0`).
  Mobile bottom sheets slide up and follow drag.
- **Toast:** slides in from its edge and stacks. When one leaves, the others **move** into
  place instead of jumping. The undo toast shows a draining progress line for its timeout.
- **⌘K palette:** scale .98 → 1 plus fade in 150ms. The highlighted row's background
  **slides** between results rather than blinking.

**Lists and data**
- **Insert:** a new row grows in: `grid-template-rows: 0fr → 1fr` + fade, or FLIP. Give it a
  brief accent-tinted background that fades over 1.5s ("this is the new one").
- **Remove:** the row fades and collapses, and the rows below **slide up**. Never jump.
- **Reorder / sort / filter:** the rows move to their new positions (FLIP or view transitions
  with `view-transition-name` per row). If there are more than ~50 rows, crossfade instead.
- **Skeleton → content:** crossfade over 200ms. The skeleton shimmer is a slow 1.5s gradient
  sweep, and it's static under reduced motion.
- **Numbers** (counts, totals, KPIs): tick to the new value over 400–600ms with
  `tabular-nums`, or use a vertical digit roll. Stock going from 12 to 11 should visibly change.
- **Inline edit:** the field morphs from text to input with no layout shift. The "Saving… →
  Saved ✓" indicator crossfades and fades out after 2s.
- **Bulk action bar:** slides up from the bottom with a spring. The selected count ticks.
- **Accordion / details:** height animates via `grid-template-rows` or `interpolate-size`, and
  the chevron rotates.

**Navigation**
- **List → detail:** shared-element transition. The row's title (and thumbnail) morphs into the
  detail header via `view-transition-name`. Back reverses it.
- **Route change:** outgoing content fades out in 120ms, incoming content fades in with an 8px
  rise over 250ms. Keep the sidebar and header static: only the content area transitions.
- **Sidebar collapse:** width animates via `grid-template-columns` and labels fade out
  before the width shrinks.

**Marketing / decorative** (ration these)
- **Hero load:** headline, subhead, CTA and product visual stagger in: opacity + 12px rise
  + `blur(6px) → 0`, 600ms, 60ms apart.
- **Scroll reveals:** sections fade and rise 16px once as they enter (scroll-driven
  `animation-timeline: view()` behind `@supports`, or IntersectionObserver). Once, not on
  every scroll.
- **Product visual:** a subtle parallax (≤ 30px), or a slow tilt that settles as you scroll.
  The UI inside it *does something* on a loop: a cursor clicks, a row gets added, a status
  changes. That is what makes a product shot feel alive.
- **Ambient:** a slow gradient drift (20–40s loop) behind the hero, only if the direction
  calls for it.

## Snippets (CSS / vanilla)

```css
.btn { transition: background-color 120ms, scale 380ms var(--spring-snappy); }
.btn:active { scale: .97; transition-duration: 80ms; }

/* popover / menu with origin */
[popover] {
  transform-origin: var(--origin, top left);
  opacity: 0; scale: .96; translate: 0 -4px;
  transition: opacity 150ms var(--ease-out), scale 150ms var(--ease-out), translate 150ms var(--ease-out),
              display 150ms allow-discrete, overlay 150ms allow-discrete;
}
[popover]:popover-open { opacity: 1; scale: 1; translate: 0;
  @starting-style { opacity: 0; scale: .96; translate: 0 -4px; } }

/* collapse / expand rows or accordions */
.collapse { display: grid; grid-template-rows: 1fr; transition: grid-template-rows 250ms var(--ease-out), opacity 200ms; }
.collapse[data-state="closed"] { grid-template-rows: 0fr; opacity: 0; }
.collapse > * { overflow: hidden; }

/* newly inserted row */
@keyframes flash-new { from { background: var(--accent-soft); } }
.row[data-new] { animation: flash-new 1.5s var(--ease-out); }

/* view transitions: content only, faster exit */
::view-transition-old(content) { animation: 120ms var(--ease-in) both fade-out; }
::view-transition-new(content) { animation: 250ms var(--ease-out) both rise-in; }
@keyframes fade-out { to { opacity: 0; } }
@keyframes rise-in { from { opacity: 0; translate: 0 8px; } }
```

```js
// FLIP for list reorder / remove, when view transitions aren't used
function flip(container, mutate) {
  const rows = [...container.children];
  const first = new Map(rows.map(el => [el, el.getBoundingClientRect().top]));
  mutate();
  for (const el of container.children) {
    const dy = first.get(el) - el.getBoundingClientRect().top;
    if (!dy) continue;
    el.animate([{ translate: `0 ${dy}px` }, { translate: '0 0' }],
               { duration: 250, easing: 'cubic-bezier(.16,1,.3,1)' });
  }
}

// number tick
function tick(el, to, ms = 500) {
  const from = Number(el.textContent) || 0, t0 = performance.now();
  const step = t => { const p = Math.min(1, (t - t0) / ms), e = 1 - (1 - p) ** 4;
    el.textContent = Math.round(from + (to - from) * e); if (p < 1) requestAnimationFrame(step); };
  requestAnimationFrame(step);
}
```

## Svelte 5

Svelte ships most of this built in, so use it instead of hand-rolled code:

- `transition:fly={{ y: 8, duration: 200 }}`, `in:`/`out:` for asymmetric enter and exit,
  `transition:slide` for collapse.
- `animate:flip={{ duration: 250 }}` on keyed `{#each}` blocks gives insert, remove and
  reorder for free.
- `Spring` / `Tween` from `svelte/motion` for indicators, number ticks and drag follow
  (`new Spring(0, { stiffness: 0.15, damping: 0.8 })`).
- `crossfade` from `svelte/transition` for list → detail and card → modal shared elements.
- SvelteKit `onNavigate` plus `document.startViewTransition` for route transitions.
- If you need more, **Motion** (`motion` package, `animate()`) is the standard JS library.
  Reach for it before GSAP in product UI.
