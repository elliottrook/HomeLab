# Plex-to-Jellyfin Media Migration Project

> Status: Ready
>
> Project owner: Jason
>
> Last updated: 2026-08-28

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
- [ ] Record the Plex server address, version, host and library names.
- [ ] Record the Plex media source device, dataset/share and exact paths.
- [ ] Record the installed Jellyfin version, container name, internal media
  mount and exact current Movies, TV and Music paths.
- [ ] Record current media counts, byte totals, filesystem types and free space
  at both source and destination.
- [ ] Record every Plex account whose playlists are in scope.
- [ ] Export an inventory of Plex playlists and movie collections before moving
  any media.

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

- [ ] Record Plex and Jellyfin versions and take screenshots of the current
  library lists.
- [ ] Record all host paths, container paths, mounts, datasets, share protocols
  and filesystem ownership.
- [ ] Record library-level media counts and storage byte totals.
- [ ] Record the source-to-destination network path and expected throughput.
- [ ] Confirm that the copy runs directly between the source storage and
  TrueNAS rather than relaying media through a Mac.
- [ ] Confirm destination free space for the archive copy, music staging area,
  temporary reports and snapshot retention.
- [ ] Export the Plex library inventory with rating key, media type, title,
  year, edition, source path, size and provider GUIDs.
- [ ] Export every in-scope Plex playlist before paths change.
- [ ] Export every Plex movie collection before paths change.
- [ ] Record which playlists belong to which Plex account.
- [ ] Identify regular and smart playlists separately.
- [ ] Identify manual, metadata-derived and smart movie collections separately.
- [ ] Store exported manifests in the protected migration workspace and record
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

## Milestone 2 — Recovery and destination preparation

- [ ] Verify the most recent TrueNAS pool scrub and SMART status.
- [ ] Take and record ZFS snapshots of affected destination datasets.
- [ ] Back up and validate the current Jellyfin configuration/database.
- [ ] Confirm the Plex server and source media remain backed up or otherwise
  recoverable throughout the project.
- [ ] Create `archive-movies`, `archive-tv` and the temporary migration
  directories in the approved dataset.
- [ ] Apply dataset ACLs that allow the migration process to write and Jellyfin
  UID/GID `568` to read.
- [ ] Keep Jellyfin read-only against archive media unless an approved feature
  specifically requires write access.
- [ ] Ensure the migration staging directory is outside all active Jellyfin
  library roots; use a Jellyfin `.ignore` file as an additional safeguard if a
  temporary directory must exist below a scanned parent.
- [ ] Record available space after snapshot and directory creation.

### Gate

Create and remove a test file through the migration identity, then confirm that
Jellyfin can read—but need not modify—the corresponding destination test file.

## Milestone 3 — Archive video copy

- [ ] Run an `rsync` dry run for Plex movies into `archive-movies`.
- [ ] Review excludes. Exclude caches and operating-system debris, not subtitle,
  NFO, artwork or extras files that may be useful to Jellyfin.
- [ ] Copy movies with partial-transfer protection and logging enabled.
- [ ] Run the same process for Plex television into `archive-tv`.
- [ ] Preserve the relative directory structure during the first copy.
- [ ] Perform a no-change `rsync` comparison after each copy.
- [ ] Produce a checksum manifest or checksum verification report for the final
  source and destination trees.
- [ ] Compare file counts, byte totals and extensions by library.
- [ ] Quarantine zero-byte, unreadable and unsupported files for review; do not
  delete them automatically.
- [ ] Record any naming collisions, duplicate editions and incomplete shows.

### Transfer template

Substitute verified absolute paths; do not execute placeholders literally.
Preserve media content and timestamps while allowing the destination dataset's
ACL model to control ownership.

```bash
rsync -aH --no-owner --no-group --protect-args \
  --partial --info=progress2 --dry-run \
  SOURCE_PATH/ DESTINATION_PATH/
```

After reviewing the dry run, repeat without `--dry-run`. Use an explicitly
logged checksum verification pass after the bulk transfer. A checksum pass is
slower than the initial size/time comparison and should be scheduled
accordingly.

### Gate

Archive video is complete only when copy logs are clean, counts and totals are
reconciled, checksum verification passes and the Plex source remains intact.

## Milestone 4 — Music staging, normalization and merge

- [ ] Copy Plex music into `/mnt/Media/data/migration/plex-music`; do not point
  Jellyfin at this folder.
- [ ] Inventory formats, bitrates, sample rates, bit depth, embedded artwork,
  lyrics and current tags.
- [ ] Catalogue the existing Jellyfin music and staged Plex music separately.
- [ ] Run beets with move and delete disabled and tag writing disabled for the
  first audit.
- [ ] Produce album-level and track-level duplicate reports.
- [ ] Distinguish exact duplicate files from alternate releases, masters,
  formats and legitimately repeated tracks.
- [ ] Define the retention choice for every collision; do not automatically
  prefer one file merely because its bitrate is larger.
