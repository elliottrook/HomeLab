# ARR Stack Operational Reference

> Authority: current-with-exclusions
> Reviewed: 2026-10-08
> Review owner: HomeLab operations

This page is the current operational reference for Aster's ARR curriculum. It
records service roles, stable dependencies, storage and network boundaries,
and every known unattended workflow that can acquire, import, rename, move or
remove media. It deliberately contains no credential, media title, download
history, queue identity, raw error, user-library item or raw service response.

## Evidence and precedence

The 2026-09-09 review used, in descending order of present-state authority:

1. secret-free live container state and installed package metadata from
   TrueNAS for versions, running state, bound ports and the shared-data mount;
2. Aster's schema-validated aggregate report generated at
   `2026-09-09T20:40:01Z` for a point-in-time health/queue snapshot;
3. TrueNAS middleware metadata for enabled Cron Jobs 2–5;
4. `docs/04-Operations.md`, `docs/reference/Aster-Operations.md`, and the relevant
   project decision records for canonical roots, relationships and tested
   behavior.

The live sanitized report outranks this page for current health. This page
outranks historical activity notes for stable topology and responsibility. A
conflict is reported as drift; Aster must not silently select whichever value
is more convenient.

## Current service inventory

All six services run as Docker containers on TrueNAS at `192.168.20.40`.
Their listeners are host-published on both IPv4 and IPv6; OPNsense remains the
inter-VLAN policy boundary. The containers use the shared host tree
`/mnt/Media/data` for media workflow data. Configuration volumes and exact
credentials are outside this reference.

| Service | Installed version | Host port | Role | Canonical library root / handoff | Downloader relationship |
|---|---:|---:|---|---|---|
| Sonarr | 4.0.20.3014 (`ls326`) | 8989 | TV monitoring, search, completed-download import, naming and library management | `/mnt/Media/data/media/tv` | Receives indexer configuration through Prowlarr and imports completed SABnzbd TV downloads |
| Radarr | 6.4.4.10685 (`ls318`) | 7878 | Movie monitoring, search, completed-download import, naming and library management | `/mnt/Media/data/media/movies` | Receives indexer configuration through Prowlarr and imports completed SABnzbd movie downloads |
| Lidarr | 3.1.0.4875 (`ls39`) | 8686 | Album-oriented music monitoring, acquisition, import, metadata and naming | `/mnt/Media/data/media/music` | Uses the shared Prowlarr/SABnzbd acquisition path; requests and imports are album-scoped |
| Prowlarr | 2.6.5.5623 (`ls162`) | 9696 | Indexer authority and application synchronization | No media-library root | Synchronizes indexer definitions to connected ARR applications; it is upstream of search/grab, not the downloader |
| SABnzbd | 5.1.3 | 8080 | Download queue, unpack/post-processing and handoff | No canonical library root; working data remains under the shared dataset | Downloads for the ARR applications; completion is not proof that an ARR import succeeded |
| Jellyfin | 12.1.0 (live check 2026-09-26) | 8096 | Downstream library scan, metadata match and playback visibility | Movies, Shows and Music roots above, plus `/mnt/Media/data/archive-movies` and `/mnt/Media/data/archive-tv` | No downloader authority; observes files only after ARR import or an explicitly managed side workflow |
| Bazarr | 1.6.2-ls366 | 6767 | Regular English and forced-English subtitle sidecar automation | Reads the shared `/mnt/Media/data` tree; writes additive subtitle sidecars | Receives Sonarr/Radarr import events; scheduled missing-subtitle and upgrade searches are disabled to protect provider quotas |

The diagnostic dependency order is:

`request/monitor → Prowlarr indexer sync/search → SABnzbd download → ARR import/rename → Jellyfin scan/match`

A successful state at one boundary never proves success at the next. Diagnose
the first failing boundary before proposing a repair.

## Point-in-time health snapshot

The sanitized report generated at `2026-09-09T20:40:01Z` recorded:

| Service | Status | Declared coverage | Aggregate queue state |
|---|---|---|---|
| Sonarr | healthy | health, queue | 0 pending; 0 warning/error records |
| Radarr | warning | health, queue | 1 pending; 1 warning/error record |
| Lidarr | warning | health, queue | 4 pending; 4 warning/error records |
| Prowlarr | healthy | health only | queue/import unknown |
| SABnzbd | healthy | health, queue | 0 pending; 0 failed/error records |
| Jellyfin | healthy | health only | queue/import not applicable or unknown |

This table is evidence of one report, not a durable assertion. Aster must use
the latest fresh validated report for words such as “currently” or “now.” It
must not infer titles, causes or import state from these aggregate counts.

## Automation and mutation map

### Enabled host workflows

