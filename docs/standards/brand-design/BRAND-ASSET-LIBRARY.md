# Shared brand asset library

Status, 2026-11-06: migration prepared; private repository publication, complete
retrieval and post-import backup/restore validation are pending. Until these pass,
the existing Documents library remains authoritative. Do not infer completion
from this document or a proposed URL.

## Destination and lookup

The intended shared home is the separate private Forgejo repository
`jason/brand-assets`, default branch `main`:

- Browser: https://git.elliottrook.com/jason/brand-assets
- SSH: `git@192.168.20.30:jason/brand-assets.git`

HomeLab contains this entry point, workflow standards and templates; the separate
asset repository contains brand-specific artwork, releases and state. Do not
check that artwork into HomeLab or assume the HomeLab GitHub mirror includes it.

Use a configurable local checkout root, e.g. `BRAND_ASSET_ROOT`, rather than a
fixed username/Documents path. Read root `AGENTS.md`/`START-HERE.md`, then
`registry.json`. Resolve the exact brand and read its `brand.json`, brief and
approved-master hashes. Preserve the separation between approved `assets/`,
draft `working/`, immutable `incoming/`, `sources/`, `releases/` and `archive/`.
Access to a registry entry does not grant access to all brands or to the network.

## Portable first checkout

Install Git and Git LFS from their official distribution or a trusted package
manager. From an authorized network and account:

```sh
GIT_LFS_SKIP_SMUDGE=1 git clone git@192.168.20.30:jason/brand-assets.git
cd brand-assets
git lfs install --local
git lfs pull
git lfs fsck
```

Set `BRAND_ASSET_ROOT` to this checkout for tools supporting that configuration;
otherwise pass the checkout using the library helper's `--root` option. This
environment variable is a storage convention, not a claim that every existing
script already reads it. LFS pointers alone are not usable images. Verify actual
retrieved files and recorded approved-master hashes before editing. Remote/cloud
agents still need separately authorized LAN/VPN reachability and credentials;
never weaken a network boundary to make a clone succeed.

## Network backup and recovery

Forgejo LXC 108 stores repositories at
`/var/lib/forgejo/data/forgejo-repositories` and LFS objects at
`/var/lib/forgejo/data/lfs`. Both are on its backed-up root disk. The existing
nightly Proxmox guest backup covers the database/configuration, Git repositories
and LFS content together. An independent TrueNAS pull stores guest archives at
`/mnt/Recovery/guests/homelab-proxmox-guests`. Consult current live schedules and
[backup documentation](../../05-Backups.md), not remembered times.

On 2026-11-06, the Proxmox schedule was enabled at 00:30, retention daily 7 /
weekly 4 / monthly 6. TrueNAS task 1 was enabled at 01:00 and latest state SUCCESS.
Times are in their respective scheduler timezones. The latest observed independent
LXC 108 archive was `vzdump-lxc-108-2026_11_06-00_39_00.tar.zst`, 1,637,006,398
bytes. These archives predate the import; they are not evidence the artwork has
already been backed up. No additional TrueNAS guest-dataset snapshot retention or
new offsite artwork copy is claimed.

Before migration graduation, verify a post-import guest archive, independent copy,
matching archive hashes and integrity, and isolated recovery of Git plus LFS
objects with representative asset hashes matching the imported inventory. A plain
Git mirror can omit LFS content and is insufficient by itself. Restore into an
isolated location before considering any production replacement. Never delete a
working repository or the original Mac library as a recovery shortcut.

## Publication gates

Record the actual imported asset commit, source inventory/hash checks, independent
clone result and post-import restore proof in the
[migration project](../../projects/Brand-Asset-Library-Forgejo.md). Only then update
this entry point and the installed skill to declare the shared checkout canonical.
Approval of migration does not approve a logo draft or change its master hash.