- [ ] Use MusicBrainz Picard in reviewed batches for ambiguous or poorly tagged
  albums.
- [ ] Ensure each album has album artist, album, track title, track number and
  disc number metadata where applicable.
- [ ] Correct compilation metadata so various-artist albums remain one album.
- [ ] Preserve useful genres and custom tags unless their removal is explicitly
  approved.
- [ ] Retain sidecar artwork and lyrics with their album/tracks.
- [ ] Preview the final canonical paths and review collisions before enabling
  organizer writes.
- [ ] Copy approved albums into the live `music` root; do not move the only
  source copy.
- [ ] Re-run duplicate and missing-track reports against the combined root.
- [ ] Reconcile track, album and byte totals.

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
remaining collection.

## Milestone 5 — Jellyfin libraries and identity mapping

- [ ] Add read-only container mounts for `archive-movies` and `archive-tv`.
- [ ] Confirm the existing Movies, TV and Music mounts remain unchanged.
- [ ] Create the `Archive Movies` library using the Movies content type.
- [ ] Create the `Archive TV` library using the Shows content type.
- [ ] Scan the combined Music library only after its merge gate passes.
- [ ] Run library scans and allow metadata tasks to finish before object
  migration begins.
- [ ] Export a post-scan Jellyfin inventory containing item ID, library, path,
  provider IDs and media-specific metadata.
- [ ] Build `plex-to-jellyfin-map.json` and a CSV exception report.
- [ ] Require each mapping to record its match method and confidence.
- [ ] Manually resolve ambiguous items and any case where both current and
  archive libraries contain the same title.
- [ ] For archive video, prefer the destination path derived from the original
  Plex path so a collection is not accidentally attached to an existing
  Jellyfin duplicate.

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

- [ ] Transfer regular playlists as ordered snapshots.
- [ ] For a Plex smart playlist, export both its rule description and current
  ordered membership.
- [ ] Do not claim that a smart rule was migrated unless an equivalent Jellyfin
  rule has been separately designed and tested.
- [ ] By default, recreate a smart playlist as a dated static snapshot and mark
  the original rule in the migration report.
- [ ] Resolve every playlist member through `plex-to-jellyfin-map.json` after
  the final Jellyfin scan.
- [ ] Create the playlist for the intended Jellyfin user through the Jellyfin
  playlist API.
- [ ] Add items in their exported order.
- [ ] Preserve duplicate occurrences when Jellyfin supports them; otherwise
  record each collapsed duplicate explicitly.
- [ ] Reapply supported name, overview and artwork fields.
- [ ] Record missing or ambiguous members instead of silently omitting them.
- [ ] Repeat the transfer independently for each in-scope user.

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

### Gate

Every playlist is either `passed`, `passed-with-documented-exceptions` or
`deferred`. A destination playlist whose count matches but order differs does
not pass.

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

- [ ] Confirm the Jellyfin TMDb Box Sets plugin version is compatible with the
  installed Jellyfin server.
- [ ] Back up Jellyfin before installing or enabling the plugin.
- [ ] Confirm imported movies have correct TMDb IDs.
- [ ] Run the plugin's scheduled collection task in a controlled window.
- [ ] Compare generated collection names and membership against the Plex export.
- [ ] Lock or manually protect collections only when there is a documented need.

### Manual and curated collections

- [ ] Export collection title, summary, sort behaviour, artwork and ordered
  members from Plex.
- [ ] Resolve each member through the accepted media mapping.
- [ ] Require archive path agreement when the same title exists in both current
  and archive movie libraries.
- [ ] Create the Jellyfin collection with the resolved item IDs.
- [ ] Reapply supported overview and artwork fields after membership creation.
- [ ] Record unsupported Plex display settings rather than claiming parity.
- [ ] Preserve custom collection ordering when Jellyfin and the selected client
  expose an equivalent; otherwise document Jellyfin's resulting order.

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

- [ ] Confirm existing Jellyfin Movies and TV counts did not change because of
  archive ingestion.
- [ ] Confirm Archive Movies and Archive TV contain only their intended source
  content.
- [ ] Confirm no archive root is nested inside an existing Jellyfin root.
- [ ] Test direct play and transcoding separately for representative movie and
  television formats.
- [ ] Test external subtitles, alternate audio, extras and at least one
  multi-episode file where present.
- [ ] Test music album grouping, disc ordering, artist navigation, compilation
  handling, artwork and lyrics.
- [ ] Test at least one migrated playlist in each supported Jellyfin client used
  by the household.
- [ ] Test at least one manual collection and one TMDb-derived box set.
- [ ] Review Jellyfin logs for scan, metadata, permissions and playback errors.
- [ ] Re-run counts, byte totals and mapping exception reports.
- [ ] Keep Plex operational during an agreed observation period.
- [ ] Obtain Jason's approval before deleting any Plex library, database,
  playlist, collection or source media.

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
| _Pending_ | 1 | Plex/Jellyfin inventory and object exports | Pending | _TBD_ |

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
