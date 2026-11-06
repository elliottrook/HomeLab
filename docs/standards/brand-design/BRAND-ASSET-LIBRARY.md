# Brand Asset Library

This is the HomeLab entry point for brand assets. The canonical asset store is
the private Forgejo repository below; no Mac directory is authoritative.

| Property | Authority |
|---|---|
| Repository | `git@192.168.20.30:jason/brand-assets.git` |
| Branch | `main` |
| Verified migration baseline | `2bdb72732f67e117da6be34da914f16f043e2dce` |
| Repository instructions | root `AGENTS.md` and `START-HERE.md` |
| Registry | root `registry.json` |
| Recovery contract | root `BACKUP-AND-RECOVERY.md` plus the HomeLab migration receipt |

## Consumer workflow

1. Obtain an authorized checkout and materialize required Git LFS objects using
   the setup in `START-HERE.md`. Knowing the URL does not grant access. Never
   work around missing access by changing a firewall, publishing files or
   extracting credentials.
2. Read the asset repository's root `AGENTS.md`, `registry.json`, selected
   brand metadata and brief, `approved-master-hashes.json`, and the applicable
   project approval/state record.
3. Resolve a brand from that checkout, for example:

   ```sh
   python3 scripts/brand_library.py resolve "Aster Home"
   ```

4. Run `python3 scripts/verify_approved.py` after materializing the applicable
   LFS objects. An LFS pointer is not artwork and must not be installed or
   visually reviewed as if it were the asset.
5. Consume only an explicitly approved master or promoted release. A file in
   `incoming/` or `working/` remains a draft unless its project approval record
   explicitly identifies that exact path and SHA-256. Preserve the prior
   approved release as rollback.
6. Record repository revision, brand ID, exact path, SHA-256, approval record,
   consumer context and output/export hashes in the consuming project.

## AsterTV SVG-only ingestion rule

An Aster-owned brand or interface asset may enter AsterTV only as an approved
SVG master or as a deterministic, placement-specific export made directly
from that exact SVG. The export record must bind source path/hash, output
path/hash, named placement, dimensions/export recipe and `runtime_resize=false`.
PNG, WebP, JPEG or another raster must never be resized, repurposed or used as
the source for another AsterTV asset. Pre-policy rasters are frozen by exact
path/hash until replaced; their presence is not precedent for new raster work.

Externally supplied movie, television, album, book, podcast, news and camera
imagery is dynamic content rather than an Aster interface asset. It may be
masked/cropped by the content component but must not be promoted into the brand
asset library or reused as interface artwork.

The optional `BRAND_ASSET_ROOT` or `--root` resolver argument may select a
checkout, but neither changes the authority: Forgejo `main` and its recorded
approval state remain canonical.

## Separation of records

- `brand-assets` stores brand-specific inputs, working files, approved assets,
  reproducible sources and LFS-backed release packages.
- HomeLab stores the reusable creation standard, templates, consumer mappings,
  migration receipt and deployment evidence—not duplicate artwork masters.
- A Git-only mirror or LFS pointer set is not a recoverable asset library.
  Recovery requires Git data and LFS objects together.

## Migration and recovery receipt

The authoritative HomeLab project receipt is
`docs/projects/Brand-Asset-Library-Forgejo.md`. Its verified 2026-11-06 state
records baseline `2bdb72732f67e117da6be34da914f16f043e2dce`, 2,591 files,
4,363,230,287 bytes and 115 matched approved hashes. It also records the
post-import LXC backup, its independent TrueNAS copy and an isolated restore
test. Read the current receipt before claiming a later revision is protected.

