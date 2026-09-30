# Generic-UI tells and their fixes

Models, and templates, fall back to the statistical average of the web. That means Tailwind
defaults, the shadcn look, Inter, a purple gradient, and three feature cards. Every row below is
a default you must *choose* against the brief. None of them is banned outright.

| Tell | Countermeasure |
|---|---|
| Inter/Roboto/system-ui in a single weight, with little size contrast | Pick a face for this brief. Display size should be 3–5× body size. If you use two families, make them clearly different (display + text). Don't rotate the same "safe distinctive" picks (Space Grotesk, Fraunces) through every project. |
| Indigo→purple gradient, gradient text on the headline | Derive the palette from the domain. Use one accent with a job (action, selection, status). Neutrals do 90% of the work. |
| The *newer* defaults: cream `#F4F1EA` + serif + terracotta; near-black + one acid-green accent; broadsheet hairlines with radius 0; mono labels everywhere | These are equally generic now. Use them only if the brief asks for them. |
| Hero → 3 icon cards → testimonials → CTA | Choose the macro-structure from the content: product screenshot as the hero, an asymmetric grid, a table, a long-form narrative, or a bento with a real size hierarchy. |
| The same padding, radius and card height everywhere | Hierarchy is deliberate. Primary things are bigger, heavier, and closer together. The spacing scale has real jumps. |
| Card in card in card, heavy shadows, blur on everything | Separate with space, alignment, and one hairline or a tone change. In app UI, shadows are only for true overlays (menus, dialogs, toasts). The one hero product visual on a marketing page is the exception and gets real depth. |
| Emoji as icons, random icon weights | One icon set (Lucide / Phosphor / Tabler) at one stroke width, sized to the text. Add icons only where they help scanning. |
| One accented word in the headline, "01/02/03" on things that aren't steps, ALL-CAPS eyebrows over every block | Let the plain headline stand. Number real steps only. Drop eyebrows that repeat the heading. |
| Everything centered | Left-align text blocks. At most, center a short hero statement. |
| Weightless copy ("Build faster. Ship smarter.", "all-in-one platform") and lorem-ish stats | Use real nouns, numbers, and the user's vocabulary. Would the founder say it out loud? |
| Every element fades in with the same timing, or there's no motion at all | Functional motion on every state change (see `motion.md`), plus one orchestrated decorative moment. |
| Correct but flat: no mistakes, and also no moment that lands | Restraint everywhere *except* 2+ deliberate big moments (SKILL.md §1b): a dominant product visual, atmosphere, contrast rhythm, real imagery. |
| Only the happy path | Design empty (3 kinds), loading, error, long content, zero-permission, and 1-item vs 1,000-item states. |
| Dark mode as inverted greys, pure `#000` / `#fff` | Tinted neutrals, lighter surfaces for elevation, a desaturated accent, and a contrast check in both themes. |
| Placeholder stock data ("John Doe", "Lorem ipsum", `$1,234`) | Realistic, varied data: long names, missing values, odd numbers, different statuses. Design shows up in the edge cases. |

## Pre-flight: before writing code

These are the five direction lines from SKILL.md §1, which is the source of truth. Also note
the display and body sizes on the type line. Critique them against the brief. If a line would
fit any product, redo it.

1. **Subject:** what the product is, and one word for how it should feel.
2. **Type:** the family (or families), and the display/body sizes.
3. **Color:** the neutral hue, the one accent and its job, and whether the theme is dark or
   light first.
4. **Layout idea:** the one structural decision that makes this page not-a-template.
5. **Signature:** the one detail someone would remember.

## Must-haves (a11y / UX)

- Contrast ≥ 4.5:1 for body text, and ≥ 3:1 for large text, control borders, and focus rings.
  Check both themes. Muted grey text is the usual failure.
- Every interactive element has `:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px }`.
  Never write `outline: none` without a replacement.
- `<button>` for actions and `<a href>` for navigation. A `<label>` on every input. Landmarks,
  one `h1`, and an `aria-label` on icon-only buttons.
- Nothing hover-only. Anything revealed on hover is also reachable by focus and by tap.
- **Every control state** is designed: hover, active, focus-visible, disabled (say why),
  pending, selected, and invalid.
- **Every data state** is designed: empty, loading, error with retry, and success. Async
  results are announced through `aria-live="polite"`.
- **No layout shift:** media get `aspect-ratio`, async regions reserve their space, and use
  `scrollbar-gutter: stable`.
- `prefers-reduced-motion` is respected.
- Re-renders keep focus. When a region re-renders (a vanilla `innerHTML` swap or keyed lists),
  focus and caret stay where they were. Otherwise keyboard use breaks silently.
- Works at 320px width and 200% zoom.
- Color is never the only signal: pair status colors with an icon or text.
