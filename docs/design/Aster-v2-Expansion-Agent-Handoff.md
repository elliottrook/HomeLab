# Aster Home v2 application-family expansion — agent handoff

Owner-approved identity expansion: 2026-10-14. Jason approved all twelve PNG
masters and explicitly authorized SVG processing, commit, push and private
Forgejo release publication. This is an asset delivery, not an application
deployment.

## Retrieve the approved package

[Aster v2 expansion release](https://git.elliottrook.com/jason/homelab/releases/tag/aster-brand-v2-expansion-2026-10-14)

Download the attached
`aster-v2-application-family-expansion-2026-10-14.zip`, not the automatically
generated repository source archive.

- ZIP size: **240,062,428 bytes**.
- ZIP SHA-256:
  `e030b6104fbdffb44faf035471f8c55320c3869065046a1ff5f9f0433069c48e`.
- ZIP entries: **174**.
- Verify the archive hash, then `SHA256SUMS` and `manifest.json` before use.

The repository and release are private. A receiving agent needs authorized
Forgejo and private-network access. Do not expose Forgejo publicly or place
access tokens in prompts.

## Included masters

Twelve production SVGs:

- `20-music-app.svg`, `21-books-app.svg`, `22-podcasts-app.svg`,
  `31-settings-app.svg` — limestone launcher icons.
- `23-music-album.svg`, `24-music-artist.svg`, `25-music-song.svg`,
  `26-music-playlist.svg` — tile-free Music navigation.
- `27-aster-media-logo.svg`, `28-aster-books-logo.svg`,
  `29-aster-music-logo.svg`, `30-aster-news-logo.svg` — stacked product logos.

The package also contains eight PNG sizes from 16 through 3000 px, lossless
512 px WebP exports, exact approved PNG sources, the existing eight-page Aster
v2 manual, a style-guide addendum, palette tokens, contact sheets, comparison
metrics, reconstruction code, manifests, checksums and QA evidence.

## Quality and safety evidence

- All twelve approved source hashes match the recorded approval ledger.
- All twelve SVGs are editable outlined paths with named semantic regions.
- No embedded raster, live text, external reference, script, event handler,
  foreign object or filter occurs in a master.
- Source/render silhouette IoU is at least 0.98; visible RGB MAE is at most 9.
- All 96 PNGs and 12 WebPs decode at their declared dimensions.
- Dark/light 128, 64 and 32 px contact sheets were reviewed.
- The final ZIP passed CRC, reopen and every-entry hash verification.

## Implementation and limitations

Use PNG/WebP exports for ordinary app delivery and SVGs as editable masters.
Launcher/navigation icons remain recognizable at 32 px, but labels are still
required for ambiguous functions. Stacked product subtitles are not intended
for favicon sizes; use a companion icon instead.

This is a private owner-directed Aster/HomeLab identity. Public trademark,
font/legal clearance and public redistribution are not established. Deployment
to any application needs a separate authorized cutover and rollback record.

## Rollback

The original immutable
[`aster-brand-v2-2026-10-14`](https://git.elliottrook.com/jason/homelab/releases/tag/aster-brand-v2-2026-10-14)
release remains unchanged. Roll back consumers to their recorded previous
right-sized exports; do not rewrite either release or Git history.
