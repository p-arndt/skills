---
name: frontend-design
description: 'Design and build web or app UIs that look deliberately designed, not like the averaged AI or template default. Covers visual direction (type, color, layout, one signature element), design tokens (OKLCH ramps, spacing, radius, motion), and how screens and actions work: list, detail, create, edit, delete, empty, loading and error states, ⌘K, mobile. Use when building or restyling a page, landing page, dashboard, app screen or component, when the user asks for "modern", "schön", "clean", "polished" UI, or when reviewing a UI for generic look or missing states.'
argument-hint: '[what to build or review]'
---

# frontend-design

A generated UI goes generic in a predictable way. The model reaches for the most probable
choice at every decision, and the most probable choices add up to a look everyone recognizes:
Inter, a purple gradient, a centered hero, three icon cards, soft shadows, and only the happy
path. Neutral isn't the failure. The failure is that nothing was **chosen**.

Well-made products look distinct for four reasons:
- They make a few deliberate choices and apply them strictly.
- They show the real product instead of decoration.
- They get the dense, boring parts right: tables, forms, states.
- Their interactions follow conventions users already know from Linear, GitHub and Stripe.

This skill works in that order: **direction → tokens → screens → states → motion → check.**

Avoiding the generic look is only half the job. A page with no mistakes and no ambition is still
forgettable. Section 1 decides where to be restrained, and section 1b decides where to go big.

## References

Load what the task needs. Don't load all of them by reflex.

| File | Load when |
|---|---|
| `references/visual-language.md` | Choosing a direction, and any marketing or landing page. What Linear, Vercel, Stripe, Raycast, Cursor and others actually ship, with verdicts on bento, grain, glass and gradients. |
| `references/tokens.md` | Setting up or changing styles. Spacing, type scale, fonts, OKLCH ramps, dark mode, radius, elevation, motion, density, and a starter CSS block. |
| `references/screens-and-actions.md` | Any app screen: list, detail, create, edit, delete, validation, toasts, empty states, navigation, settings, ⌘K, shortcuts. |
| `references/mobile.md` | Anything a phone will see: tab bar, sheets, touch targets, swipe actions, the desktop→mobile mapping table, safe areas. |
| `references/motion.md` | **Always, for anything interactive.** Timing, springs in CSS, and the catalogue of transitions every app needs: press, overlays, list insert/remove/reorder, number ticks, list→detail, route changes. Includes Svelte 5 equivalents. |
| `references/modern-css.md` | Writing the CSS: `<dialog>`, popover, anchor positioning, view transitions, `:has()`, container queries, `light-dark()`, with baseline status. |
| `references/stack-svelte-tailwind-shadcn.md` | The project uses (or may use) SvelteKit, Tailwind v4 or shadcn-svelte. Maps the tokens onto shadcn variables and lists which primitives to restyle and how. |
| `references/anti-slop.md` | Before starting (pre-flight) and before finishing (tells and a11y checklist). |

## 1. Direction: before any code

Write these five lines down, in the response or in a comment at the top of the stylesheet.
Then read them back against the brief. **If a line would fit any product, redo it.**

1. **Subject and feel:** what the product is, and one adjective for it (calm, dense, playful,
   editorial, technical, luxurious…).
2. **Type:** the family or families and why. Default for product UI: Geist + Geist Mono.
   Editorial or brand pages: a display serif for headings over a grotesk body. Inter is fine, but
   it is the most common choice, so something else has to carry identity.
3. **Color:**
   - The neutral's temperature: cool ink, warm paper, or achromatic.
   - **One** accent, with a stated job.
   - Dark-first or light-first.
   - Derive all of it from the domain, not from a default.
4. **Layout idea:** the one structural decision that makes this not-a-template. For example: the
   product screenshot as the hero, a dense table front and center, an asymmetric grid, or a
   long-form narrative.
5. **Signature:** exactly **one** memorable detail. Standard structure (a closing CTA band, a
   footer) doesn't count. For example: a visible hairline grid, a serif
   headline, a warm grain, a crisp dark app window, or one bold color field. One committed idea beats
   ten safe ones.

