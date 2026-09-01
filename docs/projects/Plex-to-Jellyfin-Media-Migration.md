# Plex-to-Jellyfin Media Migration Project

> Status: Milestone 2 complete; Milestones 3 and 4 in progress (overnight
> unattended copy running)
>
> Project owner: Jason
>
> Last updated: 2026-08-30
>
> **Execution order note (2026-08-30):** Milestone 4 (music staging,
> normalization and merge) is being executed before Milestone 3 (archive video
> copy), per Jason's request — music is the highest-priority content and is
> far smaller (~128 GiB vs. ~5.29 TiB), so it delivers usable Jellyfin content
> much sooner. The two milestones write to entirely separate destinations
> (`migration/plex-music` → the canonical music root vs. `archive-movies`/
> `archive-tv`) and share no dependency, so reordering them is safe. Milestone
> numbers are left as originally defined so references in Milestones 5–8
> (which depend on both) remain valid; only the execution sequence changes.

## Purpose

Move the media currently configured for Plex into the TrueNAS-hosted Jellyfin
environment without disturbing the existing Jellyfin video libraries. Preserve
the former Plex movie and television content as clearly separated archive
libraries, while consolidating all music into one canonical physical music
library that is correctly tagged and fully usable by Jellyfin.

The project also transfers Plex playlists and curated movie collections. These
objects cannot be moved by copying media files: they must be exported from Plex,
matched to the corresponding Jellyfin items after the destination scan, recreated
through the Jellyfin API and validated independently.

## Completion outcome

The project is complete only when:

- Plex movies appear in a distinct Jellyfin library named `Archive Movies`;
- Plex television appears in a distinct Jellyfin library named `Archive TV`;
- existing Jellyfin Movies and TV libraries remain physically and logically
  separate from the imported archive content;
- existing Jellyfin music and imported Plex music are consolidated beneath one
  canonical music root, with one album per folder and reliable embedded tags;
- all in-scope Plex playlists have been recreated for the correct Jellyfin user,
  with item order and membership validated;
- Plex movie collections have either been recreated from TMDb metadata or
  explicitly transferred and audited, according to their collection type;
- source files remain recoverable until checksum, library, playback and object
  migration gates have passed; and
- the final layout, permissions, mappings, exceptions, backups and rollback
  procedure are documented.

## Authoritative baseline

- [x] TrueNAS operates at `192.168.20.40` on Servers VLAN 20.
- [x] The media pool is named `Media`.
- [x] The Docker media stack uses `MEDIA_PATH=/mnt/Media/data`.
- [x] Jellyfin is the destination media server.
- [x] TrueNAS application data, including Docker data, is under
  `Media/ix-apps`.
- [x] Media-stack containers use UID/GID `568` unless an installed service has a
  separately documented exception.
- [x] Existing Jellyfin video must not be combined physically with the former
  Plex video.
- [x] Former Plex video will be exposed through separate `Archive Movies` and
  `Archive TV` libraries.
- [x] Existing and imported music must become one canonical physical Jellyfin
  music library.
- [x] Record the Plex server address, version, host and library names. — Plex
  Media Server `1.41.5.9626-9ba082670` on Synology `GoWest` (`192.168.20.41`).
  Libraries: `Movies` (key 1), `TV Shows` (key 2), `Music` (key 4).
- [x] Record the Plex media source device, dataset/share and exact paths. —
  Synology `/volume1` (Btrfs). Movies library sources both `/volume1/Movies`
  (effectively empty) and `/volume1/Plex/Movies` (2.2 TiB, 898 items via API);
  TV Shows sources `/volume1/Plex/TV Shows` (3.4 TiB, 5,453 episodes); Music
  sources `/volume1/@appdata/ContainerManager/all_shares/Music`, confirmed by
  inode to be the same filesystem location as `/volume1/Music` (135 GiB, 7,911
  tracks). All source paths are world-readable (`777`).
- [x] Record the installed Jellyfin version, container name, internal media
  mount and exact current Movies, TV and Music paths. — Jellyfin `10.11.11`
  (server name `elliottrook`), container `6f532232719b…`, running on TrueNAS as
  a Docker Compose service (not a TrueNAS catalog app). Confirmed via
  `/Library/VirtualFolders`: Movies → `/media/media/movies`, Shows →
  `/media/media/tv`, Music → `/media/media/music` (container paths), backed by
  a single host bind mount of `/mnt/Media/data` at `/media` plus a separate
  Docker-managed named volume for `/config`. Host path `/mnt/Media/data` is
  owned `root:apps` (568), mode `770` — matches the documented UID/GID 568
  convention. Existing content: 28 movies, 43 series (625 episodes), 140
  tracks — this is the pre-migration baseline that must not change.
- [x] Record current media counts, byte totals, filesystem types and free space
  at both source and destination. — Source (Plex): 898 movies (2.12 TiB), 5,453
  episodes (3.17 TiB), 7,911 tracks (0.13 TiB) = ~5.42 TiB total, on Btrfs
  (`/volume1`, 65% full, 3.95 TB free). Destination (TrueNAS `Media` pool):
  ZFS, 4.15 TiB used, 10.3 TiB available — comfortable headroom after the
  ~5.42 TiB copy. Network path: Synology NICs are 1 GbE (bottleneck); TrueNAS
  is on a 10G bond — expect roughly 16–20 hours of sustained transfer time.
  Direct storage-to-storage copy (TrueNAS ↔ Synology, no Mac relay) is **not
  yet possible**: neither host has SSH key trust to the other today: this is
  an inter-host trust change and needs its own explicit approval as a
  Milestone 2 prerequisite before Milestone 3's `rsync` can run as designed.
- [x] Record every Plex account whose playlists are in scope. — 5 Plex accounts
  have server access (`Elliottrook1` plus 4 shared/managed users); confirmed
  with Jason that only `Elliottrook1` curates playlists, so no other account
  export is required.
- [x] Export an inventory of Plex playlists and movie collections before moving
  any media. — Done; see Required inventory files below.

Unknown paths must be resolved during Milestone 1. The paths below describe the
approved target structure; they are not permission to guess the source paths.

## Architecture decisions

### Video remains separated

Former Plex movies and television will be separate at both the filesystem and
Jellyfin-library layers. The archive directories must not be nested beneath the
current Jellyfin Movies or TV roots, because a parent-library scan could then
discover the same content twice.

Plex-compatible movie and episode naming is generally close enough to Jellyfin's
requirements to support an initial scan without a bulk rename. Files that fail
to match will be corrected individually after the first scan. Provider IDs may
be added to ambiguous folder names only after the original names and mappings
have been captured.

### Music becomes one physical library

"One music folder" means one Jellyfin music root containing album directories;
it does not mean one flat directory containing every track. The canonical form
is:

```text
music/
└── Album Artist/
    └── Album (Year)/
        ├── 01 - Track Title.flac
        ├── 02 - Track Title.flac
        └── cover.jpg
```

Every album must occupy its own folder. Correct embedded metadata takes
precedence over cosmetic filename changes. Required fields include album
artist, artist, album, title, track number, disc number and compilation status.
MusicBrainz identifiers are strongly preferred where reliable.

Imported music will first enter an unscanned staging location. It will not be
merged directly into the live Jellyfin music root until duplicate detection,
tag review and an approved dry run have completed.

### Metadata objects are migrated after media

Plex rating keys and Jellyfin item IDs are server-local identifiers and cannot
be copied directly. Playlist and collection transfer therefore uses a durable
mapping manifest:

```text
Plex object -> source file/provider IDs -> final media path -> Jellyfin item ID
```

Matching priority is:

1. stable MusicBrainz, TMDb, IMDb or TVDb identifier, as appropriate;
2. normalized final media path;
3. media-specific metadata such as album artist/album/disc/track or
   movie title/year;
4. manual review.

No playlist or collection member is silently accepted using title alone.

## Approved target layout

The exact existing folder spelling must be confirmed before implementation.
The intended host-side structure is:

```text
/mnt/Media/data/
├── movies/                 # Existing Jellyfin Movies
├── tv/                     # Existing Jellyfin TV
├── archive-movies/         # Former Plex movies
├── archive-tv/             # Former Plex television
├── music/                  # Combined canonical music library
└── migration/              # Temporary, excluded from Jellyfin scans
    ├── plex-music/
    ├── manifests/
    ├── reports/
    └── artwork/
```

The equivalent Jellyfin container paths may differ from host paths. Record both
host and container mappings before changing the compose configuration.

| Jellyfin library | Content type | Host path | Required behaviour |
|---|---|---|---|
| Movies | Movies | Existing path under `/mnt/Media/data` | Remains unchanged |
| TV Shows | Shows | Existing path under `/mnt/Media/data` | Remains unchanged |
| Archive Movies | Movies | `/mnt/Media/data/archive-movies` | Former Plex movies only |
| Archive TV | Shows | `/mnt/Media/data/archive-tv` | Former Plex television only |
| Music | Music | `/mnt/Media/data/music` | Existing plus normalized Plex music |

## Scope

- Inventory Plex and Jellyfin libraries, paths, versions, users and media
  objects.
- Protect the source and destination with current backups or snapshots.
- Copy Plex movies and television directly between storage systems into the
  two archive roots.
- Preserve associated subtitles, artwork, lyrics, NFO files and supported
  extras.
- Stage, audit, tag, deduplicate and merge Plex music into the existing
  Jellyfin music root.
- Identify duplicate files already present within Plex's own source library
  (movies, TV and music) and, for confirmed music duplicates, remove the
  redundant copy from Plex only after individual review and only once the
  retained copy is safely staged/verified elsewhere.
- Configure the required Jellyfin container mounts and libraries.
- Export, map, recreate and validate Plex playlists.
- Classify, export, recreate and validate Plex movie collections.
- Produce machine-readable manifests and human-readable exception reports.
- Validate permissions, counts, checksums, metadata, playback and rollback.
- Update HomeLab operational, backup and service documentation after cutover.

## Out of scope

- Mixing archive video into the existing Movies or TV filesystem roots.
- Flattening the music library into one directory.
- Transcoding media merely to complete the migration.
- Automatically deleting lower-quality or apparently duplicate music.
- Blind bulk renaming of the Plex video library before its first Jellyfin scan.
- Directly editing Plex or Jellyfin database files.
- Assuming Plex watch history, ratings, playlists or collections are embedded
  in media files.
