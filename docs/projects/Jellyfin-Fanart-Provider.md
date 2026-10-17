# Jellyfin Fanart provider

> Status: completed and validated  
> Owner: Jason  
> Stream: A — autonomous  
> Approved: 2026-10-17  
> Service: existing production Jellyfin 12.1.0  
> Target: TrueNAS `192.168.20.40`, `/mnt/Media/appdata/jellyfin`  
> Rollback: pre-install ZFS snapshot plus removal of only the Fanart provider

## Purpose and desired outcome

Add the official Jellyfin Fanart image provider as a lower-priority supplement
to the existing TMDb, OMDb and AudioDB providers. New or deliberately refreshed
items may use additional posters, backdrops, logos and artist/album artwork from
fanart.tv. Existing selected artwork must not be bulk-replaced by this project.

## Current state and evidence

- Jellyfin 12.1.0 is healthy and uses `/mnt/Media/appdata/jellyfin` as `/config`.
- Existing external plugins are Community SSO, Intro Skipper, LrcLib Lyrics,
  Open Subtitles, TMDb Box Sets and Trakt.
- Movies and shows currently use TMDb and OMDb image providers; music uses
  AudioDB and embedded images.
- Official Fanart 15.0.0.0 targets server ABI 12.0.0.0. The downloaded package
  matches the official MD5 `bbe8ea54bc956933b238388b0a78b9ce` and contains
  only `meta.json` and `Jellyfin.Plugin.Fanart.dll`.

## Scope, exclusions and authority

Authorized changes are limited to a Jellyfin-configuration ZFS snapshot, the
official plugin directory, lower-priority provider entries for supported movie,
show, season, artist and album image types, one Jellyfin restart, functional
validation, documentation and focused local commits. No bulk metadata or image
refresh, personal fanart.tv key, media rename/write, account/authentication,
network, DNS, firewall, certificate, Homepage, NetBox, other-service or remote
Git change is authorized.

The Jellyfin official catalog owns package identity and compatibility; the live
Jellyfin library options own provider order; fanart.tv owns returned artwork;
this document owns project scope and recovery evidence.

## Architecture, privacy and security

Jellyfin will make outbound HTTPS requests to fanart.tv using media provider
identifiers when a relevant metadata/image search occurs. No inbound listener or
new credential is added. The plugin's shared project access is sufficient; a
personal key is deliberately excluded. Fanart is ordered after existing image
providers so it fills gaps rather than becoming the primary authority.

## Pre-start risk assessment

- **Availability:** one controlled Jellyfin restart, expected around 45 seconds.
  Abort if startup does not complete or existing plugins fail to load.
- **Integrity:** provider-order mistakes could change future artwork selection.
  Use exact before/after option diffs and do not run a bulk refresh.
- **Privacy:** future searches disclose media identifiers to fanart.tv. This is
  limited to the feature's purpose and introduces no account identity.
- **Recovery:** snapshot `/config` immediately before installation. First-line
  rollback removes Fanart and its provider entries, preserving newer watch state;
  whole-snapshot rollback is reserved for configuration damage.
- **Dependencies:** official Jellyfin package repository and fanart.tv HTTPS.
- **Data/speech:** no media payload or spoken output changes.

Jason selected Stream A after receiving the exact install, enablement, restart,
validation and rollback proposal. Execution begins only after the separate
LRCLIB backfill completes and validates.

## Persistence and milestones

- [x] Discover live state and verify the official package and checksum.
- [x] Confirm LRCLIB backfill completion and Jellyfin health.
- [x] Capture the pre-install snapshot and exact library-option baseline.
- [x] Install Fanart, restart Jellyfin and verify every existing plugin reloads.
- [x] Enable Fanart only as a lower-priority supported image provider.
- [x] Validate a read-only artwork search without changing selected artwork.
- [x] Record rollback evidence, integration impacts and final health.
- [x] Commit only project-owned documentation; do not push without approval.

Resume by rereading this document and the project standard, checking Git status,
verifying the LRCLIB task is no longer running, and rechecking the live plugin
and library-option state before any mutation.

## Validation and graduation

Graduation requires a healthy public endpoint and private HTTPS UI, Fanart 15.0.0.0
active, all prior plugins loaded, exact provider ordering, at least one successful
read-only Fanart result, no bulk refresh, and a documented narrow rollback.
Provider latency and returned-image usefulness will be sampled; installation
alone is insufficient.

## Integration impact

- Existing Jellyfin configuration backup and availability monitoring cover the
  change; the new snapshot provides an immediate checkpoint.
- No host/container/port changes: Beszel, NetBox, DNS, firewall, certificates,
  Homepage and diagrams are not applicable.
- Native/SSO authentication and AI administration are unchanged.
- This project document and the eventual completion record are the repository
  operational references; no Aster mirror update is needed for this small
  optional provider.
- No new service or environment is created, so the release registry and
  environment placement remain unchanged.

## Evidence log

| Date | Evidence | Result |
|---|---|---|
| 2026-10-17 | Live Jellyfin 12.1.0, existing plugins and library provider order inspected; official Fanart package downloaded and MD5 checked | Discovery gate passed; waiting for LRCLIB backfill |
| 2026-10-17 | LRCLIB task completed; 5,279 lyric sidecar paths measured from the protected snapshot; follow-up library scan completed | Dependency gate passed before restart |
| 2026-10-17 | `Media/appdata/jellyfin@pre-fanart-20261017T072554Z` present; staged DLL and metadata rechecked | Recovery and package gates passed |
| 2026-10-17 | Only the `jellyfin` container restarted; startup completed in 11.7 seconds | Fanart 15.0.0.0 and all prior external plugins loaded |
| 2026-10-17 | Library options updated and read back through the supported API | Fanart is last in both enabled-provider and provider-order lists for every targeted type |
| 2026-10-17 | Read-only remote-image lookup on a music album | Fanart provider available and returned three candidates; no image was downloaded or selected |
| 2026-10-17 | Public information endpoint and private HTTPS SSO UI | Jellyfin 12.1.0 setup complete; HTTPS returned HTTP 200 |

## Completed provider order

Fanart is enabled last in both `ImageFetchers` and `ImageFetcherOrder` for:

- `Movie` in Movies and Archive Movies, after all existing image providers;
- `Series` and `Season` in Shows and Archive TV, after TheMovieDb; and
- `MusicArtist` and `MusicAlbum` in Music, after the existing AudioDB and,
  where applicable, embedded-image providers.

Archive Movies and Archive TV previously represented their effective defaults
with empty `TypeOptions`. Their API updates expanded those inherited defaults
using the matching live Movies and Shows options, then appended only Fanart to
the supported type lists. Episode and Audio options, metadata providers, image
limits and every unrelated library option were preserved. Collections were not
changed because the plugin does not expose the requested movie/show/season or
music provider types there.

## Close-out and documentation reflection

The project graduated on 2026-10-17. Fanart 15.0.0.0 is active, all existing
plugins reloaded, a provider-specific read-only search returned results, and no
bulk artwork refresh or image selection occurred. The retained snapshot and
the exact order above are sufficient for update and rollback operations.

First-line rollback is to remove `Fanart` from only the listed image-provider
arrays through the same API, remove
`data/plugins/Fanart_15.0.0.0`, and restart only Jellyfin. The snapshot is a
last-resort recovery point because restoring it would also discard newer
Jellyfin configuration and watch state. No remote Git operation was performed.