| Authority | Schedule | Capability and boundary |
|---|---|---|
| TrueNAS Cron Job 2 — `jellyfin-integrity` | Wednesday 03:00 | Forces Jellyfin scans; may folder orphaned tracks, consolidate only unambiguous scatter, extract artwork and gap-fill missing tracks within its action cap. It never automatically deletes duplicate albums. |
| TrueNAS Cron Job 3 — `playlist-bridge` | Every six hours at minute 15 | May add/search album-scoped Lidarr requests for missing exported-playlist tracks and create or replace the bounded Jellyfin playlist only after reconciliation. It does not download media itself. |
| TrueNAS Cron Job 4 — `video-archiver` | Monday–Saturday 01:30 | May transcode eligible aged video, place the archive copy, use Radarr/Sonarr's authoritative delete-file API for the replaced source and unmonitor the parent to prevent reacquisition. Candidate age and per-run caps bound it. |
| TrueNAS Cron Job 5 — Aster ARR report | Every five minutes | Read-only. Produces and transports only aggregate health/queue/import fields plus at most one separately issued opaque repair candidate. It cannot create an approval or execute a repair. |

### Built-in and event-driven behavior

- Prowlarr application synchronization can change indexer definitions in its
  connected ARR applications. A stale connected-app key can therefore break
  both synchronization and downstream indexer health.
- Sonarr, Radarr and Lidarr can monitor items, evaluate RSS/search results,
  hand selected releases to SABnzbd, process completed downloads and apply
  their configured naming on import. Per-title monitoring state, release
  history and exact live scheduler settings are deliberately excluded.
- Lidarr's `Rename Tracks` and artwork metadata consumer are enabled for future
  imports; that does not authorize an unattended bulk rename of existing
  files.
- SABnzbd owns download, unpack and category handoff. Its completion status
  does not authorize Aster to mark the corresponding ARR import successful.
- The active and archive video roots remain separate. Archive directories and
  files use the `apps` service group with group traversal/write permission so
  Radarr/Sonarr can replace an archived copy when the existing archive workflow
  deliberately hands an upgrade back through the ARR importer. This is a
  permission policy only; it does not authorize a new archive mover or deletion
  workflow.
- Watchtower remains always running on its existing schedule, but only
  explicitly labelled services are eligible for unattended image updates.
  Critical ARR, downloader, request and custom media services are not included
  in that automatic update set.
- Jellyfin runs native library and metadata maintenance. Its destructive
  “Clean up collections and playlists” trigger remains disabled and is checked
  for drift by `jellyfin-integrity`.

### Explicitly not unattended

- The media sideload inbox has no scheduled importer. Manual/Interactive Import
  remains the reviewed path until its separate project proves automation is
  needed.
- Aster's ARR execution broker is stopped and boot-disabled. Candidate issue,
  independent review, the two-minute operator approval and the temporary
  Aster-to-broker network path are separate manual gates. Natural-language
  chat cannot execute the repair.
- No general-purpose Aster or Hermes ARR administrator exists. Search, grab,
  monitor, rename, profile, indexer, downloader and additional delete actions
  require their own decisions and graduation gates.

## Known exclusions

The review intentionally excludes API keys and their values, downloader
credentials, config-volume paths, media titles, artist/album/movie/show names,
queue identifiers, release names, download history, user/watch data, raw
health messages and raw API/configuration payloads. The sanitized report now
claims only aggregate import-pending and import-error counts for Sonarr,
Radarr and Lidarr; it still does not claim title-level import details.

Root paths are included because they are approved operational boundaries, not
library contents. Current Sonarr/Radarr rename switches, the exact connected
Prowlarr application list, per-item monitoring state and detailed SABnzbd
category/post-processing settings were not independently exported during this
review. Treat them as unknown until a future purpose-built sanitized field is
reviewed and added; do not fill them from stale config directories.

## Historical lessons, not current-state substitutes

- The old `/mnt/Media/configs/<app>/` trees are disconnected remnants. Never
  use them for current credentials or settings.
- The 2026-09-02 key-rotation outage proves Prowlarr application sync and
  downstream indexer health are coupled, but it does not mean they are
  currently unhealthy.
- Prior import, rename, orphan, artwork and migration incidents explain the
  safeguards above. Their titles, counts and one-time corrective commands are
historical evidence, not instructions for a current incident.

## Reliability hardening — 2026-10-08

The live Stream A upgrade found and corrected inconsistent group ownership and
write permissions under `/mnt/Media/data/archive-tv` and
`/mnt/Media/data/archive-movies`. Disposable write/remove tests passed from the
Radarr and Sonarr containers, and no media was changed. Existing Radarr and
Lidarr warning queue records were retained for normal operator review rather
than being automatically retried or dismissed.

Sonarr, Radarr and Prowlarr now reject unapproved Host headers while accepting
their documented private HTTPS hostname and direct TrueNAS recovery address.
Lidarr's deployed configuration does not expose the same Allowed Hosts setting;
it retains the existing Authentik/private-network boundary.

The sanitized ARR report now includes aggregate import-pending and import-error
counters for Sonarr, Radarr and Lidarr. It still excludes titles, paths,
release names, queue IDs, API keys and raw responses. The first post-change
report was generated at `2026-10-08T23:52:57Z` and delivered through the
existing forced-command transport.

## Configuration recovery — 2026-09-26

Actual ARR `/config` Docker volumes, Jellyfin state and the NAS deployment
definitions now have a verified daily media-free export into the TrueNAS
backup hub. The image and library paths were not changed by this backup work.
See `docs/runbooks/Configuration-Backups.md`; bulk media is excluded.