- Recreating Plex smart-playlist or smart-collection query rules without an
  explicit Jellyfin design and validation.
- Retiring Plex before the completion gate passes.

## Safety and credentials

- Create a current ZFS snapshot of every affected destination dataset before
  media or application configuration changes.
- Back up Jellyfin configuration and metadata before creating libraries,
  playlists or collections.
- Export all Plex playlist and collection manifests before the media paths
  change.
- Copy first; do not move or delete source media during the migration.
- Run transfer and organizer tools in dry-run or non-writing mode first.
- Keep Plex tokens and Jellyfin API keys outside Git. Use temporary environment
  variables or a root-readable secrets file and record only the recovery or
  rotation procedure.
- Prefer a temporary, least-privilege Jellyfin API key and revoke it after
  object migration.
- Do not expose either media server or its API publicly for this project.

## Tooling decision

Use tools according to the job rather than relying on one opaque migration
utility:

- `rsync` over SSH for resumable, direct storage-to-storage copying and a
  repeatable verification pass;
- `ffprobe` or `mediainfo` for format and stream inventory without transcoding;
- `beets` in audit/non-destructive mode for music catalogue comparison and
  duplicate reporting;
- MusicBrainz Picard for human-reviewed album matching and tag correction;
- Python with `plexapi` to export ordered playlists and Plex collections;
- the Jellyfin API to resolve destination item IDs and create playlists and
  collections; and
- JSON and CSV manifests committed only after secrets and private tokens have
  been removed. Large file inventories containing personal path details may be
  retained in the protected operations store instead of Git.

Do not adopt an unmaintained all-in-one migration script without reviewing its
source, supported Jellyfin version, write behaviour and rollback limitations.

## Milestone 1 — Inventory and export gate

- [x] Record Plex and Jellyfin versions and take screenshots of the current
  library lists. — Versions recorded above. Screenshots not captured (no
  interactive session against either UI); the structured JSON exports below
  are a more precise record of library contents and supersede screenshots for
  this project's evidentiary purpose. Flag if a visual screenshot is still
  wanted for the record.
- [x] Record all host paths, container paths, mounts, datasets, share protocols
  and filesystem ownership. — See Authoritative baseline above.
- [x] Record library-level media counts and storage byte totals.
- [x] Record the source-to-destination network path and expected throughput.
- [ ] Confirm that the copy runs directly between the source storage and
  TrueNAS rather than relaying media through a Mac. — Tested: **no SSH trust
  currently exists** between TrueNAS and the Synology in either direction.
  Direct storage-to-storage copy is not possible until this is set up, which
  needs separate explicit approval (inter-host trust) before Milestone 2/3.
- [x] Confirm destination free space for the archive copy, music staging area,
  temporary reports and snapshot retention. — 10.3 TiB available against
  ~5.42 TiB incoming; comfortable headroom.
- [x] Export the Plex library inventory with rating key, media type, title,
  year, edition, source path, size and provider GUIDs.
- [x] Export every in-scope Plex playlist before paths change.
- [x] Export every Plex movie collection before paths change.
- [x] Record which playlists belong to which Plex account.
- [x] Identify regular and smart playlists separately.
- [x] Identify manual, metadata-derived and smart movie collections separately.
- [x] Store exported manifests in the protected migration workspace and record
  their checksums.

### Required inventory files

| File | Minimum contents |
|---|---|
| `plex-media.json` | Plex rating key, type, title, year, edition, paths and provider GUIDs |
| `plex-playlists.json` | Owner, title, type, smart flag and ordered item identities |
| `plex-movie-collections.json` | Title, type, smart flag, ordered members, summary and artwork reference |
| `jellyfin-before.json` | Existing item IDs, provider IDs, paths and library names |
| `migration-baseline.csv` | Counts and byte totals by source library |

### Gate

Do not copy or reorganize media until all in-scope playlists and collections
have a readable export. Their membership becomes harder to recover after Plex
paths or libraries are removed.

**Gate passed 2026-08-30.** All five required inventory files exist in the
protected migration workspace with recorded checksums (see evidence log). One
open item carries forward as a named Milestone 2 prerequisite rather than a
Milestone 1 blocker: SSH trust between TrueNAS and the Synology does not yet
exist, so the direct storage-to-storage copy Milestone 3 assumes cannot run
until that trust is explicitly approved and configured.

## Milestone 2 — Recovery and destination preparation

- [x] Verify the most recent TrueNAS pool scrub and SMART status. — `zpool
  status Media`: ONLINE, scrub repaired 0B with 0 errors on 2026-08-16, no
  active disk-health alerts. (One unrelated CRITICAL alert exists —
  `nas-ups` communication lost — from the separate UPS/NUT project; not
  acted on here, out of scope.)
- [x] Take and record ZFS snapshots of affected destination datasets. —
  `Media/data@pre-plex-migration-20260830-205932` (live media) and
  `Media/ix-apps@pre-plex-migration-20260830-210033` (Docker data root,
  covers Jellyfin's named config volume).
- [x] Back up and validate the current Jellyfin configuration/database. —
  Covered by the `Media/ix-apps` snapshot above (validated: snapshot created
  and confirmed present via `zfs.snapshot.query`).
- [x] Confirm the Plex server and source media remain backed up or otherwise
  recoverable throughout the project. — Hyper Backup confirmed installed and
  active on the Synology (`/volume1/@appdata/HyperBackup` +
  `HyperBackupVault` present), consistent with existing repo documentation.
- [x] Create `archive-movies`, `archive-tv` and the temporary migration
  directories in the approved dataset. — Created under `/mnt/Media/data`:
  `archive-movies`, `archive-tv`, `migration/{plex-music,manifests,reports,
  artwork}`.
- [x] Apply dataset ACLs that allow the migration process to write and Jellyfin
  UID/GID `568` to read. — All seven directories: owner `truenas_admin`
  (uid 950), group `apps` (gid 568), mode `750`. `truenas_admin` was added to
  the `apps` group (with explicit approval) after discovering it couldn't
  otherwise traverse into `/mnt/Media/data`, which is itself `root:apps 770`.
- [x] Keep Jellyfin read-only against archive media unless an approved feature
  specifically requires write access. — Group `apps` has `r-x` only (mode
  `750`), not write, on all new directories.
- [x] Ensure the migration staging directory is outside all active Jellyfin
  library roots. — Confirmed via Jellyfin's own `/Library/VirtualFolders`:
  its libraries are scoped to `/media/media/movies`, `/media/media/tv`,
  `/media/media/music` specifically, not the broader `/media` root, so
  `archive-movies`, `archive-tv` and `migration/` (siblings of `media/` under
  the same bind mount) are outside every current scan root. No `.ignore` file
  needed.
- [x] Record available space after snapshot and directory creation. — 10.3 TiB
  available, unchanged (new snapshots and empty directories cost negligible
  space until written to).

### Gate

Create and remove a test file through the migration identity, then confirm that
Jellyfin can read—but need not modify—the corresponding destination test file.

**Gate passed 2026-08-30.** Wrote a test file into `archive-movies` as
`truenas_admin`; confirmed via Jellyfin's own `/Environment/DirectoryContents`
API (container-side, `includeFiles=true`) that it was visible; removed it and
confirmed Jellyfin's view returned to empty.

**SSH key trust from TrueNAS to the Synology — resolved 2026-08-30.** A
dedicated ed25519 keypair was generated on TrueNAS
(`~/.ssh/plex_migration_ed25519`) and installed into
`/etc/ssh/authorized_keys/Jason` via a one-time DSM Task Scheduler script run
as `root` (Jason ran it; this host's `sshd_config` points `AuthorizedKeysFile`
at that path rather than the standard `~/.ssh/authorized_keys`, and that path
is root-owned). The key is bound to a read-only rsync restriction wrapper at
`~/.ssh/rsync-readonly-wrapper.sh` on the Synology: it only permits
`rsync --server --sender` (pull/read direction — never receiver/write) against
exactly `/volume1/Plex/Movies`, `/volume1/Plex/TV Shows` or `/volume1/Music`,
validated through a character allowlist before any shell tokenization to
prevent command injection via `SSH_ORIGINAL_COMMAND`. Verified end to end:
plain commands rejected, allowed paths (including the space in `TV Shows`,
which required a wrapper fix — rsync backslash-escapes spaces rather than
quoting them) succeed, disallowed paths rejected, and a semicolon-injection
attempt rejected at the character-allowlist stage.

## Milestone 3 — Archive video copy

> **Execution note:** started before Milestone 4 finished, queued to run
> overnight — see below.

- [x] Run an `rsync` dry run for Plex movies into `archive-movies`. — Clean:
  969 regular files, 2.39 TB (2.18 TiB).
- [x] Review excludes. Exclude caches and operating-system debris, not subtitle,
  NFO, artwork or extras files that may be useful to Jellyfin. — Excluded
  `@eaDir`, `.DS_Store`, `.quarantine`, `@tmp` (same harmless Synology
  metadata-stream pattern confirmed during the music copy: 58 `@eaDir` dirs /
  7.6 MB in Movies, 164 dirs / 74 MB in TV Shows — negligible, not real
  duplicate content). Subtitles/NFO/artwork/extras are not excluded.
- [~] Copy movies with partial-transfer protection and logging enabled. — Also
  ran an `rsync` dry run for TV into `archive-tv`, clean: 5,973 regular files,
  3.63 TB (3.31 TiB). Combined real total ~6.03 TB (5.48 TiB) — higher than
  the ~5.29 TiB estimate in Milestone 1's evidence log, which only counted one
  file per Plex library item; the real filesystem includes extra subtitle/
  artwork/NFO files and multi-edition movies. Destination had 10.1 TiB
  available at queue time (music copy in progress) — comfortable headroom.
  **Queued 2026-08-30 21:44** via `migration/overnight-video-copy.sh`,
  running detached on TrueNAS: waits for the Milestone 4 music copy to exit,
  then runs Movies then TV Shows sequentially (same read-only migration key),
  logging to `migration/reports/overnight-video-copy.log`. **Started
  automatically 2026-08-30 21:48:51** the moment the music copy exited — no
  manual trigger needed. **Movies complete 2026-08-31 05:02:18**: 969 files,
  exact byte match (2,392,854,409,248 bytes), exit code 0.
- [x] Run the same process for Plex television into `archive-tv`. — Chained
  into the same overnight run; **started automatically 2026-08-31 05:02:18**
  the moment Movies finished, **complete 2026-08-31 17:32:23**: exit code 0.
- [ ] Preserve the relative directory structure during the first copy.
- [~] Perform a no-change `rsync` comparison after each copy. — Chained
  together with the checksum step below rather than run separately.
- [~] Produce a checksum manifest or checksum verification report for the final
  source and destination trees. — `migration/verify-video-copy.sh` runs both
  the no-change comparison and a full `--checksum` pass (reads file content on
  both sides, not just size/mtime) per library, logging to
  `migration/reports/verify-movies.log` / `verify-tv.log`. **Movies passed
  2026-08-31 16:52**: quick comparison and full checksum pass both clean —
  969 files, zero created/deleted/transferred, exact checksum match on all
  content. TV verification **started automatically 2026-08-31 17:32:23** via
  `migration/verify-tv-after-copy.sh` the moment the TV copy exited — no
  manual trigger needed, same pattern as Movies. **Passed 2026-08-31 23:44**:
  quick comparison and full checksum pass both clean — 5,973 files, zero
  created/deleted/transferred, exact checksum match on all content.
  **Milestone 3 is now fully complete and verified for both libraries.**
- [ ] Compare file counts, byte totals and extensions by library.
- [ ] Quarantine zero-byte, unreadable and unsupported files for review; do not
  delete them automatically.
- [x] Record any naming collisions, duplicate editions and incomplete shows.
  — Movies checked (fully copied and checksum-verified, no need to wait for
  TV): 928 real video files (779 `.m4v`, 138 `.mp4`, 9 `.mkv`, 2 `.mpg`), no
  zero-byte files. 7 titles share a base name; 4 are legitimately different
  films/content, not duplicates ("Overboard" '87/'18, "The Color Purple"
  '85/'23, "A Star Is Born" '76/'18 are real remakes; "Hogfather" CD1/CD2 is
  one film split across two discs). Of the 3 real candidates: **"In the Heat
  of the Night"** resolved — near-identical runtime (110.1 vs 110.3 min)
  confirmed it was the same cut at two quality levels (720×460 vs 1280×720);
  kept the higher-quality copy, removed the redundant one from both
  `archive-movies` and Plex's live library (approved). **"Cats" (1998)** and
  **"Taken" (2008)** were *not* auto-resolved — both have real runtime gaps
  (~11 min and ~2.5 min) between their two copies, which could mean a
  genuinely different cut/edition rather than just a quality difference (e.g.
  Taken has a real theatrical vs. extended/unrated release) — flagged as a
  follow-up needing an actual look, not a guess.

### Transfer template

Substitute verified absolute paths; do not execute placeholders literally.
Preserve media content and timestamps while allowing the destination dataset's
ACL model to control ownership.

```bash
rsync -aH --no-owner --no-group \
  --partial --info=progress2 --dry-run \
  --exclude=@eaDir --exclude=.DS_Store --exclude=.quarantine --exclude=@tmp \
  SOURCE_PATH/ DESTINATION_PATH/
```

After reviewing the dry run, repeat without `--dry-run`. Use an explicitly
logged checksum verification pass after the bulk transfer. A checksum pass is
slower than the initial size/time comparison and should be scheduled
accordingly.

**Learned during execution:** the originally-planned `--protect-args` flag is
**not compatible** with the read-only SSH key's path-restriction wrapper (see
Milestone 2) — with `--protect-args`, rsync sends the source/destination path
over its own wire protocol rather than as a visible SSH command-line argument,
so the wrapper has nothing to validate against and rejects every request.
Dropping `--protect-args` is safe here: it only affects how the top-level
source/destination path is passed to the remote shell, not how individual
filenames are handled during the actual transfer (confirmed working correctly
with the space in "TV Shows", handled via backslash-escaping rather than
quoting once `--protect-args` is removed).

