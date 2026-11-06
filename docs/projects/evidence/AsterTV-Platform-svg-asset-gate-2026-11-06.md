# AsterTV SVG-only asset gate — 2026-11-06

## Decision

Every Aster-owned brand or interface asset must have an approved SVG master.
AsterTV may consume the SVG directly or a deterministic raster export made
from that exact SVG for one named placement. Raster-to-raster derivation,
repurposing a raster and runtime resizing are forbidden.

Dynamic media-provider imagery—movie, television, album, book, podcast, news
and camera content—is not reusable Aster interface artwork and remains governed
by content masks/layout rules.

## Enforcement

- `services/kodi/astertv-design/asset-policy.json` is the machine-readable
  rule and freezes the 20 pre-policy runtime rasters by aggregate path/hash
  digest `26d56035f7daa690d1bb598c1d362e4e0e4ed65d23f5fde32eb234dc71f5a3e4`.
- A new placement export must record the SVG source path/hash, output path/hash,
  named placement, fixed dimensions, export recipe and
  `runtime_resize_allowed=false`.
- Existing generic raster outputs may be classified only as frozen legacy;
  they cannot be resized, copied to another placement or used as source.
- The deterministic builder validates semantic masters, exports, registered
  runtime placement outputs and the frozen baseline before generating the
  design index.
- A deliberate unregistered PNG injection is included in the unit tests and
  must fail with `asset-policy: unregistered raster added or frozen legacy
  raster changed`.

## Validation

- Generated outputs: 29/29 reproduced and rechecked.
- Design tests: 14/14 passed, including the deliberate raster violation.
- Skill tests: 3/3 passed.
- Installed design skill matches the source rule and acceptance reference.
- No live AsterTV appliance or brand-asset repository was changed.

