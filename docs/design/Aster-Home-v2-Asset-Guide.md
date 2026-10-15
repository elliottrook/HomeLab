# Aster Home version 2 asset guide

Status: the original 18-asset family and the 12-asset application-family
expansion are owner-approved private releases. Application adoption remains a
separate decision; this guide does not claim that live apps have changed.

## Retrieve the assets

- [Original Aster Home v2 release](https://git.elliottrook.com/jason/homelab/releases/tag/aster-brand-v2-2026-10-14)
- [Aster v2 application-family expansion](https://git.elliottrook.com/jason/homelab/releases/tag/aster-brand-v2-expansion-2026-10-14)
- [Expansion handoff](Aster-v2-Expansion-Agent-Handoff.md)

Forgejo is private. Receiving agents require authorized private-network and
repository access. Never publish the repository, release or access credentials.

## Identity system

Aster v2 uses a dimensional compass: champagne-gold cardinal faces, jade
diagonal faces, charcoal bearing, engraved centre symbols and a pale limestone
launcher tile. Navigation symbols omit the stone tile. Centre motifs remain
compact. Product lockups use the same compass and gold Aster lettering, with
the product name in green and restrained gold rules.

Interface styling remains calm and restrained: ink `#171C19`, charcoal panels
`#242B25`, warm-white text `#F5F1E8`, soft text `#BFC6BB`, champagne gold
`#D8B778`, jade `#235640`, and light jade `#A7C5AA`. Material textures belong
in identity art rather than behind reading text.

## Expansion contents

The expansion adds four limestone launcher icons (Music, Books, Podcasts and
Settings), four tile-free Music controls (Album, Artist, Song and Playlist),
and four stacked product lockups (Aster Media, Books, Music and News).

The Artist icon uses the approved simplified performer pictogram holding a
microphone. Settings uses an eight-tooth cog. Product names are exactly MEDIA,
BOOKS, MUSIC and NEWS in green.

## Implementation

Use the supplied right-sized PNG or WebP exports in application interfaces.
The SVG masters are dense, editable material illustrations intended for source
and high-quality export, not necessarily direct runtime delivery. Provide text
labels when a compact centre motif could be ambiguous.

The detailed vectors were reconstructed from approved native 1254 px PNGs using
the material-preserving process in
[the repository standard](../standards/brand-design/BRAND-CREATION-STANDARD.md).
They contain no embedded rasters, live fonts, scripts or external references.
The 3000 px files are SVG renders, not claims of newly generated native raster
detail.

## Adoption boundary and rollback

Do not change deployed applications merely because these assets exist. Each app
cutover needs its own consumer list, accessibility and small-size checks, and a
recoverable previous asset set. The immutable original v2 release is the family
rollback source; the expansion release is additive and must not rewrite it.
