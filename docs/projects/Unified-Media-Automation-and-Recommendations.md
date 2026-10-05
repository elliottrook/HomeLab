# Unified Media Automation and Recommendations

> Status: Active — Stream A; M0 in progress
>
> Project owner: Jason
>
> Proposed: 2026-10-05
>
> Authorization stream: Stream A

## Purpose and desired outcome

Build one private, Docker-managed media automation and recommendation layer
for films, television, music, ebooks and audiobooks. The user-visible result
is a single recommendation view that explains why an item is suggested and
offers the correct one-button action:

- request films and TV through Seerr, which remains the request authority;
- request music albums through Lidarr;
- mark ebooks and audiobooks wanted through the selected book automation
  service; and
- create or update Jellyfin playlists after acquired music is present.

The project also migrates the current TrueNAS Apps used for books and
audiobooks into the existing Docker/Dockge operating model, while preserving
the current media lifecycle: newly acquired high-quality films and TV remain
in the active libraries for four months, then the existing A380-backed
video-archiver transcodes and moves them into separate archive libraries.

## Scope and authorization envelope

This project is authorized as Stream A only after Jason accepts this exact
envelope. The permitted change classes are:

- create a Docker Compose/Dockge project on TrueNAS for the recommendation
  portal, book automation, audiobook/ebook library services and their
  documented dependencies;
- configure read-only readers for Jellyfin, Sonarr, Radarr, Lidarr,
  Audiobookshelf and the ebook catalog;
- configure narrowly scoped write adapters for Seerr, Lidarr, LazyLibrarian
  and Jellyfin playlists, each requiring an explicit user button action;
- migrate Audiobookshelf and the current Calibre/Calibre-Web workflow from
  TrueNAS Apps to Docker with checkpoints, temporary ports and retained
  recovery paths;
- repair or replace the unhealthy Calibre-Web Automated deployment;
- add private Authentik/NPM routes, Homepage discovery, Doctor checks,
  monitoring and protected configuration backups for newly deployed services;
- normalize container media paths to a common `/data` contract while keeping
  active and archive libraries as separate roots;
- create the recommendation data model, ranking pipeline, API adapters,
  approval UX and local Aster llama.cpp explanation calls; and
- run bounded acquisition tests using Jason-selected disposable or
  explicitly approved media candidates.

Explicit exclusions:

- no second or third GPU; the Proxmox Arc Pro B60 remains dedicated to Aster
  inference and the TrueNAS Arc A380 remains dedicated to Jellyfin/media
  transcoding;
- no migration of Jellyfin, Sonarr, Radarr, Lidarr, Prowlarr, SABnzbd or the
  A380-backed video-archiver away from TrueNAS;
- Bazarr is a concurrent Stream A project owned by another Codex task. This
  project must not modify its container, configuration, credentials, routes,
  mounts or subtitle workflow; it may only validate Bazarr's graduated result
  as an integration dependency.
- no collapse of active and archive libraries, no change to the four-month
  archive policy, and no archive deletion or bulk re-encoding policy change;
- no direct AI access to raw production credentials, download clients or
  databases;
- no automatic acquisition from an AI recommendation without a user action;
- no automatic following of entire artists, authors or series by default;
- no public ingress, new WAN exposure, broader firewall trust, or external
  streaming-service recommendation integration unless separately approved;
- no deletion of the existing TrueNAS Apps or their data until migration and
  restore gates pass; and
- no Git push, remote workflow change, release, tag or pull request mutation
  under this charter without the required immediate confirmation.

## Current state and evidence

- TrueNAS `192.168.20.40` hosts Sonarr, Radarr, Lidarr, Prowlarr, SABnzbd,
  Jellyfin, Seerr, Bazarr, Newtarr and Profilarr in Docker-managed services.
- The media dataset is `/mnt/Media/data`, currently about 7.7 TB used and
  6.0 TB available. Existing containers share the dataset through host
  bind mounts, which is the preferred hardlink topology; NFS is not required
  for these same-host containers.
- Active video roots are `/mnt/Media/data/media/movies` and
  `/mnt/Media/data/media/tv`. Archive roots are
  `/mnt/Media/data/archive-movies` and `/mnt/Media/data/archive-tv`.
