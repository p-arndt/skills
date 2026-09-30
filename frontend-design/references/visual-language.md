# Visual language: what well-made products actually ship

Values come from the CSS of linear.app, vercel.com, stripe.com, raycast.com, resend.com, cursor.com,
clerk.com, supabase.com, attio.com, mercury.com, anthropic.com, and posthog.com, plus the galleries
Awwwards, siteinspire, saaslandingpage, and recent.design (Sept 2026). Dribbble serves shots,
not products, so treat anything seen only there as unproven.

## The shared grammar

1. **One grotesk, a mono, and often a serif.** Neutral sans for UI (Inter, Geist, Söhne,
   Suisse, custom), mono for labels, code, and numbers. A serif accent is now common:
   Cursor uses EB Garamond, Attio and Mercury use Tiempos, Resend uses Domaine for the h1,
   and Raycast uses Instrument Serif.
2. **Tracking tightens as size grows.** Body 0 to −.01em. Headings −.022em (Linear) to −.035em
   (Clerk), down to −.06em (Vercel display). Heading line-height 0.95–1.1.
3. **Restrained weights.** Headings are 500–600, rarely 700. Stripe's hero is 300. Vercel's h1
   is 400. Fractional variable weights (450/550, 360/420/480) are a craft signal.
4. **Tinted neutrals, never pure.**
   - Linear `#08090a`, Raycast `#07080a`
   - Cursor paper `#f7f7f4`, Cursor ink `#14120b`
   - Anthropic `#faf9f5`, Stripe ink `#061b31`, Mercury `#10101a`
   - 3–4 background steps carry the elevation.
5. **One accent, used sparingly.**
   - Linear `#5e6ad2`, Stripe `#533afd`, Supabase `#3fcf8e`, Cursor `#f54e00`, Anthropic clay `#d97757`.
   - Vercel and Resend have **no** hue at all.
6. **Borders over shadows.**
   - Hairlines are 1px at 8–12% alpha, or a `0 0 0 1px` ring.
   - On dark surfaces, a top-edge highlight `inset 0 1px #ffffff1a`.
   - Shadows, where they exist, are multi-layer at 1–15% alpha.
7. **Small, tokenized radii.** Controls 4–8px, cards 12–16px, large media 24–40px, and pills for
   primary buttons and chips.
8. **Show the real product.** Rebuilt HTML app windows (Raycast, Cursor), live components (Clerk
   renders its actual SignIn), tabbed code (Resend, Supabase), and dark-framed screenshots
   (Linear). Never stock photos or abstract 3D blobs standing in for the product.
9. **Fast motion with expo ease-out.** 120–300ms, `cubic-bezier(.32,.72,0,1)` (Linear) or
   `(.25,1,.5,1)` (Stripe). The entrance is a blur plus fade (Attio: `blur(1.5px)` → 0). No bounce.

## The knobs that make a site distinct

| Knob | Options (examples) |
|---|---|
| Neutral temperature | Cool ink (Stripe, Mercury), warm paper (Cursor, Anthropic), pure achromatic (Vercel, Resend). A warm off-white is the cheapest way out of "default Tailwind". |
| Display face | A serif h1 reads editorial. A custom grotesk reads premium. A light weight at a huge size reads calm. Semibold with tight tracking reads engineered. |
| Base | Dark-first and glossy (Linear, Raycast) vs light-first and papery (Attio, Mercury, Anthropic). |
| Signature surface | Visible grid with crosshairs (Vercel), glass with inset highlight (Raycast), stacked soft shadow (Clerk), animated mesh gradient (Stripe), hand-drawn illustration (Anthropic). **Pick one.** |
| Product presentation | Live components, rebuilt windows, code-first, cinematic photo plus UI, or illustration only. |
| Copy voice | Terse slogans (Raycast), paragraph-long h2s (Attio), irreverent (PostHog), numeric proof (Mercury "$650M"). |
| One weird committed idea | PostHog's whole site is a retro desktop OS. rauno.me uses an asymmetric radius `16px 80px 16px 80px`. One committed oddity beats ten safe choices. |

## Signature elements: verdicts

| Element | Verdict | How, if used |
|---|---|---|
| **Bento grid** | Shipped but saturated. Use it once per page for a feature overview, never as the whole page. | 4- or 12-column grid, mixed spans (2×1, 1×2), `grid-auto-flow: dense`, 12–16px gaps. Each tile holds a real UI crop, not "icon + heading + 2 lines". |
| **Grain / noise** | Fine on marketing surfaces, never in app chrome. | SVG `feTurbulence` overlay at 3–8% opacity, `mix-blend-mode: overlay`, `pointer-events: none`. It also kills gradient banding. |
| **Gradients** | Only as ambient light. | 1–2 large blurred radial glows at low chroma behind content. No gradient text, no gradient buttons, no purple→blue diagonal. |
| **Glass** | Restricted to the floating nav layer. | `backdrop-filter: blur(16px)`, background ≥ 72% opaque, a 1px border, and an opaque fallback. NN/g documents legibility failures over busy content. |
| **Oversized type hero** | Shipped. | `clamp()` up to 6–9rem, −.03em tracking, line-height ~0.95, and tiny meta text (12–14px) for contrast. Show the product right below it. |
| **Visible grid / hairlines** | Shipped, especially for dev tools. | 1px low-contrast lines, aligned edges, optional `+` marks at intersections. |
| **Serif revival** | Current trend and credible. | A display serif for h1/h2 only, over a grotesk body. |
| **Mono labels** | Fine as texture. A cliché when every label is mono. | 11–12px uppercase, +.04–.08em tracking, for metadata only. |
| **Neumorphism** | Avoid. | It can't carry state or contrast. |
| **3D / WebGL heroes** | Avoid by default. | Only when the product is physical or the site *is* the experience. |
| **Neo-brutalism** | Legitimate for dev and editorial work. | A cliché with thick black borders and hard offset shadows on everything. |
| **Earthy palettes** (clay, cream, taupe, olive) | A rising antidote to SaaS blue/purple. | Note: the cream + serif + terracotta combination is itself becoming a default. |

## Dashboards: Dribbble vs reality

- **Dribbble version:** every card is a hero chart, KPIs at 48px, glass cards on purple blobs,
  no tables, no empty or error states.
- **Real version:** mostly tables, filters, and forms. Numbers are 20–28px `tabular-nums` in a
  small KPI row, and charts are secondary.
- **Design for the real one.** If the screen looks like a Dribbble shot, it is probably missing
  density and states.

## Marketing page skeleton (one good default, not the only one)

1. **Nav:** logo, 4–5 links, a quiet secondary link, and one primary button. Sticky, with an
   opaque-ish background after scroll.
2. **Hero:** left-aligned or centered, a 2–8 word claim, a 1–2 line muted subhead, a primary
   and a secondary CTA. **The product visual is right there, above or just below the fold.**
3. **Proof strip:** customer logos or one hard number.
4. **2–4 feature sections:** a claim h2, a 1-line lead, and a real UI crop. Vary the
   composition (text left or right, full-bleed, a table, code).
5. **Optional:** one bento overview, a changelog or "recently shipped" feed, a testimonial wall.
6. **Closing CTA band.**
7. **Dense multi-column footer.**