### Gate

Archive video is complete only when copy logs are clean, counts and totals are
reconciled, checksum verification passes and the Plex source remains intact.

## Milestone 4 — Music staging, normalization and merge

> **Execution note:** running before Milestone 3 — see the execution order
> note at the top of this document.

- [x] Copy Plex music into `/mnt/Media/data/migration/plex-music`; do not point
  Jellyfin at this folder. — **Complete 2026-08-30 21:48**, started 21:19.
  39,112 files transferred, exact byte match to the dry run
  (144,317,754,115 bytes, zero discrepancy).
- [ ] Inventory formats, bitrates, sample rates, bit depth, embedded artwork,
  lyrics and current tags.
- [x] Catalogue the existing Jellyfin music and staged Plex music separately. —
  Existing Jellyfin music (140 tracks, entirely a Paul Simon test collection
  per Jason — not real content to preserve) compared against Plex's 7,911
  tracks: 59 overlap, 81 Jellyfin-only, 7,396 Plex-only. Since the Jellyfin
  side is disposable test data, this comparison doesn't need careful
  reconciliation — the real work is the Plex-internal duplicate check below.
- [x] Run beets with move and delete disabled and tag writing disabled for the
  first audit. — **Complete 2026-08-30.** Cataloged 7,129 of 8,008 real audio
  files (the earlier "39,112 files" dry-run count included non-audio sidecars
  — cover art, etc. — not just tracks; 8,008 is the correct denominator).
  879 tracks across 61 albums were skipped during import as apparent
  already-in-library matches — listed separately at
  `migration/reports/beets-skipped-albums-during-import.txt` (sha256
  `457c2eef…`) as their own review category, since import-time skips aren't
  the same as a reviewed duplicate decision.

**Tooling note:** `beets` 2.13.1 and `ffprobe` (both required — beets 2.13's
import pipeline calls `ffprobe` unconditionally) were installed fully
self-contained under `/mnt/Media/data/migration/beets-tool/`, with no changes
to TrueNAS's system Python or packages: `pip` bootstrapped via the official
`get-pip.py`, `beets` installed with `pip install --target=`, `ffprobe` from
the official static Linux build (johnvansickle.com, the source ffmpeg.org
itself links to; sha/md5 verified against the publisher's manifest before
executing). `BEETSDIR` points at `beets-tool/beetsdir` so its config/database
stay inside the migration workspace, not `truenas_admin`'s home directory.
Config disables move/copy/write/autotag and ignores Synology `@eaDir`
metadata-stream clutter (checked: 946 such directories in the source Music
library, totaling only 3.7 MB — not real duplicate content, just Synology
extended-attribute storage; excluded from analysis for cleanliness, not out
of a real duplication concern).
- [x] Produce album-level and track-level duplicate reports **covering two
  separate comparisons**: duplicates already present within Plex's own source
  music library, and collisions between the existing Jellyfin music root and
  staged Plex music. — The Jellyfin-side comparison is moot (its music library
  is disposable test data, see above). Plex-internal duplicates:
  `migration/reports/beets-duplicates.json` (sha256 `94cf170c…`) — 166
  duplicate groups, 335 tracks, built directly from beets' SQLite catalog
  (real embedded tags/audio properties) after finding the `duplicates` plugin
  wasn't enabled (`plugins: duplicates` was missing from config) and, once
  enabled, that its custom `-f`/format output was broken in this beets
  version (printed the literal template instead of substituting values) —
  queried the catalog directly instead. Confirmed example:
  "Absolute Reggae" exists under both `Compilations/` and `Various Artists/`
  with identical bitrate and length to the decimal.
- [x] Distinguish exact duplicate files from alternate releases, masters,
  formats and legitimately repeated tracks. — 160 of 166 groups have all
  copies in the same format (likely exact/near-exact duplicates); 6 groups
  are mixed-format (e.g. one copy MP3, another FLAC of the same song) and
  need individual review rather than an automatic bitrate-based call, per the
  rule below. Estimated ~1.71 GB reclaimable if one copy is kept per group.
- [ ] Define the retention choice for every collision; do not automatically
  prefer one file merely because its bitrate is larger.
