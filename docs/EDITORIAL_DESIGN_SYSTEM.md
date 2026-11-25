# CareContext Studio v0.3 — Editorial visual system

This redesign adapts the user-supplied `DESIGN.md` into **CareContext's own product identity**. It carries across the reference's proportions, colors, typography hierarchy, spatial rhythm, and component geometry without using ElevenLabs branding or licensed assets.

## Token map

| Role | Hex | Applied to |
| --- | --- | --- |
| Canvas | `#f5f5f5` | Masthead, hero, bottom section |
| Canvas soft | `#fafafa` | Workspaces, document upload fields |
| Card | `#ffffff` | Document, conversation, and source surfaces |
| Primary ink | `#292524` | Main action pills, small brand mark |
| Text ink | `#0c0a09` | Headline and body emphasis |
| Body | `#4e4e4e` | Explanatory copy |
| Muted | `#777169` | Metadata and secondary text |
| Hairline | `#e7e5e4` | Cards, section rules, fields |
| Hairline strong | `#d6d3d1` | Hover/boundary contrast |
| Pastel atmosphere | `#a7e5d3`, `#f4c5a8`, `#c8b8e0`, `#a8c8e8` | **Decorative-only** radial orbs |

All tokens are in `carecontext/web/studio.css` under `:root`. No gradient buttons, neon accents, or saturated CTA backgrounds.

## Typography

- **Display:** `EB Garamond` (open-source substitute), `Baskerville`, `Georgia`, then Times. Headings use font-weight 300, compact line height, and slight negative tracking. The licensed Waldenburg font from the reference is intentionally **not copied or distributed**.
- **Body:** `Inter`, system sans-serif fallback at 400/500, comfortable line height.
- **Microcopy:** Inter, 10–12px, modest uppercase tracking. Reading text remains 13–16px and contrast-conscious.

## Layout / interaction

- Sticky 70px masthead with brand, navigation, and a single dark action pill.
- Main content capped at 1200px; large section rhythm around 96px on desktop.
- White cards at 16px radius / 1px hairline; gentle shadows used sparingly.
- Pills for primary actions, secondary actions use outline or understated links.
- Hero atmosphere uses *only* blurred mint/peach/lavender/sky radial orbs behind a decorative document.
- Three audience perspectives remain directly usable; changing the view changes explanatory wording, not evidence validity or permissions.
- The original v0.2 application remains available under `/classic` unchanged; it is a preserved research reference.
- Form behavior, ingestion constraints, grounded evidence, citation navigation, and export logic are untouched.

## Safety and accessibility

- The public interface is for synthetic documents, not protected patient records.
- Use contrast-preserving ink and body colors; don't use pale gradients behind body text.
- Clear focus rings, semantic labels, `aria-live` for messages, a working mobile menu, and `prefers-reduced-motion` support.
- Pastel motion is decorative: evidence never depends on animation.
- No remote font or image fetches, analytics, or third-party scripts required.

## Validation

Run `python -m pytest -q`, `npm run check`, `npm test`. The standalone HTML is a UI preview that uses an explicit synthetic data mock; actual PDF/DOCX extraction needs the FastAPI app.