- The existing video-archiver uses the TrueNAS-hosted Jellyfin container and
  the Intel Arc A380 for bounded HEVC VA-API conversion before moving aged
  content into archive roots. This project preserves that system.
- The TrueNAS host has an Intel Arc A380 (`8086:56a5`) using `i915`; Jellyfin
  receives `/dev/dri`. The Proxmox host separately has the Intel Arc Pro B60,
  mapped to Aster llama.cpp LXC 110. These are separate ownership domains.
- Audiobookshelf currently runs as a TrueNAS App with approximately 49 GB of
  audiobooks and about 46 titles. It has a working API and is the playback,
  user and listening-progress authority.
- Calibre-Web Automated currently runs in Docker but is unhealthy. The
  existing ebook library is `/mnt/Media/media/books`; its current Calibre
  workflow and metadata database require a single-writer migration plan.
- The existing Music Recommender is report-only and proposed. The Music
  Playlist Acquisition Bridge already translates playlists into conservative
  Lidarr album requests and creates Jellyfin playlists after import.
- Readarr is not a suitable new foundation: the upstream project was retired
  and archived. LazyLibrarian is the proposed replacement for ebook and
  audiobook acquisition, subject to the pilot's metadata and import tests.
- Aster llama.cpp is available at `192.168.70.12:11435/v1` for local,
  bearer-authenticated explanation generation. Core ranking remains
  deterministic and auditable.

## Target architecture and data flows

```text
                         +-----------------------------+
                         | Unified Media Portal         |
                         | recommendations + actions    |
                         +--+----------+----------+-----+
                            |          |          |
                     Seerr API   Lidarr API   LazyLibrarian API
                            |          |          |
                      Sonarr/Radarr  Lidarr    book/audio wanted queue
                            |          |          |
                       Prowlarr/SABnzbd       Prowlarr/SABnzbd
                            |          |          |
                       active video     music/books/audiobooks
                            |          |          |
                    video-archiver       Jellyfin / CWA / Audiobookshelf
                    (unchanged)                |
                         TrueNAS `/data` shared media contract

       Jellyfin + Sonarr/Radarr/Lidarr + CWA + Audiobookshelf metadata
                                |
                    sanitized local recommendation snapshot
                                |
                         Aster llama.cpp narrative
```

The common container mount contract is:

```text
/data/downloads
/data/media/movies
/data/media/tv
/data/media/music
/data/media/books
/data/media/audiobooks
/data/archive-movies
/data/archive-tv
/data/inbox
```

The common mount does not imply a single library. Active movies/TV and archive
movies/TV remain distinct Jellyfin libraries. Sonarr/Radarr own only active
roots; the video-archiver owns the active-to-archive transition and continues
to unmonitor replaced parents to prevent reacquisition.

## Application decisions

### Films and television

- Seerr is the sole household request front door.
- The portal submits a request to Seerr, never directly to Radarr/Sonarr.
- Seerr remains connected to Jellyfin, Radarr and Sonarr.
- SuggestArr may be evaluated later, but is not the default recommendation
  path because it is designed to create requests automatically from viewing
  activity.

### Music

- Jellyfin is the library and playback authority.
- Lidarr remains the acquisition authority.
- The portal recommends artists/albums using Jellyfin and Lidarr state, and
  requests one album per user action by default.
- Existing playlist-bridge logic is reused for imported Spotify/Apple/other
  playlists and for post-import Jellyfin playlist creation.
- Whole-artist following is disabled initially; a bounded starter-set action
  may be considered after the album request path is proven.

### Ebooks and audiobooks

- LazyLibrarian is the pilot acquisition manager for both ebooks and
  audiobooks, using Prowlarr and SABnzbd.
- Calibre-Web Automated is the ebook library and conversion/presentation
  service. It receives ebooks through a controlled ingest path and remains the
  sole active writer of the Calibre metadata database after migration.
- Audiobookshelf remains the audiobook playback, user and progress service,
  moved from TrueNAS Apps into Docker.
- Kavita is optional follow-up work for a richer multi-format reader, not a
  second ebook authority in this project.