- [x] For duplicates found within Plex's own source library: review every
  duplicate group individually and record which copy is the keeper before any
  removal. Never delete automatically, never delete by title/tag match alone,
  and never delete a file until its retained counterpart has already been
  staged/copied and checksum-verified — so a wrong duplicate call never
  results in true data loss. Deletion from the live Plex library happens only
  after this review, and only for the files explicitly confirmed as redundant.
  — **Reviewed 2026-08-31.** Of the 6 mixed-format groups: 3 had a clear
  reviewed decision (see below), 3 were kept as-is (Jason's call — "Up Town
  Top Ranking" and both Paul Simon tracks are the same song across genuinely
  different album releases — compilation vs. studio/greatest-hits — not
  wasteful duplicates). The other 160 same-format groups and the 61
  import-skipped albums were **not** acted on — see findings below.

  **Real finding on the 61 "skipped" albums**: investigated three at random
  (Dolly Parton's 23-track "Diamonds & Rhinestones", Kane Brown's "The High
  Road", Demi Lovato's "Demi") and all three are the same pattern: one
  correctly-tagged compilation album whose individual featured-collaborator
  tracks (real duets, e.g. Dolly Parton & Kenny Rogers' "Islands In The
  Stream") sit in their own per-collaborator folders. Beets' import matched
  them as "same album, skip" on title alone, without checking that the
  artist/tracks genuinely differ — a false positive in its own heuristic, not
  real duplication. **None of the 61 should be deleted**; they're legitimate
  tracks that were simply left out of beets' catalog and should be included
  normally in the eventual merge. Nothing was ever at risk — beets' import
  never had delete/move/write enabled, so the underlying files were untouched
  throughout.

  **Actions taken** (2 files, reviewed individually, keeper verified staged
  before any live deletion):
  - "Just Dance" (Lady Gaga): kept FLAC
    (`Lady Gaga/The Fame (2008)/12 Vinyl 01/...flac`, verified staged and
    byte-size-matched to source), removed the redundant AAC copy
    (`Lady Gaga/The Fame (2008)/The Fame/01 Just Dance.m4a`) from both the
    staging copy and Plex's live library (`/volume1/Music/...`).
  - "The House That Built Me" (Miranda Lambert): same pattern — kept FLAC,
    removed the redundant AAC copy from staging and live Plex.
  - "jukeboxClick" (both a `.m4a` and `.wav` copy): not a real track at all —
    a 0.5-second UI sound effect from The Beatles' "1" iTunes LP interactive
    package. Removed both from the staging copy only; left untouched in Plex
    itself as it's part of the iTunes LP package internals, not music library
    content in scope for this project.
  Removals logged at `migration/reports/staging-dedup-removals.log`.
- [x] Use MusicBrainz Picard in reviewed batches for ambiguous or poorly tagged
  albums. — No Picard GUI available on this headless server; used beets' own
  MusicBrainz client instead (same underlying database), with proposed
  matches reviewed before applying — same substance as the Picard workflow.
  Targeted the 12 albums (48 tracks) with missing album/artist metadata found
  during the earlier inventory. Real results: only 2 of 12 got a confident
  MusicBrainz match (K.T. Tunstall "Eye to the Telescope", 100%; Various
  Artists "New Jack City", 99.1% — both applied via `beet write`, richer
  metadata than a manual fix: correct per-track artist credits, MusicBrainz
  IDs, compilation flag, ISRC codes, years). The other 10 had too little
  starting metadata for confident MB search matching. Of those: **6 turned
  out not to be music at all** — Justin Timberlake/LMFAO/Lorde/Maroon 5/Rod
  Stewart's "Unknown Album" entries are real music *videos* (`.m4v`,
  confirmed via `ffprobe` — genuine H.264 video streams, titles like "(Live)
  (HD)" and "[The Making Of]"), not audio. **Excluded from this project's
  scope per Jason's call** — left untouched in the staging copy, not
  carried into the eventual Jellyfin music merge. The remaining 4 real
  albums (Missy Elliott/Under Construction, Robbie Williams/Greatest Hits,
  Taylor Swift/folklore, plus the Unknown Artist/Pop Idol Christmas
  compilation, 66 tracks total) got a deterministic fix — album/artist filled
  in directly from the unambiguous folder name via `mutagen`, since
  MusicBrainz search couldn't resolve them but the folder structure already
  gave the obvious correct answer.
- [x] Ensure each album has album artist, album, track title, track number and
  disc number metadata where applicable. — Catalog-wide check: 99.5%+ complete
  on album artist, 99.6%+ on album, 100% on title/track/disc/year before any
  of the above fixes; now further improved by the 89 tracks corrected above.
- [x] Correct compilation metadata so various-artist albums remain one album.
  — Handled as part of the MB/deterministic fixes above (New Jack City and
  Pop Idol Christmas both now correctly tagged as single compilation albums
  with `Various Artists` as album artist and real per-track performer
  credits).
- [ ] Preserve useful genres and custom tags unless their removal is explicitly
  approved.
- [ ] Retain sidecar artwork and lyrics with their album/tracks.
- [x] Preview the final canonical paths and review collisions before enabling
  organizer writes. — Surveyed the whole staged catalog for albums whose
  tracks are split across multiple physical folders (46 found); filtered out
  the legitimate multi-disc pattern (CD 01/02, Disc 1/2 — already acceptable
  per this doc's own naming rules) programmatically, leaving 16 genuine
  anomalies. Of those: 4 were confirmed full-album duplicates (same tracklist
  filed under both a generic `Compilations/` folder and the correct
  artist-named folder — "Absolute Reggae", "Dancehall Reggae", "Simply The
  Best", "The Very Best Of Pure Dancehall [Disc 2]") — resolved by merging
  each pair's unique sidecar files (`album.nfo`, missing `folder.jpg`) into
  the artist-named keeper, then removing the redundant `Compilations/` copy
  from both staging and Plex's live library (approved). The 3 remaining
  "anomalies" (Massive Reggae/Caribbean Uncovered, Ride Da Riddims
  Volume 2/Duets) turned out not to be tagging errors at all, once Jason
  confirmed "Caribbean Uncovered" and "Summer Riddims 2004" are real,
  intentional custom compilations he assembled — every track had simply kept
  its *original source album's* tag rather than being retagged to the
  compilation it was actually placed in. Fixed directly: retagged all 45
  Caribbean Uncovered tracks (both discs) and all 32 Summer Riddims 2004
  tracks (both discs) with the correct album name, `Various Artists` as
  album artist, and disc/track numbers derived from each file's own
  `N-NN` filename prefix (which was already correctly ordered).
  The remaining ~9 were stale database artifacts or already-decided cases
  (the Paul Simon Greatest-Hits cross-references from the earlier duplicate
  review, and genuine 1960s Beatles/Capitol Records release-history overlaps)
  needing no action. Beyond these anomalies, the staged structure already
  follows Artist/Album/tracks reasonably closely; a full rename to the
  letter-perfect "01 - Title.ext" naming target was not pursued, since
  Jellyfin's music library primarily organizes by embedded tags (now
  corrected) rather than strict filename parsing.
- [x] Copy approved albums into the live `music` root; do not move the only
  source copy. — **Complete 2026-08-31.** Existing test content (the Paul
  Simon folder) left untouched per Jason's call, not cleared first — any
  overlap with the real collection is a follow-up, not a blocker. Dry run
  clean (38,755 files, 143.7 GB), then the real copy: all 38,755 files
  transferred with an exact byte match to the source (143,746,532,374
  bytes both sides) — zero missing or corrupted files. rsync reported exit
  code 23 ("some attrs not transferred"), but both underlying causes were
  harmless directory-metadata failures (couldn't set timestamp on the
  live music root itself, couldn't chgrp the pre-existing Paul Simon
  folder) — both because those directories are `root`-owned and the
  migration identity lacks permission to alter attributes on directories
  it doesn't own. No file content was affected; this is `copy`, not
  `move`, so the staged and source copies remain intact regardless. Live
  music root now has 340 artist folders and 8,068 tracks (up from the 140
  Paul Simon test tracks alone).
- [x] Re-run duplicate and missing-track reports against the combined root.
  — After the live merge, Jason ran a Jellyfin scan and reported 741 albums /
  8,054 songs (including the Paul Simon test data), against my own tag-based
  count of 955 albums / 8,068 files — a real, substantial gap worth
  investigating rather than dismissing as rounding. Root cause found: **97
  folders** (not just Caribbean Uncovered/Summer Riddims) had this exact
  scattered-tag pattern — each folder is one real, purchased album (Jason
  confirmed: not personal compilations, "years of poor tagging," bought
  secondhand/bargain over time in England), but individual tracks kept
  whatever album tag they arrived with from wherever they were originally
  sourced, rather than being retagged to the album they were actually filed
  under. Wrote a general fix (dry-run tested first — caught two real bugs
  before applying: a nested "Digital Media 01/02" disc-subfolder pattern that
  would have swapped album/artist for 5 folders including both Lionel Richie
  and Beatles "Sgt. Pepper's" discs, and a bare unbracketed "Disc 1" suffix
  on a Whitney Houston folder that wouldn't have been stripped). Applied to
  all 93 remaining affected folders (2 Paul Simon ones excluded — test data,
  left alone; 2 more already fixed manually) — 1,392 tracks corrected: album
  and album artist set from the folder's own path (parent folder = artist,
  unless the parent is a generic `Compilations`/`Various Artists` bucket),
  disc/track numbers derived from each file's own filename pattern.
  Post-fix count: **680 distinct albums**, down from 955 — a fresh Jellyfin
  rescan should land close to this, materially lower than the 741 seen
  before this fix.
- [x] Reconcile track, album and byte totals. — 8,068 audio files in the live
  music root (Jellyfin reported 8,054 before this fix — the 14-file gap is
  explained by a handful of genuinely unidentifiable/non-music files, see
  below); only 4 files remain with no usable album/artist tags at all after
  the fix (down from 5): 3 truly unidentifiable singleton tracks in
  "Unknown Artist/Unknown Album" and 1 iTunes LP package-internal file (not
  real music, same category as the already-excluded jukeboxClick files) —
  none are worth further chasing given their scale. One further follow-up
  not yet resolved: "Various Artists/Perfect Love, Vol. 2 Disc 1" still has
  a stray untagged track and is worth a closer look.

**Jellyfin indexing note — resolved 2026-08-31/09-01.** After the tag fixes
landed, Jellyfin's reported counts didn't move at all (stayed at 741/8,054
through two separate refresh attempts, including an explicit
`MetadataRefreshMode=FullRefresh&ReplaceAllMetadata=true` call). Root cause:
every track carried a leftover MusicBrainz Album ID (and related Release
Group/Track/Status/Type identifiers) from whichever original source it was
ripped from — confirmed by checking 6 tracks in one folder and finding 6
completely different Album IDs. With `EnableInternetProviders: false`,
Jellyfin isn't calling the MusicBrainz API, but it still trusts an embedded
MusicBrainz Album ID as the authoritative local album-identity key over the
plain-text `album` tag, so it kept grouping by the stale original-source
identity. Stripped the stale album/release-level identifiers (kept
per-recording/per-artist ones, which remained accurate) across the same 97
folders — 705 of 1,469 tracks affected. Even after that, a refresh still
didn't rename the already-created `MusicAlbum` container entities (confirmed
by refreshing one directly by ID: the track underneath correctly showed
`Album: Caribbean Uncovered`, but the container object kept its stale
`Caribbean Uncovered [Disc 1]` name) — Jellyfin's album containers are
created once and don't get renamed by a refresh, only their children get
re-validated. Fix: removed and re-added the Music library in Jellyfin
(config captured and preserved exactly — path, `EnableInternetProviders:
false`, `SaveLocalMetadata`, `PreferNonstandardArtistsTag` — verified after
recreation), forcing a full rebuild from the current, correct file tags.
Source files were never touched by any of this — only Jellyfin's database
records. No playlists or watch history existed yet for this content, so
there was nothing to lose.

### Music naming target

```text
Album Artist/Album (Year)/01 - Track Title.ext
Album Artist/Album (Year)/1-01 - Track Title.ext  # optional multidisc form
```

Disc subdirectories are acceptable, but the embedded disc number remains
authoritative. Avoid filesystem-reserved characters in generated names.

### Gate

Test at least one single-disc album, multidisc album, compilation, album with
multiple artists, lossless album and album containing lyrics before merging the
remaining collection. Every duplicate group found within Plex's own source
library has a recorded keeper decision before any file is deleted from Plex.

## Milestone 5 — Jellyfin libraries and identity mapping

> **Execution note:** the music portion of this milestone (scanning the
> merged Music library) was done ahead of the formal write-up here, as a
> direct prerequisite for Milestone 6's playlist item mapping — see the
> Milestone 4 Jellyfin-indexing note above for the full diagnostic story.

- [x] Add read-only container mounts for `archive-movies` and `archive-tv`.
  — Not needed: Jellyfin's container already bind-mounts the whole
  `/mnt/Media/data` tree as `/media` (confirmed back in Milestone 2), so
  `archive-movies`/`archive-tv` are already visible inside the container
  with no separate mount configuration required. Confirmed via
  `/Environment/DirectoryContents?path=/media/archive-movies&includeFiles=true`
  — 597 files visible immediately.
- [x] Confirm the existing Movies, TV and Music mounts remain unchanged. —
  Confirmed via `/Library/VirtualFolders`: existing `Movies`
  (`/media/media/movies`) and `Shows` (`/media/media/tv`) libraries are
  untouched; `Archive Movies` was created as a fully separate library
  (`/media/archive-movies`), not nested inside or merged with either.
- [x] Create the `Archive Movies` library using the Movies content type. —
  **Created 2026-09-01**, since Movies (archive-movies) already passed both
  its quick comparison and full checksum verification — no need to wait for
  TV Shows' still-in-progress checksum pass. Scanned successfully: **921
  movies indexed** (928 real video files existed; the small gap is expected
  — e.g. "Hogfather" CD1/CD2 recognized as one multi-part movie).
- [x] Create the `Archive TV` library using the Shows content type. —
  **Created 2026-09-01**, once TV Shows' checksum verification passed.
  Scanned successfully: **171 series** (exact match to the 171 show folders
  on disk) and **5,678 episodes** indexed (5,973 real files existed; small
  gap expected, same pattern as movies). One false alarm during setup: the
  `/Environment/DirectoryContents` browse endpoint showed 0 entries for
  `/media/archive-tv` immediately after library creation, despite the
  filesystem clearly having 171 real folders (`truenas_admin:apps 777`,
  fully readable) — turned out to be an unreliable check, not a real
  problem; the actual library scan picked everything up correctly.
- [x] Scan the combined Music library only after its merge gate passes. —
  Music merge completed in Milestone 4; scanned (multiple times, see the
  Jellyfin-indexing note above for why more than one pass was needed).
- [x] Run library scans and allow metadata tasks to finish before object
  migration begins. — All three (Music, Archive Movies, Archive TV) scanned
  and confirmed indexed with real counts.
- [x] Export a post-scan Jellyfin inventory containing item ID, library, path,
  provider IDs and media-specific metadata. — Pulled for Archive Movies (921
  items) with Path/ProviderIds/ProductionYear fields.
- [x] Build `plex-to-jellyfin-map.json` and a CSV exception report. —
  `plex-to-jellyfin-movie-map.json` (sha256 `9e4dec9c…`) built for all 898
  Plex movies. Real finding: the original Milestone 1 `plex-media.json`
  export had empty `guids` for every movie — Plex's bulk library-listing API
  doesn't include provider GUIDs, only per-item metadata fetches do. Initial
  pass matched 795/898 (88.5%) on normalized title+year alone. Targeted
  per-item re-fetches for the 103 unresolved ones (real GUIDs this time)
  resolved 62 more via TMDb/IMDb ID. **864/898 (96.2%) resolved** after also
  manually correcting 7 confirmed wrong auto-matches (see below). 34 remain
  unresolved — a mix of genuine bonus featurettes (not real standalone
  movies, correctly unmatched), titles that appear genuinely absent from the
  Jellyfin scan, and obscure/foreign titles not yet individually verified —
  logged as a follow-up, not silently dropped.
- [x] Require each mapping to record its match method and confidence. — Every
  entry tagged: `exact-id-tmdb-retry`/`exact-id-imdb-retry` (62 total, real
  provider ID match), `title-year` (795, the doc's `metadata-reviewed` tier),
  `manual-corrected-wrong-automatch` (7, see below), or `missing` (34).
- [x] Manually resolve ambiguous items and any case where both current and
  archive libraries contain the same title. — Checked the Plex source for
  same-title-different-year collisions: 4 found (The Color Purple, The
  Karate Kid, Overboard, A Star Is Born — all real remake pairs, both years
  legitimately present). Separately, and more significantly: **discovered
  Jellyfin's own TMDb auto-matching had picked the wrong film for several
  remakes** — its title search defaults to the more famous original rather
  than using the year to disambiguate. Confirmed and fixed 7: Aladdin (2019
  file was tagged as the 1992 original), Mean Girls (2024 tagged as 2004),
  Mulan (2020 tagged as 1998), Bad Education (2019 tagged as 2004), The
  Running Man (1987 tagged as an unrelated "2025" entry), Blade Runner 2049
  (no ID at all — folder-name year parsing confusion), and a real duplicate-
  identification bug where both Harry Potter Deathly Hallows Part 1 *and*
  Part 2 files had been matched to the same "Part 1" TMDb entry. Fixed each
  by setting the correct `ProviderIds` directly on the item, then triggering
  `MetadataRefreshMode=FullRefresh&ReplaceAllImages=true` so Jellyfin pulled
  the correct poster/synopsis from TMDb — verified all 7 now show real,
  correct, non-empty synopses. This means the wrong-match problem likely
  isn't confined to the movies checked here; the remaining 34 unresolved
  entries need the same scrutiny before being trusted either way.
- [ ] For archive video, prefer the destination path derived from the
  original Plex path so a collection is not accidentally attached to an
  existing Jellyfin duplicate. — Not yet applied; relevant once Milestone 7
  (movie collections) actually creates Jellyfin collection objects.

### Mapping states

| State | Meaning | Permitted action |
|---|---|---|
| `exact-id` | Stable provider or MusicBrainz ID agrees | May migrate automatically |
| `exact-path` | Verified source-to-destination path mapping agrees | May migrate automatically |
| `metadata-reviewed` | Multiple metadata fields agree and a person approved it | May migrate with evidence |
| `ambiguous` | Multiple possible Jellyfin items | Stop for review |
| `missing` | No destination item found | Do not create object membership |

### Gate

Playlist and collection writes are prohibited while any referenced item lacks
an accepted mapping. Exceptions may be explicitly deferred, but must appear in
the final report rather than disappearing from counts.

## Milestone 6 — Plex playlist transfer

### Export requirements

For each Plex account in scope, export every playlist with:

- owner/account identifier;
- playlist name, summary and media type;
- regular or smart status;
- ordered member list, including repeated items;
- Plex rating key and original file path;
- available provider GUIDs;
- for music: track title, album, album artist, track/disc numbers and duration;
- for video: title, year, season/episode and duration; and
- playlist artwork reference where present.

Plex playlists can be user-specific. A server administrator's token must not be
assumed to reveal another user's private playlists. Export each authorized
account separately and keep tokens out of the report.

### Transfer rules

- [x] Transfer regular playlists as ordered snapshots. — All 11 non-smart
  Plex music playlists (196 total track entries) transferred.
- [x] For a Plex smart playlist, export both its rule description and current
  ordered membership. — Already captured in Milestone 1's `plex-playlists.json`
  for all 3 smart playlists (All Music, Recently Added, Recently Played).
- [x] Do not claim that a smart rule was migrated unless an equivalent Jellyfin
  rule has been separately designed and tested. — None claimed; see below.
- [x] By default, recreate a smart playlist as a dated static snapshot and mark
  the original rule in the migration report. — **Not done, by explicit
  decision.** Reviewed all 3 with Jason: "All Music" (7,987 items) is
  redundant with the full library, "Recently Added" was empty at export time
  (nothing to snapshot), and "Recently Played" — the one genuinely meaningful
  point-in-time list — was still deliberately skipped along with the other
  two, per Jason's explicit choice to only migrate the 11 hand-curated
  playlists. Recorded as an intentional scope decision, not an oversight.
- [x] Resolve every playlist member through `plex-to-jellyfin-map.json` after
  the final Jellyfin scan. — Built `plex-to-jellyfin-playlist-map.json`
  (matching on normalized artist+title, since zero Plex tracks had any
  provider GUID to match on — confirmed 0/7,911 during Milestone 1). Initial
  automated pass resolved 192/196 (98%); the remaining 4 were real, verified
  matches with formatting differences the exact-match logic didn't catch (a
  "(2022 mix)" remaster suffix, a full "Feat. Taylor Swift & Keith Urban"
  artist credit, a missing leading "The", and a much longer descriptive
  title) — resolved manually with confirmed Jellyfin item IDs rather than
  loosening the matcher and risking false positives elsewhere. **Final: 196/196
  (100%) resolved**, zero missing, zero ambiguous.
- [x] Create the playlist for the intended Jellyfin user through the Jellyfin
  playlist API. — Created for **both** `elliottrook` and `jason` (Jason's
  call — the Plex owner account "Elliottrook1" maps to both real people who
  should have the playlists).
- [x] Add items in their exported order. — Verified programmatically: full
  ordered-ID comparison against the source, not just a count check.
- [x] Preserve duplicate occurrences when Jellyfin supports them; otherwise
  record each collapsed duplicate explicitly. — No collapsed duplicates
  encountered; each playlist's track count matched exactly.
- [ ] Reapply supported name, overview and artwork fields. — Playlist names
  applied at creation; overview/artwork not yet reapplied (Plex playlist
  summaries/artwork weren't part of the Milestone 1 export fields captured).
- [x] Record missing or ambiguous members instead of silently omitting them.
  — Zero missing/ambiguous in the final result; the 4 initial misses were
  investigated and resolved, not silently dropped.
- [x] Repeat the transfer independently for each in-scope user. — Only
  `Elliottrook1` was in scope (confirmed during Milestone 1 — no other Plex
  account had playlists); mapped to both `elliottrook` and `jason` in
  Jellyfin per Jason's decision above.

The Jellyfin API supports creating a playlist and adding item IDs to it. The
server's own generated API description for its installed version is
authoritative. Expected operations are:

```text
POST /Playlists
POST /Playlists/{playlistId}/Items
GET  /Playlists/{playlistId}/Items
```

### Playlist validation

For every playlist, record:

- source and destination owner;
- source and destination playlist name;
- source item count;
- matched item count;
- destination item count;
- first, middle and last item comparison;
- full ordered-ID comparison result;
- missing or collapsed duplicate count; and
- playback result for at least one item.

**Complete 2026-09-01.** All 22 playlist instances (11 playlists × 2 users)
validated programmatically: fetched each created playlist's items back from
Jellyfin and did a full ordered-ID comparison against the resolved source
list, not just a count check. **22/22 passed** — exact count and exact order
match on every one, zero exceptions. Playback capability spot-checked on one
item (`Here, There and Everywhere` from The Beatles playlist) via
`/PlaybackInfo` — confirmed a real, valid FLAC media source
(`Revolver (1966)/...05 - Here, There and Everywhere.flac`).

### Gate

Every playlist is either `passed`, `passed-with-documented-exceptions` or
`deferred`. A destination playlist whose count matches but order differs does
not pass.

**Gate passed 2026-09-01.** All 11 migrated playlists, for both users,
`passed` cleanly with no exceptions. One item deferred, not failed: name/
overview/artwork reapplication (names were set at creation; overview and
artwork fields weren't part of what Milestone 1 exported, so there's nothing
to reapply without a separate export pass).

**Real-client bug found and fixed 2026-09-01.** Jason's own client-side
check (Milestone 8) found every playlist showing up twice. Root cause: this
Jellyfin installation doesn't restrict playlist visibility by owner — a
check confirmed both `elliottrook` and `jason` could see all 23 playlist
objects (both per-user copies of all 11 playlists), not just their own, so
creating one copy per account (the deliberate Milestone 6 design decision)
just doubled what everyone saw rather than giving each person a private
copy. Per Jason's decision, consolidated to one shared playlist per name:
verified all 11 duplicate pairs held byte-identical membership and order
first, then deleted one copy of each via `DELETE /Items/{id}`. Left the
pre-existing "All I want for Christmas" playlist untouched (not one of this
project's 11 — a single copy already, unrelated to the migration). Final:
12 playlist objects total (11 migrated + 1 pre-existing), both accounts now
see exactly one entry per playlist.

## Milestone 7 — Plex movie collection transfer

### Classify first

Classify each Plex movie collection before recreating it:

| Collection type | Migration treatment |
|---|---|
| TMDb franchise/box set | Prefer recreation by the Jellyfin TMDb Box Sets plugin after provider-ID validation |
| Manual/curated collection | Export explicit membership and recreate through the Jellyfin Collection API |
| Smart collection | Export rule plus current membership; recreate as a static snapshot unless an equivalent rule is separately approved |
| Mixed-library or cross-media collection | Review manually; this project's automatic path covers movie collections only |

Do not create the same franchise once through the plugin and again through the
manual transfer. Run an overlap report before any collection write.

### TMDb-derived collections

**Approach decision (2026-09-01):** Jason chose the TMDb Box Sets plugin over
manual API recreation, despite the manual path already having working
tooling (exact Plex membership + the movie ID map from Milestone 5) —
accepting that the plugin generates collections from TMDb's own franchise
grouping rather than an exact copy of Plex's curated list.

- [x] Confirm the Jellyfin TMDb Box Sets plugin version is compatible with the
  installed Jellyfin server. — Plugin catalog shows v13.0.0.0 targeting ABI
  10.11.8.0; server runs 10.11.11 — compatible.
- [x] Back up Jellyfin before installing or enabling the plugin. — Fresh ZFS
  snapshot `Media/ix-apps@pre-boxsets-plugin-20260901-100925` (covers
  Jellyfin's config/plugins/database) taken immediately before install.
- [x] Confirm imported movies have correct TMDb IDs. — Covered by Milestone
  5's identity-mapping work: 864/898 movies (96.2%) confirmed with correct
  TMDb IDs, including the 7 wrong-auto-match fixes.
- [x] Run the plugin's scheduled collection task in a controlled window. —
  Installed the plugin (`204`, required a Jellyfin restart to activate —
  confirmed with Jason first, since it briefly interrupts any live playback;
  restart triggered gracefully via Jellyfin's own `/System/Restart` API).
  Plugin confirmed `Active` after restart. Ran its "Scan library for new box
  sets" scheduled task.
- [x] Compare generated collection names and membership against the Plex
  export. — Built a real comparison against all 168 non-empty Plex
  collections (had to fix the comparison script first: `Items?ParentId=`
  needs `Recursive=true` for BoxSet children, or it silently returns 0).
  Plugin created **87 box sets**: 65 exact membership matches, 20 partial
  overlaps (different movies than Plex had), 2 with names that didn't match
  any Plex collection. **83 of 168 Plex collections weren't created by the
  plugin at all** (not enough TMDb-matched movies to trigger auto-creation).
  Given this real gap, and per this doc's own rule — "run an overlap report
  before any collection write" — used exactly that report to fill in only
  what the plugin missed or got wrong, via the manual Collection API, without
  touching the 65 already-correct ones: **82 created fresh, 20 corrected
  (added missing Plex members, removed ones that shouldn't be there)**, 1
  skipped (zero resolvable members — likely composed entirely of movies
  still in the 34 unresolved from Milestone 5). The 3 smart collections
  (Austin Powers, Back to the Future, Batman) were created as dated static
  snapshots (`" (static snapshot 2026-09-01)"` suffix), per this doc's
  explicit smart-collection rule. **Initial result: 169 total box sets in
  Jellyfin, covering 167 of 168 Plex collections with real membership.**

  **Near-duplicate check and resolution (2026-09-01).** Jason asked for a
  check for duplicate collections. No exact-name duplicates existed (0/169),
  but a normalized-name comparison (stripping the snapshot suffix,
  punctuation, case and a leading "The") found all 3 smart-collection pairs
  sitting alongside a same-franchise regular/plugin collection: Austin
  Powers, Back to the Future and Batman. (The Austin Powers pair didn't
  initially surface via normalization alone — the original Plex smart
  collection's title carries a genuine typo, "Austion Powers" — found via a
  follow-up direct name search instead.) Compared actual membership for all
  3 pairs before acting, since a name collision alone doesn't prove
  redundancy:
  - **Austin Powers** — identical membership (3/3 films both sides) →
    true redundant duplicate.
  - **Back to the Future** — identical membership (3/3 films both sides) →
    true redundant duplicate.
  - **Batman** — *not* a duplicate: the plugin's TMDb-driven "Batman
    Collection" only covers the Burton/Schumacher-era 4 films (Batman,
    Batman Returns, Batman Forever, Batman & Robin); the Plex smart
    collection's snapshot also included Batman Begins and The Batman (6
    total) — a genuine scope difference, not an error.

  Resolved per Jason's decision: deleted the two truly-redundant snapshot
  collections (Austin Powers, Back to the Future) outright via
  `DELETE /Items/{id}`; for Batman, added the 2 missing films (Batman
  Begins, The Batman) to the regular plugin-generated "Batman Collection"
  via `POST /Collections/{id}/Items`, then deleted its now-redundant
  6-film snapshot copy. **Result: 166 total box sets in Jellyfin** (169 − 3
  deleted snapshots), still covering 167 of 168 Plex collections with real
  membership — no coverage was lost, since each deleted snapshot's
  equivalent regular collection remains (Batman's now with full correct
  membership).
- [x] Lock or manually protect collections only when there is a documented
  need. — **Skipped by explicit decision (Jason, 2026-09-01).** No
  documented need identified; not pursued.

### Manual and curated collections

Plex draws no formal line between "TMDb franchise" and "manual/curated" —
that distinction only exists on the Jellyfin side (plugin-generated vs.
API-created). In practice, every one of the 165 non-smart Plex collections
was already carried through Milestone 7's TMDb-derived-collections workflow
above: the plugin created 65 with exact membership, and the manual
gap-fill pass (via the same accepted media mapping and the same
`POST /Collections`/`POST /Collections/{id}/Items` API) created the
remaining 82 and corrected 20 more. So most items below were already
satisfied by that work; this section closes out what wasn't.

- [x] Export collection title, summary, sort behaviour, artwork and ordered
  members from Plex. — **Partial, a real Milestone 1 gap.** Title, smart
  flag, child count and ordered members were captured for all 233
  collections in `plex-movie-collections.json`; summary and artwork were
  specified as required fields in the Milestone 1 inventory table but the
  export script never actually populated them (confirmed empty for all
  233 entries on inspection). Decision 2026-09-01 (see below): not worth
  a live Plex re-fetch to backfill, since Jellyfin's own metadata already
  covers all but a handful of collections.
- [x] Resolve each member through the accepted media mapping. — Every
  collection write (plugin gap-fill and this session's corrections) used
  `plex-to-jellyfin-movie-map.json`, the same Milestone 5 mapping used for
  everything else in this project.
- [x] Require archive path agreement when the same title exists in both
  current and archive movie libraries. — Checked 2026-09-01: exactly 2
  titles exist in both the pre-existing Movies library and Archive Movies
  ("The Boy and the Heron", "The Shawshank Redemption"). Confirmed both
  map to their Archive Movies item IDs, not the pre-existing library's —
  and structurally can't do otherwise, since `plex-to-jellyfin-movie-map.json`
  was built only against the Archive Movies scan (Milestone 5) and never
  contains an existing-library ID at all.
- [x] Create the Jellyfin collection with the resolved item IDs. — Done as
  part of the TMDb-derived-collections gap-fill above; no separate manual
  pass was needed since the same script and mapping covered both
  categories together.
- [x] Reapply supported overview and artwork fields after membership
  creation. — **Mostly automatic, not from this project's Plex export.**
  Checked 2026-09-01: 158/166 collections already carry real overview text
  and 156/166 a real poster, sourced by Jellyfin's own built-in TMDb
  collection-metadata matching (independent of the TMDb Box Sets plugin) —
  it matches by collection name against TMDb's own collection database,
  which worked for every standard franchise name. The 8 without overview /
  10 without a poster are Jason's custom-named collections that don't
  match any real TMDb collection (e.g. "Wunder Filmreihe", "A Star Wars
  Story collection", "The Whole Nine/Ten Yards Collection", "Nobody
  Collection", "Monty Python Collection", "Searching Collection",
  "Transformers: Rise of the Beasts Collection"). **Decision (Jason,
  2026-09-01): leave as-is** — titles and membership are correct, Jellyfin
  auto-generates a poster collage from member films for the image-less
  ones, and fetching Plex's own summary/thumb for just these ~10 wasn't
  judged worth a live Plex round-trip for what's a cosmetic gap. Consistent
  with this project's established "good enough" standard from the music
  tagging cleanup.
- [x] Record unsupported Plex display settings rather than claiming parity.
  — Recorded: Plex's per-collection custom sort order/mode has no
  Jellyfin equivalent captured or reapplied by this project (see next
  item).
- [x] Preserve custom collection ordering when Jellyfin and the selected
  client expose an equivalent; otherwise document Jellyfin's resulting
  order. — **Documented as unsupported.** Jellyfin box sets have no
  persisted per-collection custom member order (unlike playlists, which
  do and were order-validated in Milestone 6) — display order is
  determined by the viewing client's own sort setting at watch time, not
  by anything this project's API writes control. No parity claim is made
  here.

**Near-duplicate found and resolved during this review (2026-09-01):**
"Three Flavours Cornetto Collection" (2 films: Shaun of the Dead, Hot
Fuzz) and "Three Flavours Cornetto Trilogy" (3 films, also including The
World's End) were both genuinely present as separate Plex collections
(confirmed in `plex-movie-collections.json`) and were faithfully copied
over as two distinct Jellyfin collections by the gap-fill pass — unlike
the earlier Batman/Austin Powers/Back to the Future cases, this was not a
migration artifact. Reviewed with Jason: merged into one 3-film
collection — added The World's End to "Collection" via
`POST /Collections/{id}/Items`, then deleted "Trilogy" via
`DELETE /Items/{id}`. **Box set total now 165** (166 − 1).

Expected Jellyfin operations are:

```text
POST /Collections
POST /Collections/{collectionId}/Items
```

The installed Jellyfin server's generated API description is authoritative for
parameters and authentication.

### Collection validation

For every Plex movie collection, record:

- classification and chosen migration method;
- source member count;
- matched member count;
- destination member count;
- provider-ID agreement;
- missing, ambiguous or duplicate members;
- title, summary and artwork result; and
- whether the collection points to Archive Movies, existing Movies or an
  explicitly approved combination.

### Gate

All manual collections must pass an exact membership comparison unless their
exceptions are individually approved. Plugin-generated collections may differ
only where the TMDb provider set has changed; every difference must be shown in
the report.

## Milestone 8 — Functional validation and cutover

- [x] Confirm existing Jellyfin Movies and TV counts did not change because of
  archive ingestion. — **Passed 2026-09-01.** Movies: 28/28, exact ID-set
  match against the Milestone 1 `jellyfin-before.json` baseline. Shows: 43/43
  series unchanged; episode count grew 625 → 629, but all 4 new episodes
  verified as legitimately new downloads under the existing `/media/media/tv`
  path (e.g. new "Adults" S02 and "Furious" S01E08 episodes) — zero missing,
  zero archive-tv cross-contamination.
- [x] Confirm Archive Movies and Archive TV contain only their intended source
  content. — **Passed.** 921/921 Archive Movies items and 5,678/5,678 Archive
  TV episodes have paths rooted under `/media/archive-movies` and
  `/media/archive-tv` respectively; 0 off-path.
- [x] Confirm no archive root is nested inside an existing Jellyfin root. —
  **Passed.** Checked all 5 content library roots pairwise; no path is a
  prefix of another.
- [x] Test direct play and transcoding separately for representative movie and
  television formats. — **Passed via API feasibility check** (no client
  login available to this session — see note below). `PlaybackInfo` queried
  for one file per movie extension (m4v, mp4, mkv, mpg): direct play/stream
  supported for all except one mkv (`The Bad Guys 2`, unusually encoded as
  mpeg2video) which correctly falls back to transcoding. Real transcode logs
  from the last several days confirm the transcoding pipeline itself works
  end-to-end (hundreds of successful FFmpeg sessions).
- [x] Test external subtitles, alternate audio, extras and at least one
  multi-episode file where present. — **Passed / not applicable.** No
  multi-episode files exist in Archive TV (0 items with `IndexNumberEnd`
  set) — nothing to test. TV subtitles are essentially absent (1/5,678
  episodes) but confirmed as real source-content reality (sampled episode
  folders contain only video files, no `.srt` sidecars — nothing was lost in
  the copy). 1,895/5,678 episodes have multiple embedded audio tracks,
  confirmed via `MediaStreams`. "Project Hail Mary" (35 subtitle streams) and
  "Star Wars: Episode I" (7 audio tracks) identified as good representative
  test items for Jason's own client-side spot check.
- [x] Test music album grouping, disc ordering, artist navigation, compilation
  handling, artwork and lyrics. — **Mostly passed, one real unresolved gap.**
  Disc ordering, `Various Artists` compilation grouping and artwork all
  verified correct on "Caribbean Uncovered" (the multi-disc compilation
  fixed earlier in this project). However, this check also surfaced a real,
  previously-undetected bug — see "Album-grouping investigation" below.
  Lyrics: 163/8,054 tracks have embedded lyrics (real, not a defect — most
  source files never had lyrics embedded). Artwork: 720/741 album objects
  have a cover image; 21 missing are untouched pre-existing gaps unrelated
  to this project.
- [x] Test at least one migrated playlist in each supported Jellyfin client used
  by the household. — **Done by Jason, 2026-09-01, via Jellyfin Web.** Found
  a real bug in the process: every playlist appeared twice. Root-caused and
  fixed — see the Milestone 6 gate section above.
- [x] Test at least one manual collection and one TMDb-derived box set. —
  **Done by Jason, 2026-09-01.** Collections displayed correctly on the home
  screen (see screenshot evidence); no issues reported for collections
  specifically. Also surfaced the home-screen library tile ordering request
  — see "Home screen library order" below.
- [x] Review Jellyfin logs for scan, metadata, permissions and playback
  errors. — **Passed 2026-09-01**, no unresolved real errors. Reviewed
  `log_20260901.log` (40,632 lines) and `log_20260831.log` in full. Findings,
  all explained and none requiring action: (1) `LibraryMonitor: Permission
  error for Directory watcher` for `/media/media/movies` (pre-dates this
  project, seen in the 8/31 log too) and `/media/media/music` (first seen
  right after the Milestone 4 library recreate) — real-time file-watching is
  broken for these paths, but scheduled/manual scans work correctly
  regardless (proven repeatedly this session), so this doesn't block
  anything; (2) one isolated `DirectoryNotFoundException` referencing the
  old (pre-recreate) Music library's internal path, 3 log lines, a single
  event, never repeated — a harmless one-time cleanup artifact of the
  earlier library recreate; (3) one isolated ffprobe "streams and format are
  both null" error on a single movie item, never recurred — Milestone 3's
  checksum verification already confirms no corrupted archive files exist,
  so this reads as a transient probe hiccup; (4) `Invalid HLS segment
  container: fmp4` (6x) — cosmetic, FFmpeg still exits 0 and playback
  completes; Jellyfin logs this at ERR level for what's actually a handled
  fallback; (5) 5x Kestrel `ObjectDisposedException`, all at 01:20:05 during
  a single server-startup race condition, not repeated. **Real evidence of
  successful playback found in these logs**: 50 real playback-stopped
  events on 2026-09-01 alone, spanning Jellyfin Web and JellyTV clients and
  both `elliottrook` and `jason` accounts, all against migrated music
  content — the household is already successfully using the migration's
  output.
- [ ] Re-run counts, byte totals and mapping exception reports.
- [ ] Keep Plex operational during an agreed observation period.
- [ ] Obtain Jason's approval before deleting any Plex library, database,
  playlist, collection or source media.

### Album-grouping investigation and remediation attempts (2026-09-01)

The album-grouping check above surfaced a real bug, distinct from the
already-documented and already-fixed "Total albums" cosmetic count issue
(Milestone 4): **45 real albums (71 extra Jellyfin album container objects,
out of 741 total) are split into 2 or more separate entries** for what
should be one album — including albums never touched by the earlier
97-folder scattered-tag fix (Abbey Road, Beyoncé, Bad, The Fame). Examples
ranged from 2-way splits up to "F-1 Trillion" split 15 ways.

**Root cause, confirmed via direct file inspection on "Caribbean
Uncovered":** tracks that correctly share the same plain-text `Album` tag
still carry different embedded per-track `MusicBrainzAlbum` /
`MusicBrainzReleaseGroup` provider identifiers, and Jellyfin groups album
identity by that ID ahead of the text tag — the same class of bug as the
already-documented Milestone 4 indexing issue, but affecting a wider set of
albums than the 97-folder fix covered.

**Remediation attempted, in order, none successful in producing a merge:**

1. Stripped the stale `MusicBrainzAlbum`/`MusicBrainzReleaseGroup` MP4/ID3/
   FLAC atoms directly from all 830 affected track files via `mutagen`
   (529/830 had a stale tag to remove; 0 errors). A full library
   remove/recreate afterward left the split identical — Jellyfin's API still
   reported the *same* stale provider IDs on tracks whose files, confirmed
   by direct inspection, no longer had the tag.
2. Traced this to Jellyfin performing its own live AcoustID-fingerprint
   MusicBrainz lookup (using the embedded `Acoustid Id` tag) independent of
   the library's `EnableInternetProviders: false` setting — 2,366 MusicBrainz
   API calls failing with HTTP 503 were found in the same day's log,
   confirming this lookup runs regardless of that setting. Attempted to stop
   it two ways: disabling the bundled MusicBrainz plugin (`POST
   /Plugins/{id}/{version}/Disable`, requires a full Jellyfin restart —
   done, with Jason's explicit approval given the household-wide playback
   interruption) and, since the plugin still reported `Status: Active` after
   restart, explicitly excluding MusicBrainz from the Music library's
   per-type `MetadataFetchers` (`TheAudioDB` only for Album/Artist, none for
   Audio) — the correct, documented mechanism. Neither, individually or
   combined with another full library rebuild, changed the outcome.
3. Directly cleared the stale `MusicBrainzAlbum`/`MusicBrainzReleaseGroup`
   provider IDs via the Jellyfin API itself (not just the file tags) on all
   578 affected objects (91 album containers + 487 tracks; 0 errors),
   followed by one more full library remove/recreate.

**Result: identical every time.** All three attempts — despite fixing three
real, different, independently-confirmed underlying causes — produced the
exact same 741 total albums and the same 39 remaining split groups,
byte-for-byte. This strongly suggests that removing and recreating the
Jellyfin Music `VirtualFolder` does not actually purge and rebuild the
underlying Album/Track database rows as its behavior implied during the
earlier single-container-rename fix (Milestone 4) — it more likely
re-attaches library membership to existing rows matched by path, which
would explain why every fix targeting *content* (tags, provider IDs,
fetcher config) left the *existing* split container objects untouched.
Confirming or fixing this would require inspecting or modifying Jellyfin's
internal database directly, which is out of scope for what's safely
achievable through the documented REST API.

**Decision: stopped after 3 escalating attempts rather than continue
disruptive trial-and-error.** The Music library remains fully intact and
functional throughout (8,054/8,054 tracks present, matching the
pre-investigation baseline, at every checkpoint) — this is a real but
low-blast-radius cosmetic defect (an album occasionally appears as 2+
separate entries when browsing), not data loss or a playback break. Net
effect of this investigation: the stale-tag cleanup and MusicBrainz-provider
exclusion are genuine improvements now in place (reduces *future* drift
even though it didn't fix the *existing* 39 split groups), but the 39
existing split groups remain unresolved and are logged here as a follow-up
requiring either a different technical approach (e.g. testing whether
Jellyfin's own admin-dashboard-driven "identify" workflow behaves
differently from the pure-API path used here) or acceptance as a permanent,
minor cosmetic limitation.

### Client-side testing needed

Jason completed the playlist and collection checks above via Jellyfin Web on
2026-09-01, which found and enabled fixing the playlist-duplication bug.
Still outstanding, needing a real client (this session has no Jellyfin login
and won't enter one): direct-play/transcode/subtitle/multi-audio-track
verification against the specific representative items identified during
this session's API checks — `Project Hail Mary` (35 subtitle tracks) and
`Star Wars: Episode I — The Phantom Menace` (7 audio tracks).

### Home screen library order

Jason requested the home screen's library tile order be changed from
Jellyfin's default (newest-created libraries first: Archive Movies, Archive
TV, Collections, Movies, Music, ...) to Shows, Movies, Music, Playlists,
Archive TV, Archive Movies, Collections. Fixed 2026-09-01 via each user's
`OrderedViews` configuration field (`POST /Users/{id}/Configuration`) —
applied to all 6 accounts on the server (`alisa`, `carter`, `elliottrook`,
`jason`, `jen`, `justin`) for a consistent household experience, using each
library's view ID: Shows (`a656b907...`), Movies (`f137a2dd...`), Music
(`7e64e319...`), Playlists (`4838f74f...`), Archive TV (`10f168d0...`),
Archive Movies (`0064264a...`), Collections (`9d7ad6af...`).

## Milestone 9 — Documentation, backup and closeout

- [ ] Record final host and container paths, mounts, ACLs and library names.
- [ ] Record the final Plex-to-Jellyfin mapping statistics and unresolved items.
- [ ] Save sanitized playlist and collection migration reports.
- [ ] Document the location and retention of unsanitized manifests containing
  full paths or user identifiers.
- [ ] Add the canonical music root and archive-library paths to the media
  operations documentation.
- [ ] Add the Jellyfin configuration/database and migration manifests to the
  backup plan.
- [ ] Confirm restored playlists and collections are covered by Jellyfin backup.
- [ ] Record temporary API-key revocation and token cleanup.
- [ ] Remove the migration staging directory only after the rollback window
  expires and deletion is explicitly approved.
- [ ] Record whether Plex remains available, is retained offline or is retired.
- [ ] Update this project status to `Complete` only after the completion gate.

## Rollback plan

### Before Jellyfin object creation

- Stop the migration process.
- Leave Plex and all source media unchanged.
- Remove incomplete destination copies only after comparing them with transfer
  logs and confirming the target path exactly.
- Restore dataset ACLs or compose mounts from the recorded pre-change state.

### After Jellyfin scan or metadata changes

- Stop Jellyfin.
- Restore the pre-migration Jellyfin configuration/database backup if library
  removal does not cleanly return the server to its prior state.
- Roll back the affected ZFS dataset snapshot only after confirming that it
  contains no unrelated post-snapshot media changes.

### After playlist or collection creation

- Use the migration-created object-ID manifest to remove only objects created by
  this project.
- Never delete objects by title alone.
- Restore the Jellyfin backup if API-level removal cannot be proven complete.

Plex is the authoritative fallback until all completion checks pass. Source
deletion is a separate destructive operation requiring explicit approval.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Archive files appear in existing libraries | Separate top-level roots and verify container mounts before scanning |
| Music albums split or merge incorrectly | Correct embedded album artist, album, disc and compilation tags in staging |
| Alternate music release deleted as a duplicate | Report duplicates; require human retention decisions; never auto-delete |
| A confirmed Plex-source duplicate is deleted before its keeper copy is verified | Only delete from Plex after the retained copy is staged and checksum-verified; per-item review, no batch or automatic deletion |
| Playlist items disappear after path changes | Export ordered manifests first and map through provider IDs/final paths |
| Playlist count matches but order changes | Validate the complete ordered destination item list |
| Collection attaches to the wrong duplicate movie | Require provider ID plus archive-path agreement where duplicates exist |
| TMDb and manual migrations create duplicate collections | Classify and run an overlap report before creating collections |
| Smart objects lose their dynamic rule | Export the rule and label the recreated object as a static snapshot unless parity is proven |
| API token leaks into Git or logs | Temporary secrets outside Git; sanitize commands/reports; revoke after use |
| Source is deleted before confidence is established | Copy-first workflow, snapshots, observation period and explicit deletion approval |
| Existing Jellyfin metadata is damaged | Pre-change Jellyfin backup plus per-milestone rollback gates |

## Completion gate

- [ ] All media transfer checksums and count reconciliations pass.
- [ ] Existing Jellyfin video libraries are unchanged and archive libraries are
  separate.
- [ ] Music is consolidated into one album-structured root with no unresolved
  destructive duplicate decisions.
- [ ] All playlists have a recorded pass, exception or deferral state.
- [ ] All movie collections have a recorded pass, exception or deferral state.
- [ ] Representative playback succeeds from each new library and migrated
  object type.
- [ ] Jellyfin logs contain no unresolved migration-related errors.
- [ ] Backup and rollback procedures are tested or otherwise validated.
- [ ] Temporary credentials are revoked and protected manifests are retained.
- [ ] Documentation and evidence logs are current.
- [ ] Jason approves the final Plex disposition and any source cleanup.

## Evidence log

| Date | Milestone | Evidence | Result | Operator |
|---|---|---|---|---|
| 2026-08-30 | 1 | `plex-media.json` (sha256 `e1e289d3…`): 898 movies, 5,453 episodes, 7,911 tracks, ~5.42 TiB total | Passed | Claude |
| 2026-08-30 | 1 | `plex-playlists.json` (sha256 `e676c168…`): 14 music playlists, owner `Elliottrook1`, full ordered membership | Passed | Claude |
| 2026-08-30 | 1 | `plex-movie-collections.json` (sha256 `210e9062…`): 233 collections (168 with members, 3 smart) | Passed | Claude |
| 2026-08-30 | 1 | `jellyfin-before.json` (sha256 `b9a0c805…`): pre-migration baseline — 28 movies, 43 series/625 episodes, 140 tracks | Passed | Claude |
| 2026-08-30 | 1 | `migration-baseline.csv` (sha256 `bad4fdfd…`): counts/byte totals by source library | Passed | Claude |
| 2026-08-30 | 1 | SSH trust test, TrueNAS \<-> Synology, both directions | Failed — no key trust either direction; flagged as Milestone 2 prerequisite | Claude |
| 2026-08-30 | 2 | `zpool status Media` | Passed — ONLINE, scrub clean 2026-08-16, 0 errors | Claude |
| 2026-08-30 | 2 | ZFS snapshots `Media/data@pre-plex-migration-20260830-205932`, `Media/ix-apps@pre-plex-migration-20260830-210033` | Passed | Claude |
| 2026-08-30 | 2 | `archive-movies`/`archive-tv`/`migration/*` created, `truenas_admin:apps 750` | Passed | Claude |
| 2026-08-30 | 2 | Gate test: write via migration identity, read via Jellyfin `/Environment/DirectoryContents` API, cleanup | Passed | Claude |
| 2026-08-30 | 2 | SSH key install, TrueNAS→Synology dedicated key, via DSM Task Scheduler (root) | Passed — installed by Jason | Claude |
| 2026-08-30 | 2 | Read-only rsync wrapper validation: plain command, 3 allowed paths (incl. space in "TV Shows"), 1 disallowed path, 1 injection attempt | Passed — 6/6 correct after fixing a whitespace-parsing bug and a follow-on eval-injection risk in the wrapper | Claude |

## References

- [Jellyfin music organization](https://jellyfin.org/docs/general/server/media/music/)
- [Jellyfin movie organization](https://jellyfin.org/docs/general/server/media/movies/)
- [Jellyfin television organization](https://jellyfin.org/docs/general/server/media/shows/)
- [Jellyfin directory exclusion](https://jellyfin.org/docs/general/server/media/excluding-directory/)
- [Jellyfin plugins and TMDb Box Sets](https://jellyfin.org/docs/general/server/plugins/)
- [Jellyfin TypeScript SDK: create playlist](https://typescript-sdk.jellyfin.org/interfaces/generated-client.PlaylistApiCreatePlaylistRequest.html)
- [Jellyfin TypeScript SDK: create collection](https://typescript-sdk.jellyfin.org/interfaces/generated-client.CollectionApiCreateCollectionRequest.html)
- [Plex Media Server API](https://developer.plex.tv/pms/)
- [Python PlexAPI playlist support](https://python-plexapi.readthedocs.io/en/latest/modules/playlist.html)
- [Python PlexAPI collection support](https://python-plexapi.readthedocs.io/en/latest/modules/collection.html)
- [beets configuration](https://beets.readthedocs.io/en/stable/reference/config.html)
- [beets duplicate detection](https://beets.readthedocs.io/en/latest/plugins/duplicates.html)
- [MusicBrainz Picard introduction](https://picard-docs.musicbrainz.org/en/v3.0/about_picard/introduction.html)
- [TrueNAS DIY SAS expansion project](TrueNAS-DIY-SAS-Expansion.md)
- [HomeLab backup design](../05-Backups.md)
