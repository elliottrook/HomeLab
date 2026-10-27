# AsterTV asset usage standard

Status: implementation audit, 2026-10-27

## Runtime rule

The SVG is the canonical artwork. Kodi 21.3 does not reliably render SVG skin
textures, so AsterTV uses a PNG rendered from the approved SVG at the nearest
required runtime size. It must not enlarge a small PNG, shrink a 512px launcher
to a 28px motif, trace a deployed PNG, or substitute a similarly named asset.
The runtime PNG hash must match either the approved release export or a
documented deterministic render of the approved SVG when a generic release
export has unsuitable canvas bounds.

Canonical masters and complete derivative sets remain in the private Brand
Asset Library and immutable Forgejo release attachments. Git carries the
right-sized runtime exports, provenance and tests rather than hundreds of
megabytes of duplicate textured SVG data.

## Canonical family inventory

| IDs | Family | Intended use |
|---|---|---|
| 01–06 | Aster and app launchers: Aster, Home Hub, Media, News Digest, Content Desk, Acquisition Hub | Limestone launcher/side-rail treatment |
| 07–13 | TV, Film, Archive TV, Archive Film, Books, Audiobooks, Music | Tile-free labelled navigation motifs |
| 14–18 | Aster Home stacked/horizontal logos, compass, monochrome mark and wordmark | Product identity and utility |
| 19 | Movie Collections | Tile-free labelled navigation motif |
| 20–22 | Music, Books and Podcasts app launchers | Limestone launcher/side-rail treatment |
| 23–26 | Album, Artist, Song and Playlist | Tile-free labelled navigation motifs |
| 27–30 | Aster Media, Books, Music and News product lockups | Page headers and product identity |
| 31 | Settings app launcher | Limestone launcher/side-rail treatment |
| 32 | AsterTV product lockup | Player/startup identity |
| 33 | YouTube | Tile-free labelled navigation motif |

The canonical store currently contains 59 SVG files across the approved family,
expansion, Collections, AsterTV and YouTube work sets. The duplication is
intentional: proofs, release staging and source dependencies remain recoverable.
There are dedicated Podcast SVG and PNG assets at every approved export size;
`22-podcasts-app` is specifically a limestone launcher, not a tile-free top-rail
symbol.

## AsterTV placement policy

- Stone/limestone launcher icons appear only in the floating side rail.
- Product lockups identify a page or product; they are not compact button icons.
- Tile-free category/navigation symbols accompany labels in top rails and lists.
- `aster-compass-128.png` is the declared temporary placeholder when no approved
  tile-free symbol exists. It must not be mistaken for a dedicated category icon.
- Large art, covers and hero imagery use source-owned media art. A launcher icon
  is never stretched into cover art.
- Every image control preserves aspect ratio unless it is an explicitly designed
  mask, ring, panel or gradient texture.

## Current intentional placeholders

The approved family has no tile-free Podcast, Settings or Home camera/automation
navigation symbol. AsterTV therefore uses the plain compass for those non-rail
surfaces. Books uses `11-books`; Audiobooks uses `12-audiobooks`; the dedicated
`22-podcasts-app` remains available for a future Podcast side-rail destination.

Recommended future additions, if bespoke marks are wanted, are:

1. tile-free Podcast navigation symbol;
2. tile-free Settings symbol;
3. tile-free camera/Home-automation symbol.

Until approved, the compass placeholder is preferable to reusing a stone
launcher in the wrong context.

## Audit corrections

The 2026-10-27 audit corrected the active skin and v2 builders so that:

- Books and eBook surfaces use the canonical 128px tile-free Books export;
- compact Audiobook surfaces use the canonical 128px export, while the 512px
  derivative remains available for large page art;
- Podcast non-rail surfaces use the declared plain-compass placeholder;
- News empty state uses the Aster News product lockup;
- Home camera/timer and Settings non-rail placeholders use the plain compass;
- Music's isolated rail uses 128px launcher exports rather than shrinking 512px
  hero exports;
- app/add-on utility icons use plain right-sized marks rather than stone launchers;
- generated Music, Home, Settings and Network candidates inherit the same rules.

`services/kodi/v2/test_asset_usage.py` enforces the launcher boundary and checks
the hashes and dimensions of the complete active Aster identity family. The
YouTube 128px runtime asset is rendered directly from the approved `33` SVG
with the documented Sharp recipe because the Brand Asset Library's generic
128px export retains excessive transparent canvas; it is not resized from a
PNG. All other checked runtime files match their canonical release exports
byte-for-byte.

## Source releases

- `aster-brand-v2-2026-10-14`, SHA-256
  `2c770b52cfc04cb90d49f01bec1067566e9b1e3c89fd9235a82c0e86be6bcffc`
- `aster-brand-v2-expansion-2026-10-14`, SHA-256
  `e030b6104fbdffb44faf035471f8c55320c3869065046a1ff5f9f0433069c48e`
- `aster-brand-v2-tv-2026-10-22`
- approved YouTube master `docs/assets/aster-v2/SVG/33-aster-youtube.svg`

Public trademark/font/redistribution clearance remains outside this private
Aster/HomeLab deployment.