## 1b. Ambition: where to go big

The restraint rules (one accent, borders over shadows, no gradient decoration) exist to
make **a few moments** hit harder, not to flatten the whole page. Every marketing page, and
every app's first impression, needs at least two of these, done with real craft:

- **A product visual that dominates.** The real UI, rebuilt in HTML, at 60–100% of the
  container width. It sits in light and depth:
  - a soft radial glow behind it, a layered shadow, and a 1px inner highlight
  - optionally a slight perspective tilt, or bleeding off the right edge or the bottom of
    the section
  - it *does something* on a loop: a row gets added, a status flips, a cursor clicks
- **Atmosphere.** 1–2 large, blurred radial gradients at low chroma in the neutral/accent hues,
  plus 3–6% grain. It is light falling on the page, not decoration.
- **Contrast rhythm.** Not every section is the same white. At least one section inverts
  (a dark band on a light page, or the other way round) or sits on a full-bleed color field or
  image. Vary the composition from section to section: split, full-bleed, dense table,
  big number.
- **Real imagery when the subject is physical.** Plants, food, places, hardware, people:
  use photographs (Unsplash / Pexels by URL, with `alt`, `aspect-ratio`,
  `object-fit: cover`). Crop them tight and give them consistent treatment. Remembered photo
  URLs are often dead or show something else, so check each one (`curl -sI`) and look at a
  small version before using it. A nursery with
  no photo of a plant has failed the brief.
- **Type at a scale that commits.** A hero at 5–8rem with tight tracking, next to 13px meta
  text. Or one enormous number. The size contrast is the design.
- **Detail craft in the app.** The places people look closely get the most polish:
  - hover states on every row
  - a sliding tab indicator
  - avatars and status dots with tiny rings
  - the empty state with a small, domain-specific illustration or a preview of the filled UI

Test: take a screenshot of the first viewport. If it could be any product's page with the
logo swapped, it hasn't committed yet.

If the user or the repo already has a design system, brand, or component library (shadcn, a
Tailwind theme, existing CSS variables), that **is** the direction. Work within it and only fill
the gaps.

## 2. Tokens

Start from the starter block in `references/tokens.md` and set its knobs from step 1: neutral
hue and tint, accent hue, fonts, radius personality. Components consume **semantic tokens only**
(`--surface`, `--text-muted`, `--accent`, `--border`…), never raw hex values or ramp steps.

Non-negotiables:
- A 4px spacing grid. Space inside a group is at most half the space between groups.
- One accent. Status colors are semantic, not brand colors.
- Tinted neutrals. No pure `#000` or `#fff` as page colors.
- App UI separates with borders and space. Shadows are only for things that float: menu,
  popover, dialog, toast.
- One radius personality: sharp, default, or soft.
- Motion: 150–300ms, expo ease-out, only `transform` and `opacity` (plus `filter`), and
  `prefers-reduced-motion` respected.
- Light **and** dark via `light-dark()`, with contrast checked in both.

## 3. Screens and actions

For app screens, `references/screens-and-actions.md` holds the full specs. The defaults to
reach for:

| Action | Default | Deviate when |
|---|---|---|
| **Browse** | Table (4+ compared attributes) or dense list rows. Toolbar with search and filter chips, filters mirrored in the URL, result count. | Cards only when the visual *is* the content. |
| **View** | Detail page with its own URL. Main column plus a 280–320px properties sidebar, activity at the bottom. Peek panel (`Space`) from lists. | — |
| **Create** | The lightest surface that fits the **required** fields: inline, then modal (≤ 6 fields), then side sheet, then full page. | Wizard (full page, 3–5 steps) only when later steps depend on earlier answers. |
| **Edit** | Always editable. Click to edit in place, popover pickers, autosave with a "Saved" indicator. | Explicit save (plus a sticky dirty bar) when fields form one transaction or have side effects. Never mix both in one form. |
| **Delete** | Act immediately, then an undo toast (8–10s). | Irreversible actions get a dialog that names the object and the count, with focus on Cancel. The most destructive get type-to-confirm in a danger zone. |
| **Navigate** | A 220–260px left sidebar, tabs for sub-views of one object, breadcrumbs from 2 levels deep. | Phone: bottom tab bar (≤ 5). |
| **Power users** | ⌘K palette that reaches every action and page. Single-key shortcuts shown in tooltips. Right-click menu = `⋯` menu. | — |

