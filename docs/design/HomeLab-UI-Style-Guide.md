# Aster-associated internal network apps — UI style guide

**Status:** Shared baseline for Aster-associated internal network apps only

## Scope and brand boundary

This guide applies to Aster-associated private HomeLab applications: AsterAI
(formerly Aster Companion), the News Digest briefing, Media Acquisition Hub
(the Unified Media Recommendations service), and Photography Content Desk.
The Contrasting Frame public site keeps its own visual identity. Its public
preview inside Content Desk retains that identity while the Desk controls use
Aster styling.

Aster Home v2 is the approved visual source. Use the [Aster Home v2 asset
guide](Aster-Home-v2-Asset-Guide.md) and the
[app icon family](App-Icon-Family.md) for the asset map. Runtime PNG and ICNS
files are exports of the SVG masters, never independent artwork.

## Design intent

Use quiet charcoal reading surfaces with restrained jade and champagne-gold
highlights. The dimensional compass and limestone tile belong in identity art;
keep dense material textures out of controls and long-form text. The interface
should explain actions, source data and approval boundaries clearly.

## Tokens

[`App-Icon-Family.css`](App-Icon-Family.css) contains the shared CSS tokens.

| Token | Value | Use |
|---|---|---|
| `--ui-bg` | `#171C19` | Page background |
| `--ui-panel` | `#242B25` | Primary panel |
| `--ui-panel-raised` | `#303A32` | Elevated panel |
| `--ui-panel-input` | `#202922` | Inputs and toolbars |
| `--ui-text` | `#F5F1E8` | Primary text |
| `--ui-text-soft` | `#E2E5DD` | Body copy |
| `--ui-muted` | `#BFC6BB` | Metadata and helper copy |
| `--ui-accent` | `#D8B778` | Focus, links and primary emphasis |
| `--ui-accent-strong` | `#A7C5AA` | Success and trusted state |
| `--ui-danger` | `#F4A89E` | Errors and warnings |
| `--ui-line` | `#526055` | Borders and dividers |

A warm light surface is also valid where the product needs it: page stone
`#E6DAC8`, panel ivory `#F8F5EF`, ink `#1E241F`, jade `#1F513B` and gold
`#C2A06B`. News Digest uses this variant. Keep text contrast appropriate to
the chosen surface rather than mixing dark and light token roles.

## Typography and layout

- Use the system font stack for application UI. Keep labels and status text
  readable without relying on the artwork.
- Use a short uppercase kicker, about `.78rem` with `.12em` tracking, for
  section context; use sentence case for controls.
- Center readable content with generous margins. Responsive cards use about
  `18px` radii and collapse to one column below `600px`.
- Use subtle panel gradients and shadows. Reserve the limestone texture for
  approved identity assets and launcher icons.

## Interaction and states

- Use jade for primary actions on charcoal, with warm-white text. Gold is a
  strong focus and identity accent. A gold-filled control requires dark text.
- Provide a visible gold focus outline for keyboard use. Aim for `44px` tap
  targets and avoid hover-only instructions.
- Disabled actions need a written reason. Success and errors need text or a
  symbol alongside color.
- Explain what data was refreshed, where an item came from, why it is offered,
  and what an approval will do. Requests remain explicit.

## Icon and imagery rules

- Begin with the approved SVG master for each product. Export the necessary
  sizes from that file and record its path and SHA-256 in the icon guide.
- The launcher artwork has its own rounded limestone tile. Export a square
  image with an opaque limestone canvas extending to every edge; do not add a
  white, black or navy border. Keep the central motif centered and inspect at
  32px, 180px and 512px.
- Browser icons use a 32px favicon and 180px Apple touch icon. A manifest may
  include a 512px image. Native macOS apps use a full ICNS iconset from the
  same master.
- Tile-free navigation marks are for in-app controls. Keep text names beside
  compact marks when their engraved centre symbols are ambiguous.
- Retire the old electric-blue, violet-glow icons and their blue UI motifs.
  Keep old files only as version history or rollback material, not active
  references or source assets.

## Accessibility and product boundaries

- Reflow controls on narrow screens without horizontal scrolling to reach an
  action. Supply useful alt text for content imagery and accessible labels for
  icon-only controls.
- AsterAI is the visible name of the assistant. Existing executable, package,
  bundle ID and `aster-companion` callback scheme remain stable to protect
  passkey and Keychain behavior.
- Media Acquisition Hub is the visible portal name; its recommendation and
  search actions retain their existing service approval boundaries.
- Content Desk uses Aster UI chrome. The embedded public photography previews
  continue to use the appropriate photography-site brand.

## Aster voice and spoken-output standard

Aster's canonical spoken voice is the British-English Kokoro voice used by the
News Digest briefing. It is now the voice of Aster for all new apps, AI
features and text-to-speech output. Do not introduce a different voice for a
new surface merely because another engine is easier to wire in.

The reproducible reference configuration is:

| Setting | Required value |
|---|---|
| Engine | Kokoro ONNX, `kokoro-v1.0.fp16.onnx` |
| Voice | `bm_daniel` |
| Language | `en-gb` / British English |
| Speed | `0.95` |
| Synthesis units | Sentence-sized; split long sentences at clauses |
| Story cadence | One second of silence between stories |
| Output | 24 kHz mono PCM during assembly, then MP3 for delivery where appropriate |

Use the News Digest implementation in `services/news-aggregator/audio_digest.py`
as the executable reference. Spoken text must pass the shared cleanup in
`services/news-aggregator/digest_text.py`: remove Markdown presentation, speak
currency naturally in words (for example, `CA $1,234.50` as “one thousand two
hundred and thirty-four Canadian dollars and fifty cents”), turn parenthetical
punctuation into natural pauses, and expand dotted abbreviations such as
`U.S.`/`U.S.A.` to “United States” and `B.C.` to “British Columbia”. Avoid long
single synthesis calls, which can produce unnatural joins, breathiness or
distortion.

For recurring briefings, use the same time-aware structure: identify the
briefing as morning or evening from local time, state the date, pause between
stories, and close with “Have a good day” in the morning or “Have a good
evening” at night. Any deliberate deviation requires a documented design
decision and a real listening test against this reference.

## Handoff checklist

Before calling a UI complete, provide a short operator note covering the route,
what each control does, source freshness, authentication, and recovery from a
failed or stale state. Include a screenshot or live review on desktop and
mobile when the UI is user-facing. This is a design requirement, not optional
polish.
