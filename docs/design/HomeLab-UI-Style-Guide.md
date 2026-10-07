# HomeLab private UI style guide

**Status:** Shared baseline — use for new private web surfaces

This guide extends the [HomeLab app icon family](App-Icon-Family.md) into a
small, practical visual system. It captures the choices used by the Unified
Media Recommendations page and the Aster / News Digest family so future UIs
feel related without becoming identical.

## Design intent

The interface should feel calm, capable and slightly luminous: a private tool
that is easy to scan, not a generic admin panel. Use dark navy surfaces,
high-contrast text, restrained cyan/mint actions, and a small amount of violet
or warm-gold glow for identity. Explain what the system knows and why it is
acting; never let decoration compete with the user decision.

## Tokens

Use the CSS variables in [`App-Icon-Family.css`](App-Icon-Family.css) as the
source of truth. The compact semantic palette is:

| Token | Value | Use |
|---|---|---|
| `--ui-bg` | `#0b1020` | page background |
| `--ui-panel` | `#151d31` | primary card/panel |
| `--ui-panel-raised` | `#1b2740` | hover, selected, or elevated panel |
| `--ui-panel-input` | `#111a2c` | filters, inputs, toolbars |
| `--ui-text` | `#f4f7fb` | primary text |
| `--ui-text-soft` | `#dce4f1` | readable body copy |
| `--ui-muted` | `#aab6ca` | metadata, helper text, timestamps |
| `--ui-accent` | `#8bd3ff` | links, focus, primary action |
| `--ui-accent-strong` | `#b9f2d0` | success, ready, trusted state |
| `--ui-danger` | `#ffaaa8` | errors and destructive warnings |
| `--ui-line` | `#2b3a58` | borders and dividers |

The page background may use a very broad radial gradient from `#25395a` into
`--ui-bg`; cards may use a subtle diagonal gradient from `--ui-panel` into
`#10182a`. Do not use gradients for long text or critical controls.

## Typography and hierarchy

- Use the system stack: `system-ui, -apple-system, BlinkMacSystemFont,
  "Segoe UI", sans-serif`.
- Use a small uppercase kicker (`.78rem`, heavy weight, letter spacing around
  `.12em`) for section context.
- Use large, tightly tracked page titles and keep them to one or two lines.
- Use muted text for provenance, timestamps and secondary metadata; never use
  low-contrast gray for required instructions.
- Use sentence case for controls. Reserve uppercase for short labels and
  status badges.

## Layout and components

- Center the content in a readable maximum width, with generous top and bottom
  padding (`42px 24px 72px` is the established desktop baseline).
- Prefer a responsive card grid with a minimum card width near `330px`; collapse
  to one column below `600px`.
- Use `18px` card radii, `16px` toolbar/filter radii, and `10px` control radii.
- Use a `1px` `--ui-line` border plus a restrained shadow (`0 12px 30px
  #0003`) for cards. Avoid thick outlines and floating glass everywhere.
- Put the primary action at the end of the content, with explanatory context
  immediately above it. A user should understand the decision before clicking.
- Use posters or artwork as visual anchors, but always provide text fallbacks
  and useful alt text.

## Interaction and states

- Primary buttons use `--ui-accent` with dark text; hover may brighten slightly.
- Disabled actions use a muted slate fill and must include a nearby reason.
- Focus rings must be visible against `--ui-bg`; do not remove the browser
  outline without replacing it.
- Success uses `--ui-accent-strong`; errors use `--ui-danger`; neither relies on
  color alone—include text or an icon.
- Empty and stale states should be calm, explicit and actionable rather than
  looking like an application failure.
- Search and filters should be local and immediate where possible. Display the
  current filter and the last refresh time.

## Content and trust

Every recommendation or automated action should expose, in plain language:

1. what the item is;
2. where it came from;
3. why it is being shown;
4. what will happen after the action; and
5. when the underlying data was refreshed.

AI may help explain or summarize, but deterministic source IDs, suppression
rules and approval boundaries remain authoritative. Avoid claiming a personal
preference unless the UI can name the supporting signal.

## Icon and imagery rules

- Use the icon-family canvas and rounded-square framing from
  `App-Icon-Family.css`.
- Prefer one centered, legible mark over a collage of tiny symbols.
- At 32px, remove detail that cannot survive reduction; retain silhouette,
  contrast and one distinctive color cue.
- Do not place words, numbers, credentials or transient status in app icons.
- New products should add a source asset and documented derivatives rather than
  copying a deployed PNG by hand.

## Accessibility and responsive baseline

- Body text should remain comfortably readable on a phone; do not rely on
  hover-only explanations.
- Keep tap targets around `44px` where practical.
- Preserve keyboard focus order and provide labels for icon-only actions.
- Reflow headers, toolbars and grids at `600px`; do not make users horizontally
  scroll to reach a primary action.
- Maintain meaningful headings even when the visual treatment is dramatic.

## Handoff checklist

Before calling a UI complete, provide a short operator note covering the route,
what each control does, source freshness, authentication, and recovery from a
failed or stale state. Include a screenshot or live review on desktop and
mobile when the UI is user-facing. This is a design requirement, not optional
polish.