- New authors, series and collections are not automatically acquired in full.
  Recommendations create an explicit wanted item only after the user clicks.

## Privacy and security design

- All recommendation computation and LLM narration remain inside the lab.
- The portal receives sanitized metadata snapshots, not raw service configs,
  credentials, download history or unrelated household data.
- Per-service credentials are dedicated and least-privilege. Read-only keys
  are used for recommendation sources; write keys are limited to the action
  adapter that needs them.
- The portal cannot call Radarr, Sonarr, Lidarr or SABnzbd directly for a
  recommendation. It calls Seerr, Lidarr's bounded album path or
  LazyLibrarian's wanted path according to the media type.
- Write actions are idempotent, duplicate-aware and recorded with user,
  timestamp, media identifier, target service and result.
- Listening and watch history is treated as household behavioral data. It is
  retained only as long as needed for the recommendation snapshot unless a
  separate trend-retention decision is accepted.
- Browser access uses the existing private Authentik/NPM pattern with a
  direct LAN recovery path. No public route is created.

## Pre-start risk assessment

| Risk | Likelihood / impact | Control | Abort condition |
|---|---|---|---|
| Migration corrupts an App database or library | Medium / high | Stop source App, protected export, temporary Docker port, read-only validation, isolated restore | Export or restore cannot be verified |
| Calibre metadata has concurrent writers | Medium / high | Single-writer contract; ingest staging; no live DB edits during cutover | Any unexplained `metadata.db` change or lock conflict |
| Recommendation action acquires the wrong item | Medium / medium | Deterministic ID matching, duplicate check, explicit one-button action, bounded test candidates | Ambiguous TMDb/MusicBrainz/Open Library match |
| AI consumes excessive Aster capacity | Medium / medium | Batch generation, token/time limits, deterministic ranking, queue visibility | Production inference latency or error budget degrades |
| Active/archive boundary is weakened | Low / high | Preserve roots, filters and video-archiver unchanged; regression checks | Any archive content becomes monitored or reacquired |
| Book metadata/provider quality is poor | Medium / medium | LazyLibrarian pilot, small author/title set, manual review before rollout | Incorrect identity or duplicate import rate exceeds acceptance threshold |
| New services broaden network exposure | Low / high | Existing VLAN/private proxy pattern only; no WAN/DNS exposure | Firewall or proxy scope differs from charter |
| Backups do not cover the new services | Medium / high | Add config exports and isolated restore before graduation | Fresh backup or restore gate fails |

Recovery checkpoints are required before each migration cutover, before any
first write-enabled recommendation test, and before enabling recurring jobs.
Rollback is to stop the new container, restore the previous App or Docker
configuration, restore only the affected application state, and leave media
files untouched unless a separately recorded import rollback is required.

## Milestones

### M0 — Charter, inventory and checkpoints

- [x] Jason accepts this Stream A envelope.
- [x] Capture current Compose/App definitions, service configs and protected
  backups without exposing secrets.
- [x] Reconcile live paths, versions, API capabilities and current health.
- [x] Confirm the archive workflow's schedules, roots, exclusion filters and
  A380 transcode path as regression baselines.

Gate: recoverable baseline exists and no material topology surprise remains.

### M1 — Docker media foundation

- [x] Create the Compose/Dockge project and `/data` path contract.
- [x] Deploy LazyLibrarian, Calibre-Web replacement/repair and the Docker
  Audiobookshelf instance on temporary ports.
- [x] Validate ebook and audiobook library scans, users, metadata and playback.
- [x] Prove Calibre single-writer behavior and ebook ingest/conversion.

Gate: book/audio services work without changing the production library or
removing the source Apps.

### M2 — One-click request adapters

- [ ] Implement and test Seerr movie/TV requests.
- [ ] Implement bounded Lidarr album requests using existing bridge patterns.
- [ ] Implement LazyLibrarian wanted-item actions.
- [ ] Add duplicate, ambiguous-match, idempotency and failure handling.

Gate: Jason can approve one synthetic or explicitly selected item in each
domain and observe the correct downstream request without direct AI authority.

### M3 — Recommendation pipeline and portal

