# Aster Home v2 — agent handoff

Owner-approved identity family: 2026-10-14. Jason approved the rendered family
and explicitly authorized publishing the private Forgejo release. This is an
asset delivery, not an application deployment or a merge to the default branch.

The later-approved Movie Collections selector is documented in the
[asset/style guide](Aster-Home-v2-Asset-Guide.md). It is a post-release extension
and is not contained in the immutable 18-asset ZIP below.

The approved Aster YouTube selector is available directly as a repository SVG:

[Aster YouTube production SVG](../assets/aster-v2/SVG/33-aster-youtube.svg)

Its SHA-256 is
`449f30b8ddff8b4fa3339bd58463064955a2215731766e2f724cd94ff611a3eb`.
It is an additive asset and is not contained in the immutable 18-asset ZIP.

The outlined `AsterTV` production lockup is published as a separate additive
private release:

[AsterTV production logo](https://git.elliottrook.com/jason/homelab/releases/tag/aster-brand-v2-tv-2026-10-22)

Download the attached `aster-brand-v2-tv-2026-10-22.zip`. Its SHA-256 is
`6a888ef158f9272f56e73c84494b20c7d7190a6e474deed403e6c72b474c95b0`;
the outlined SVG SHA-256 is
`911175f5b63a703930def4aa959652a34d3b5f5b7eef178e63834689a29d2a2d`.
This additive release does not rewrite the original family release or deploy an
application consumer.

## Retrieve the approved assets

[Aster Home v2 release](https://git.elliottrook.com/jason/homelab/releases/tag/aster-brand-v2-2026-10-14)

The repository is private. The receiving agent needs authorized Forgejo access
and private-network reachability. Do not expose Forgejo publicly or copy access
tokens into agent prompts. A cloud agent without that access cannot fetch this
link directly; use an owner-authorized local executor or file handoff.

Download the **attached `aster-version-2-family-candidate.zip`**, not the
automatically generated repository source archive. Its historical filename and
internal candidate statuses are retained deliberately so the approved package
stays byte-for-byte unchanged. This dated approval record and the release notes
supersede those review-pending statuses for this exact package only.

- ZIP size: **484,024,718 bytes**.
- ZIP SHA-256: `2c770b52cfc04cb90d49f01bec1067566e9b1e3c89fd9235a82c0e86be6bcffc`.
- Approved core `SVG/01-aster.svg` SHA-256:
  `f6a0f19ff9e5ac4728e04cf20c28e86f171d516ec403a1bc3df937c8a456c6a4`.
- Verify the archive hash before extraction, then check `SHA256SUMS` and
  `manifest.json`. The package contains 293 ZIP entries and 291 manifested files.

## Contents and design invariants

18 SVG masters: Aster; Home Hub; Home Media; News Digest; Content Desk; Media
Acquisition Hub; TV; Film; Archive TV; Archive Film; Books; Audiobooks; Music;
stacked Aster Home logo; tile-free compass; horizontal logo; monochrome utility
mark; and wordmark. Also included: eight PNG sizes (16 through 3000px), 512px
WebP, the eight-page `brand_manual.pdf`, `STYLE-GUIDE.md`, `COLOUR-PALETTE.md`,
tokens, original references, comparison sheets, build scripts and QA evidence.

Preserve the champagne-gold/jade compass faces and charcoal bearing. Launcher
icons use a limestone tile; navigation symbols omit it. Keep centre motifs
compact, the newspaper tilted counterclockwise, the same four-hole film reel
in both film symbols, the same archive-clock treatment, and HOME lettering green.
Do not substitute the rejected flat geometric package or redraw the lettering.

## Implementation guidance

Use right-sized PNG/WebP exports in app interfaces. These are dense editable
vector illustrations, not lightweight runtime SVG icons. No embedded raster,
live fonts, scripts or external references occur in the 18 SVG masters.

Read [the asset/style guide](Aster-Home-v2-Asset-Guide.md), then
[the canonical brand process](../standards/brand-design/BRAND-CREATION-STANDARD.md)
and [material-preserving reconstruction](../standards/brand-design/MATERIAL-PRESERVING-VECTORS.md).
The native references are 1254px square and 1536 × 1024 for the logo; 3000px
exports are actual SVG renders, not newly generated native detail. No separately
billed image API credits were used. Perfect and approve one source-derived
material-preserving SVG before expanding any future family.

The streaming-page illustration is a styling mockup, not a functional Kodi skin.
App rollout requires its own authorized consumer list, accessible labels,
keyboard/focus/contrast and small-size tests, and a recoverable previous asset set.
Existing security and Aster voice requirements remain unchanged.

## QA, limitations and recovery

The package passed XML/safety checks, source/export checksums, ZIP CRC/reopen,
and a packaged-core rerender matched the 3000px export byte-for-byte. The manual's
eight rendered pages were reviewed. SVG rendering used Sharp/librsvg; an
independent second SVG renderer was not verified. Legacy blanket source-size,
approval and rights checks did not produce a strict full-profile pass; retain
their report rather than describing it as passed. Family approval now resolves
the review decision only, not independent rights clearance or renderer coverage.

Intended scope is Jason's private Aster/HomeLab identity. Public trademark,
font/legal clearance and public redistribution are not established. The private
release does not authorize public reuse or production app changes.

Originals and prior rejected proofs remain in the Brand Asset Library. The
approved archive is immutable; make a new release for any correction. Roll back
an app with its recorded previous exports, not by rewriting this release or Git
history. Publishing this release does not change the current library `assets/`
directory or any live application.
