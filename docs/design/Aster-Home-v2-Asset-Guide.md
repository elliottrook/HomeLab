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

Do not restore the rejected flat package from commit `b7f2720`. It was reverted
by `8be288e`. Approval of geometric accuracy alone did not meet material fidelity.

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