- [ ] Build local readers for Jellyfin, Sonarr/Radarr/Lidarr,
  Audiobookshelf, Calibre-Web Automated/ebook metadata and LazyLibrarian.
- [ ] Confirm usable watch, listening and play-history signals; fall back to
  library composition when history is unavailable.
- [ ] Add deterministic ranking, AI explanations, media-type cards and one
  action button per candidate.
- [ ] Add private Authentik/NPM route, Homepage tile and direct recovery URL.

Gate: a reviewed recommendation batch contains no owned, archived, duplicate
or ambiguous items and every action routes to the correct authority.

### M4 — Music integration and playlist lifecycle

- [ ] Integrate the Music Recommender logic with the portal.
- [ ] Reuse playlist-bridge matching, retries and post-import reconciliation.
- [ ] Validate one-album requests and private Jellyfin playlist creation.
- [ ] Keep whole-artist following disabled unless separately accepted.

Gate: a requested album imports through Lidarr, appears in Jellyfin and is
represented accurately in the portal.

### M5 — App cutover and operational hardening

- [ ] Cut over Audiobookshelf and Calibre-Web Automated from TrueNAS Apps to
  Docker after restore and playback tests.
- [ ] Add Doctor checks, service health, stale-run and failed-action signals.
- [ ] Add protected config backups and perform isolated restore tests.
- [ ] Validate Authentik, direct recovery, Homepage, DNS and TLS paths.

Gate: source Apps remain recoverable, Docker services survive restart, and
backup/restore evidence is complete.

### M6 — Graduation

- [ ] Complete two independent production-path recommendation/request passes.
- [ ] Verify no active/archive regression and no unexpected acquisition.
- [ ] Complete documentation, wiki/mirror summaries, operational runbooks and
  systems-of-record updates.
- [ ] Create a focused local Git commit for the milestone.
- [ ] Request separate immediate confirmation before any Forgejo push.

## Validation and evaluation

- Functional: one successful request in films/TV, music, ebook and audiobook
  domains.
- Recommendation quality: Jason reviews a fixed sample for relevance,
  duplication, owned-item suppression and explanation accuracy.
- Safety: ambiguous IDs, already-owned items, archived items, duplicate
  requests, failed APIs and stale snapshots all fail closed.
- Storage: hardlink test for active ARR imports; separate active/archive roots
  remain visible and correctly excluded from ARR monitoring.
- Transcoding: Jellyfin and video-archiver continue using the TrueNAS A380;
  no B60 dependency is introduced.
- Migration: App-to-Docker restart, backup and isolated restore tests pass.
- Performance: portal remains responsive while Aster explanation jobs are
  queued; request actions do not block on LLM availability.

## Observability and maintenance

The project extends, rather than replaces, HomeLab Doctor, Prometheus/Grafana,
Beszel and Homepage. It adds:

- recommendation snapshot freshness;
- action success/failure and duplicate suppression;
- Seerr/Lidarr/LazyLibrarian request lag;
- ebook ingest/conversion failures;
- Audiobookshelf scan freshness;
- Calibre database backup age and single-writer violations;
- Docker container health and image/version inventory; and
- regression checks for the active-to-archive video pipeline.

No Uptime Kuma deployment is required unless an uncovered failure mode is
identified during M0.

## Backup, restore and rollback

Protect application configuration, databases, API integration settings,
recommendation state, action audit logs and Calibre metadata. Bulk media stays
under the existing media backup boundary. Before each cutover:

1. export the source App configuration;
2. create a dated Docker-state checkpoint;
3. verify archive integrity and expected paths;
4. run the replacement in isolation or on a temporary port; and
5. retain the source App disabled but recoverable until graduation.

No media deletion, archive removal, ZFS dataset destruction or destructive
Calibre rewrite is authorized by this charter.

## Integration impact

- **NetBox:** no new VM, LXC or physical asset; register only a new service
  relationship if the existing model requires it.
- **Human wiki:** document operator setup, request semantics, provider
  custody, migrations and recovery.
- **Aster mirror:** publish only sanitized operational summaries.
- **Homepage:** add one private portal tile and service health widgets without
  embedding credentials.
