# Shared brand asset library

Status: active, verified 2026-11-06. The canonical library is the separate private
Forgejo repository [jason/brand-assets](https://git.elliottrook.com/jason/brand-assets),
branch main. The verified migration baseline is
2bdb72732f67e117da6be34da914f16f043e2dce. Future approved work follows normal
version control and brand-specific approval records; the baseline is not a lock
against later revisions.

## Storage and lookup

The import preserves all four registered brands and all extra variants, originals,
drafts, source scripts, fonts, approved assets, releases and archives: 2,591
original files / 4,363,230,287 bytes. Every original matched its SHA-256 after
import and isolated network recovery. All 115 recorded approved-master hashes
matched; Aster's development/current-release-unset state was preserved. No design
was promoted or changed by migration.

HomeLab holds this entry point, reusable standards and project templates. Artwork
stays in the private asset repository, which has no configured push mirrors.
The HomeLab GitHub documentation mirror does not contain the artwork.

Read the asset repository's AGENTS.md, START-HERE.md and registry.json. Resolve the
exact brand and read its brand.json, brief, hashes and relevant approval/state
records. Keep approved assets distinct from working drafts, incoming originals,
sources, releases and archive. Do not infer approval from inclusion in the import.

## Start another agent

Use the [agent handover](https://git.elliottrook.com/jason/brand-assets/src/branch/main/AGENT-HANDOVER.md).
Install Git LFS from an official distribution or trusted package manager, then use
an existing authorized network/identity:

    GIT_LFS_SKIP_SMUDGE=1 git clone git@192.168.20.30:jason/brand-assets.git
    cd brand-assets
    git lfs install --local
    git lfs pull
    git lfs fsck
    python3 scripts/verify_approved.py
    python3 scripts/brand_library.py list
    python3 scripts/brand_library.py resolve "Exact Brand Name"

The bundled helper defaults to its own checkout, with BRAND_ASSET_ROOT and
explicit --root overrides. Agents should use their own writable checkout rather
than a remembered Mac path. LFS pointer files are not artwork. Cloud/remote agents
still require separately authorized reachability and credentials; knowing the URL
does not grant access or authorize firewall/credential changes.

For routine work, check current approved-master records. The import verifier
compares the original migration snapshot and will intentionally differ after
later authorized edits. Historical scripts and preview links may retain old
absolute paths; configure their root before reuse.

## Backup and recovery

Forgejo LXC 108 stores Git repositories at
/var/lib/forgejo/data/forgejo-repositories and LFS at /var/lib/forgejo/data/lfs.
Both are on its backed-up root disk. The existing Proxmox guest-backup policy
and independent TrueNAS pull protect both together. Backup schedules and retention
were retained; no new public mirror or offsite configuration was created.

A post-import archive was copied independently to TrueNAS, its SHA-256 matched
the integrity-tested source archive, and Git plus LFS were restored into an
isolated directory. All 2,591 original files matched, and recovered Git fsck
passed. A fresh normal client fetched every LFS object and passed Git LFS fsck.
This tests repository/artwork recovery, not a booted whole-guest application restore.

Exact archive, checksum, paths, job evidence and scope are in the
[migration and recovery receipt](../../projects/Brand-Asset-Library-Forgejo.md)
and [machine-readable receipt](brand-asset-library.json).
A Git-only mirror or pointer-only clone is insufficient to recover the artwork.

## Local references and rollback

The original Documents library remains unchanged as a recovery/reference copy;
it is not automatically synchronized. This Mac uses /Users/jasonelliott/brand-assets
as its working checkout outside iCloud, and its brand-design skill resolves there.
Other machines configure their own location.

Preserve the original library and previous releases. If shared access fails,
declare the chosen recovery revision and use an isolated restore; do not silently
create two current authorities or overwrite production as a test. Restore normal
guidance by a reviewed commit if rollback is needed. Rights/private-use limits,
design approvals and remote-write requirements remain unchanged.