Every screen that shows data has **all** of its states designed, not only the filled one:
- **Loading:** a skeleton that matches the real layout.
- **Empty, first use:** one CTA.
- **Empty, no results:** clear filters.
- **Error:** inline, with Retry.
- **Long content:** truncation.
- **1 item and 1,000 items.**

Validate fields on blur, re-validate on every keystroke once a field is in error, and never
show "required" errors before the first submit. Skip the blur validation when focus moves to
the submit button (`event.relatedTarget`). Otherwise the error line shifts the button away
mid-click. Never re-render controls in a blur handler, because it swallows the click.

## 4. Build

- **Stack.** Use the repo's stack. For a new project without one, prefer **SvelteKit +
  Tailwind v4 + shadcn-svelte**: dialogs, menus, command palette, sheets and toasts come
  accessible out of the box, and `animate:flip` / `transition:` make motion nearly free.
  Retheme it per `references/stack-svelte-tailwind-shadcn.md`, because its defaults are the
  generic look. Use plain HTML/CSS only for single static pages.
- **Use the platform first.**
  - `<dialog>` for modals and sheets.
  - The popover API for menus and toasts.
  - Anchor positioning for dropdowns.
  - `:has()` for parent state.
  - Container queries for components.
  - View transitions for list→detail.

  They replace JS libraries and ship accessible behavior for free. See `references/modern-css.md`.
- **Realistic data.** Varied lengths, missing values, odd numbers, every status. "John Doe" and
  "$1,234" hide the layout problems that real data exposes.
- **Real product visuals.** On marketing pages, show the actual UI rebuilt in HTML, or a cropped
  screenshot. Never stock imagery or abstract blobs in the product's place.
- **Icons.** One set (Lucide, Phosphor or Tabler) at one stroke width, sized to the text. Never emoji
  as UI icons.
- **Copy.** Specific nouns and numbers in the user's vocabulary. Buttons are verbs ("Create
  invoice", not "Submit").
- **Motion.** Functional motion everywhere, decorative motion once:
  - Everything that changes state transitions: press, hover, open/close (**enter *and*
    exit**), list insert/remove/reorder, tab indicators, number changes, skeleton → content,
    list → detail.
  - Durations 150–300ms, expo ease-out or a CSS `linear()` spring. Nothing blinks into place.
  - Decorative motion is rationed: one hero stagger, scroll reveals that play once.
  - Follow the catalogue in `references/motion.md`. An app with no motion reads as unfinished,
    however good the stills look.

## 5. Check before calling it done

Go through `references/anti-slop.md` against the result. At minimum:

- [ ] The five direction lines hold. Nothing on screen is the "most probable" choice by accident.
- [ ] No purple→blue gradient, no gradient text, no emoji icons, no card-in-card, no
      three-identical-cards section, no everything-centered layout (unless the direction says so).
- [ ] Contrast ≥ 4.5:1 for text (muted text too) in **both** themes.
- [ ] A visible `:focus-visible` ring on every interactive element.
- [ ] Nothing is hover-only.
- [ ] Every control has hover, active, focus, disabled and pending states. Every data view
      has loading, empty, error and long-content states.
- [ ] Works at 320px width and at 200% zoom. Touch targets ≥ 44px on coarse pointers. Inputs
      ≥ 16px on mobile.
- [ ] No layout shift from fonts, images or async content.
- [ ] Motion: every overlay animates in **and** out, list changes move instead of jump, tab
      indicators slide, and reduced motion keeps the crossfades.
- [ ] Ambition: the first viewport passes the "logo swap" test, and at least two items
      from 1b are present and done well.
- [ ] If you can run it, look at it: open it in a browser at 1440px and 390px, in light and dark.
      Fix what looks off before reporting.