- **Auth/Networking:** reuse existing private DNS, NPM and Authentik patterns;
  no public ingress.
- **Backups:** extend protected config exports and prove isolated restoration.
- **Existing projects:** this charter becomes the governing integration
  project for the proposed Recommendarr, Book Recommender and Music
  Recommender work. The completed Video Library Archiving project and active
  Music Playlist Acquisition Bridge remain authorities for their existing
  workflows.

## Graduation criteria

The project graduates only when the unified portal handles all four request
domains, Docker migrations have passed restore and playback tests, the active
versus archive video lifecycle is unchanged and verified, all actions are
explicit and auditable, the A380/B60 ownership split remains intact, Doctor and
backups cover the new services, and the remaining limitations are accepted in
the evidence log.

## Evidence log

- 2026-10-05: Existing repository proposals, ARR reference, music playlist
  bridge, book recommender, music recommender and archive/transcoding records
  reviewed.
- 2026-10-05: Live TrueNAS discovery confirmed Docker-managed ARR/Jellyfin
  services, Seerr, Bazarr, Newtarr, Profilarr and Audiobookshelf App; current
  Calibre-Web Automated container is unhealthy.
- 2026-10-05: Live TrueNAS GPU discovery confirmed Intel Arc A380 `8086:56a5`,
  `i915`, `/dev/dri`, and Jellyfin device mapping. Proxmox B60 remains a
  separate Aster inference device.
- 2026-10-05: Charter created as Ready — Stream A; implementation remains
  gated on Jason's explicit acceptance of this envelope.
- 2026-10-05: Jason said “Let's begin,” accepting the Stream A authorization
  envelope. M0 baseline and checkpoint work may proceed within the stated
  scope; operational cutovers remain gated by their milestone gates.
- 2026-10-05: M0 live baseline confirmed the ARR/Jellyfin services are in
  Docker Compose project `new_arr`, with `/mnt/Media/data` shared through
  service-specific container paths; no NFS migration is needed for the
  same-host services.
- 2026-10-05: M0 confirmed Audiobookshelf remains a TrueNAS App
  (`ix-audiobookshelf`) while Calibre-Web Automated is Docker-managed but
  unhealthy. No cutover or restart was performed.
- 2026-10-05: M0 confirmed existing schedules: Jellyfin integrity Wednesday
  03:00, Playlist Bridge every six hours, video archiving Monday–Saturday
  01:30, and the five-minute ARR report. The Playlist Bridge job is currently
  labelled `Eminem test`; its ownership and intended production scope must be
  validated before this project adds or changes music automation.
- 2026-10-05: M0 acceptance gate passed for baseline topology and GPU
  separation. M1 remains gated on protected service checkpoints and the
  Calibre single-writer/migration design; no operational cutover has started.
- 2026-10-05: M1 discovery found the existing `new_arr` Compose definition
  already has a reusable Docker foundation and retained `.codex-*`/dated
  rollback copies. The current Sonarr/Radarr mount destinations differ
  (`/media/tv` and `/media/movie`) and will be normalized only through a
  staged path-migration test.
- 2026-10-05: M1 discovery found Calibre-Web Automated's unhealthy status is
  associated with an HTTP health listener receiving TLS bytes and then
  crashing while formatting the malformed request. This is a bounded health
  configuration/upgrade issue, not evidence that the ebook database is safe
  to rewrite. No restart or healthcheck change was made.
- 2026-10-05: M1 discovery confirmed Audiobookshelf's current App state is
  healthy and its metadata/config paths are distinct from the audiobook media
  path. Migration will therefore use an additive Docker instance and a
  post-cutover library scan, not an in-place mount rewrite.
- 2026-10-05: Jason reported that Bazarr integration is being completed by a
  concurrent Codex task. Bazarr is now an explicit no-touch dependency for
  this project; shared `/data` changes must preserve its final mount contract.
- 2026-10-05: M1 created the reversible shadow-stack artifacts at
  `services/unified-media/compose.shadow.yaml` and its README. The stack uses
  temporary loopback ports, no acquisition credentials, a read-only audiobook
  mount and a read-only live Calibre library. Local Docker Compose
  validation was unavailable because the calling Mac has no `docker` binary;
  validation remains a TrueNAS-side gate before startup.
