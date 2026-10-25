# Aster Home version 2 asset guide

Status: core and original 18-asset family approved by Jason on 2026-10-14;
private Forgejo release authorized. A nineteenth Movie Collections selector was
approved later that day. Application adoption remains a separate decision.
This document does not claim that live apps have changed.

Start with the [Aster v2 agent handoff](Aster-v2-Agent-Handoff.md) for the
versioned download, checksums, approval scope and implementation boundaries.

## Identity and source of truth

Aster v2 uses a dimensional compass: champagne-gold cardinal faces, jade diagonal
faces, charcoal bearing, engraved centre and a pale limestone launcher tile.
Navigation symbols omit the stone tile. Centre motifs remain compact. Digest's
newspaper is tilted counterclockwise; film uses four reel holes; the archive
clock treatment is shared; HOME in the stacked logo is green.

The Brand Asset Library is the asset authority:

`/Users/jasonelliott/Documents/Brand Asset Library/brands/aster-home/`

The engagement is `working/2026-10-13-aster-home-v2-reconstruction/`.
The accepted pilot is in `core-component-proof-2026-10-14/`; its exact SVG hash
is `f6a0f19ff9e5ac4728e04cf20c28e86f171d516ec403a1bc3df937c8a456c6a4`.
The family candidate is `family-candidate-2026-10-14/` and contains the source,
SVG/PNG/WebP masters, style guide, palette tokens, manual, comparisons and QA.

## Approved post-release extension

`19-movie-collections` is the tile-free selector for movie box-set collections.
Its compact centre uses three offset film cases and a single four-hole reel,
leaving the compass points visible. The owner approved the 1254 px transparent
PNG and then the actual material-preserving SVG render on 2026-10-14.

- Brand-library engagement:
  `working/2026-10-14-movie-collections-icon/`
- PNG SHA-256:
  `5b2df4b991bbfc8ad683c5eeed65763b5414d05bee7cd485ce0d8d0e6c28938c`
- SVG SHA-256:
  `3f89124d6314320a56368b3f208efce9baf293f899c466e8f113cb5164598fcd`
- SVG QA: 23 named components, 1,177 paths, no embedded raster, live font,
  script, event handler, filter or external reference; 1254 px and small-size
  renders reviewed on dark and light surfaces.

This extension is not inside the immutable 18-asset Forgejo release ZIP. Do not
rewrite that release or claim the icon is deployed. A future package revision or
app adoption requires its own authorized action and rollback record.

## AsterTV production lockup

`32-aster-tv-logo` is the owner-approved product lockup for AsterTV. It retains
the centred compass, gold arc and textured gold `Aster` construction, with a
jade uppercase `TV` butted against the lowercase r. The TV has a deliberate
optical overshoot above the capital A; the r terminal sits beneath the left arm
of the T without touching its vertical stem.

- Private Forgejo release:
  `aster-brand-v2-tv-2026-10-22`
- Brand-library engagement:
  `working/2026-10-22-aster-tv-logo/`
- Approved PNG proof SHA-256:
  `e67c4faa46a3aee5aa41a75157c81db02c8c14efb10f9a788579ce2aec4eca79`
- Outlined production SVG SHA-256:
  `911175f5b63a703930def4aa959652a34d3b5f5b7eef178e63834689a29d2a2d`
- Release ZIP SHA-256:
  `6a888ef158f9272f56e73c84494b20c7d7190a6e474deed403e6c72b474c95b0`
- SVG QA: 1,474 paths, no live text, embedded raster, scripts, event handlers,
  external references, duplicate IDs or missing local references. The outlined
  render differs from the exact approved proof by only 0.0094695% of pixels
  above an eight-channel tolerance.

Use the SVG as the scalable production master and a supplied right-sized raster
for ordinary UI delivery. The complete lockup is recommended at 256 px wide or
larger. The release is additive and does not itself change a live application.

Do not restore the rejected flat package from commit `b7f2720`. It was reverted
by `8be288e`. Approval of geometric accuracy alone did not meet material fidelity.

## Aster YouTube selector

`33-aster-youtube` is the owner-approved tile-free selector for the Aster
YouTube consumer. It uses a detailed mid-century CRT receiver with rabbit-ear
aerials, jade glass, restrained play glyph and aged bronze/champagne-gold
materials over the established compass. The complete compass medallion remains
intact; an external dark-jade backing fills its transparent centre aperture so
light interfaces do not create pale bars above or below the television.

- Repository master:
  [`docs/assets/aster-v2/SVG/33-aster-youtube.svg`](../assets/aster-v2/SVG/33-aster-youtube.svg)
- Brand-library engagement:
  `working/2026-10-25-aster-youtube-icon/`
- Approved revision-08 PNG proof SHA-256:
  `dce307ddb727cd5113eb4178eb574ebc07bf4d7d5f1a910561bc516d0cf9cc6c`
- Production SVG SHA-256:
  `449f30b8ddff8b4fa3339bd58463064955a2215731766e2f724cd94ff611a3eb`
- SVG QA: 1,154 paths and 26 clipping paths; no embedded raster, live
  text, external reference, duplicate ID or missing local reference. Transparent,
  white-background and small-size renders passed visual review.

The SVG is an additive approved asset. Committing it to Forgejo makes the master
available to authorized production consumers but does not itself deploy or alter
an application.

## Interface direction

Keep interfaces calm and restrained: ink `#171C19`, charcoal panels `#242B25`,
warm-white text `#F5F1E8`, soft text `#BFC6BB`, champagne gold `#D8B778`, jade
`#235640`, and light jade `#A7C5AA` for green text/selection on dark surfaces.
Use the package's full token/contrast records during implementation. Material
textures belong in identity artwork, not behind reading text. System sans-serif
typography remains the interface baseline; the bespoke logo is not a font.

Use right-sized raster exports for ordinary app delivery; the detailed vector
masters are intentionally large. Labels are required where compact motifs
become ambiguous. Preserve keyboard focus, accessible names, explicit source
freshness and explanations of recommendations. Existing voice, security and
authorization requirements remain unchanged.

## Adoption boundary

Do not change deployed apps merely because this guide exists. Before rollout,
record the owner-reviewed family revision and hashes, application consumers,
export sizes, keyboard/contrast/small-size tests and rollback. The prior UI guide
continues to describe current deployments until each app's cutover is verified.

Future branding follows [material-preserving reconstruction](../standards/brand-design/MATERIAL-PRESERVING-VECTORS.md):
approved native colour evidence, measured components, actual SVG render review,
one-asset approval, family expansion, packaging and explicit deployment status.