- 2026-10-05: M1 TrueNAS validation started the shadow Audiobookshelf and
  LazyLibrarian containers successfully on loopback ports `30077` and `5299`.
  Audiobookshelf `/healthcheck` returned `OK`; LazyLibrarian reached its web
  listener with no providers or download credentials configured.
- 2026-10-05: M1 CWA shadow validation exposed a migration constraint: the
  image recursively changes ownership under its application/library paths at
  startup and remained in uninterruptible `chown` state, so it never reached
  its web listener. The shadow CWA container was stopped and removed; the
  production CWA container and live Calibre library were not changed. This
  required an M1 architecture decision before the ebook cutover.
- 2026-10-05: Jason selected the Kavita evaluation path. The shadow stack was
  updated to use LinuxServer Kavita on temporary loopback port `8284`, with a
  disposable ebook-library copy and no production Calibre mount. Kavita
  reached `/api/Health` with HTTP 200 after its first-run migrations. Adoption
  remains gated on library setup, scan/read validation and the Calibre
  single-writer/import contract.
- 2026-10-05: The TrueNAS management address became unreachable from the
  approved Proxmox read-only path during the Kavita setup check (SSH timeout
  and ICMP loss). No retrying mutation, production restart or cutover was
  attempted; the remaining shadow API/library validation is resumable.
- 2026-10-05: Diagnosis corrected the enforcement point to OPNsense, not
  UniFi. With Jason's approval, OPNsense received two logged, host-specific
  rules: Proxmox `192.168.50.10` to TrueNAS `192.168.20.40` TCP 22
  (`9f8d5c1e-6e6d-4b61-9b43-0c9b5f29e2a1`) and TCP 443
  (`a2b7d4f0-7f3c-4d72-9b4d-1e8c6a54f903`). A protected pre-change copy was
  saved at `/conf/backup/config-unified-media-before-20261005.xml`; the
  rules were applied with `configctl filter reload` and live counters showed
  one state and seven packets on each rule. Proxmox TCP connection tests to
  both ports succeeded. No VLAN-wide route, Docker port, or service exposure
  was added.
- 2026-10-05: Kavita shadow setup completed registration and library creation,
  but the LinuxServer build (`v0.9.1.4`) rejected both a copied Calibre EPUB
  and a generated valid EPUB during scanning, producing zero series. The
  upstream `jvmilazz0/kavita:latest` image was also tested on a separate
  loopback port and remained stuck during first-run startup. Both disposable
  containers were stopped and removed; production Calibre, CWA,
  Audiobookshelf and ebook data were untouched. Kavita is not adopted for
  cutover until a version-specific parser/startup test succeeds.
- 2026-10-05: M1 evaluated LinuxServer Calibre-Web on loopback port `8284`
  using the disposable Calibre database/library copy. It loaded the database,
  rendered 128 book links without a database error, served a book detail page,
  and returned a working reader page. The shadow container was stopped after
  validation; production CWA, Calibre metadata and ebook files were not
  mounted or changed. Calibre-Web is now the ebook presentation candidate;
  acquisition and single-writer cutover remain open.
- 2026-10-05: M1 corrected the shadow Audiobookshelf source after the first
  scan exposed an empty-path mismatch: `/mnt/Media/data/media/audiobooks`
  exists but is empty, while the production App mounts
  `/mnt/Media/media/audiobooks`. The compose file now uses an explicit
  `UNIFIED_AUDIOBOOKS_PATH` defaulting to the confirmed production dataset and
  mounts it read-only. After recreating only the shadow container, it saw 757
  audiobook files; the scan endpoint returned HTTP 200 and the library API
  reported 24 indexed items. LazyLibrarian remained healthy on HTTP 303 to
  `/home` with no providers or downloader credentials configured. Production
  Audiobookshelf, media files and acquisition workflows were not changed.
- 2026-10-05: M1 smoke checks confirmed the shadow Audiobookshelf audiobook
  bind is `rw=false`, its health endpoint returns HTTP 200, and LazyLibrarian
  remains reachable with HTTP 303. Both containers remain loopback-only;
  their configuration/metadata paths are separate shadow paths.
- 2026-10-05: M1 read-only topology inspection confirmed the live
  `calibre-web-automated` container is the only current container mounting
  `/mnt/Media/media/books` read-write; its separate ingest directory is empty,
  and the container remains unhealthy. No test book was placed in the live
  ingest path. The migration therefore retains the single-writer requirement
  and needs a disposable ingest/conversion test before any cutover decision.
- 2026-10-05: A second bounded CWA shadow test used a separate config,
  ingest directory and a tiny disposable ebook library. CWA completed its
  database initialization and then stalled during its recursive ownership
  pass over the library/ingest paths; it remained health `starting` and never
  opened its web listener. The disposable container was removed. CWA is not
  an acceptable migration target on this TrueNAS dataset until its startup
  ownership behavior is resolved; evaluate a separate Calibre worker/import
  path while retaining Calibre-Web for presentation.
- 2026-10-05: M1 tested the existing `ghcr.io/linuxserver/calibre:9.13.0`
  image as a disposable worker. With a separate library and read-only input,
  `calibredb add` created a new `metadata.db` with one imported EPUB, and
  `ebook-convert` produced a valid AZW3 output (`10,658` bytes). The
  disposable worker paths were removed afterward. This validates the worker
  primitive without authorizing LazyLibrarian credentials, live-library
  writes or a production ingest change.
- 2026-10-05: M1 added a profile-only guarded Calibre worker definition under
  `services/unified-media/calibre-worker`. Compose validation passed on
  TrueNAS. The wrapper refused the live library with exit code 2 unless its
  explicit override was supplied, while the disposable library listed 505
  records and converted a test EPUB to a 10,658-byte AZW3. Temporary test
  files were removed; no production library or ingest path was mounted.
- 2026-10-05: With Jason's approval, the isolated LazyLibrarian shadow was
  given separate `/downloads`, `/books` and `/audio` paths and configured to
  use the existing SABnzbd service through the valid `prowlarr` category.
  SABnzbd connection testing passed with version `5.1.3`; no download was
  submitted. Both existing Prowlarr indexers advertise no Newznab book or
  audiobook search capability in their advertised caps, so the first provider
  test failed. Read-only `t=book&q=Dune` probes nevertheless returned 83 and
  100 results through the two Prowlarr indexer endpoints. The shadow provider
  was then enabled with explicit `book` mappings for ebook and audiobook
  searches; SABnzbd connectivity still passed and no grab/download was made.
- 2026-10-05: With Jason's approval, SABnzbd's API created the isolated
  `books-shadow` category at `/media/downloads/books-shadow`; a pre-change
  configuration copy was saved at
  `/mnt/Media/appdata/unified-media-shadow/sabnzbd-before-dune-20261005.ini`.
  A bounded Dune EPUB test was submitted. Prowlarr returned a valid NZB and
  SABnzbd downloaded, verified and extracted the payload, but the first
  post-processing move failed because the new category directory was owned by
  root. Ownership was corrected to the existing `apps` UID, but the same
  one-time result was then protected by Prowlarr's duplicate-download rule
  before a second completion could be made. The queue and Dune staging data
  were cancelled/removed; no Calibre or audiobook library was touched. The
  remaining test gap is final handoff into the disposable ingest path.
- 2026-10-05: A fresh Dune-series result from the second Prowlarr indexer
  completed the bounded acquisition test. SABnzbd reported `Download
  Completed` in `books-shadow`, producing one EPUB; the guarded Calibre worker
  then imported it into a separate temporary library and reported one Calibre
  record. The temporary library, output and downloaded payload were removed,
  while the empty `books-shadow` boundary was retained with `apps` ownership.
  The test did not touch production Calibre, Audiobookshelf, active media or
  archive roots.
- 2026-10-05: M1 playback validation used the isolated Audiobookshelf API to
  create a direct-play session for a scanned audiobook item. The shadow
  service returned a playback session successfully; production Audiobookshelf
  state and media were not used. M1 gate passed with the source Apps retained
  and recoverable.
