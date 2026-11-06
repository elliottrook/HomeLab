# Aster media lifecycle redesign

> Status: In progress — M0 live discovery began after the
> Wednesday 2026-11-04 01:00 America/Vancouver (PST) start gate
>
> Owner: Jason | Proposed and authorized: 2026-11-02 | Stream A — Autonomous
>
> Governing process: HomeLab `docs/Project-Creation-Standard.md`.

## Authorization and start gate

Jason explicitly directed on 2026-11-02 that this project be completed under
Stream A and that implementation **not start until Wednesday 2026-11-04 at
01:00 America/Vancouver**. Creating and pushing this planning record now is
the separately requested preparation. No live discovery, service/configuration
mutation, media rewrite, or other implementation milestone may begin before
that time.

The Stream A envelope is limited to the media lifecycle scope and exclusions
below: read-only inventory; bounded changes to the existing arr profiles,
optimizer/archiver/compactor, Jellyfin presentation, subtitle handling,
monitoring, recovery, documentation and their tests; and staged deployment
after each gate. It does not authorize irreversible bulk replacement, removal
of the last recovery copy, new public exposure, credential disclosure, or a
materially different system or objective. Any newly discovered material risk
or failed recovery checkpoint triggers the standard's non-waivable stop
condition. Forgejo pushes beyond this specifically requested planning push
still follow the repository's immediate remote-write authorization rule.

## Purpose and desired outcome

Keep one Radarr/Sonarr-managed, monitored copy of each title while providing
distinct Current and Archive views in Jellyfin. Preserve the best acceptable
picture, genuine HDR, 5.1 audio and English subtitles under a 5 GB Archive
ceiling; leave exceptions playable in Current. Do not recompress for its own
sake. Existing 480p/720p/stereo files stay playable and monitored until a
genuine upgrade exists.

## Agreed intent

- Keep existing playable files in Radarr or Sonarr, monitored while a better release is sought.
- Jason clarified on 2026-11-06 that older 480p/720p or stereo titles remain
  visible in Archive once old enough while their arr entries stay monitored
  for a genuine upgrade. Their legacy quality is not, by itself, a reason to
  fill Current with old titles.
- Prefer genuine 1080p, HDR and 5.1 audio for new acquisitions. Do not manufacture HDR or surround sound by upscaling or upmixing older sources.
- Retain Current and Archive views in Jellyfin. Preferred layout: one physical `tv` root and one physical `movies` root, with age-based views rather than file moves. This needs a client-specific view pilot before migration.
- Preserve genuine HDR and a usable 5.1 track when compressing. Preserve 4K if it remains visually sound under the limit; if it cannot, a good 1080p version is authorized. Never upscale or upmix an older source.
- Retain every English subtitle track, including forced and SDH variants, and any external English subtitle sidecar. Preserve language, forced and hearing-impaired flags. If a subtitle cannot be retained in the output container, fail the encode and report it; do not silently retry without subtitles or delete the source.
- Treat 5,000,000,000 bytes per file as an Archive ceiling, not an encoding target. Do not recompress a compliant file just to make it smaller. With virtual views, oversized files stay in Current even after four months.
- Existing files already over 5 GB in the physical Archive are a mandatory
  optimization backlog. Attempt quality-led compression for every such file;
  if an acceptable output cannot fit, keep the original playable and classify
  it as a Current exception until the source can be handled safely. Never
  silently grandfather an over-ceiling file as Archive.
- Keep an archive-eligible file registered in Radarr/Sonarr and monitored. The preferred virtual-view design needs no archive move. If physical folders are retained, a move must update the application's own path or root folder rather than deleting the file record and unmonitoring the title.

## Current state and evidence

The code findings below come from a local HomeLab checkout inspected on
2026-11-02. The planning checkout was freshly cloned from Forgejo main.
TrueNAS and the live arr/Jellyfin configuration were not reachable from this
workspace. Historical repository evidence is not a claim that production is
healthy today.

### Current code conflicts

- `pipeline.py` deletes the Radarr/Sonarr file record and unmonitors its parent after moving the file.
- `transcode.py` selects a lower resolution tier to fit the size target, can select a default stereo track over an available English 5.1 track, and verifies only size and duration.
- `transcode.py` currently retries a failed subtitle-bearing encode without subtitle streams, which conflicts with the new retention standard.
- `compact.py` can also step down resolution and targets roughly 1.9 GB, creating a second encoding pass.
- `config.example.json` still uses a 2 GB archiver maximum and a 2 GB compactor threshold.

## Scope and exclusions

In scope: Radarr/Sonarr quality and monitoring policy; the archiver and
compactor; English subtitle retention; Current/Archive presentation in
Jellyfin; related backup, Doctor and operating documentation. Excluded:
automatic reacquisition of the whole DVD library, invented HDR or surround
from old sources, a new downloader, public exposure, and irreversible bulk
media rewrites. Any bulk rewrite needs a separate risk decision.

## Authority model

| Fact | Authority |
|---|---|
| Actual stream properties and bytes | Probed file on TrueNAS |
| Title identity, monitoring, profile, import | Radarr/Sonarr |
| Watch state and Current/Archive display | Jellyfin |
| English sidecar retrieval | Bazarr plus files on disk |
| Job state | TrueNAS scheduler and durable run logs |
| Project decisions and evidence | This document in Forgejo after adoption |
| Service and host inventory | NetBox where applicable |

## Architecture and data flow

Radarr/Sonarr import into one movies and one TV root and remain responsible for
each file. A single optimizer probes files over the Archive size ceiling,
stages any candidate outside Jellyfin's libraries, and accepts a replacement
only after stream, size, playback and arr-record checks. Jellyfin presents
Current/Archive from import age and verified eligibility instead of physical
moves. A missing monitored file can be reacquired; a damaged file requires
separate verified quarantine because arr cannot infer corruption.

### Implementation shape

1. Inventory live arr profiles, custom formats, root mappings, existing file records, and the scheduler. Back up the application databases and configuration before migration.
2. Configure download profiles to prefer 1080p HDR and 5.1, with explicit fallback for older titles. Set quality and custom format cutoffs so a valid compressed copy does not trigger an automatic larger replacement. Preserve release quality metadata in filenames and arr records; resolution by itself is not a sufficient upgrade guard.
3. Give one optimizer authority over compression. It may replace a source only after verifying full playback properties, file size, and arr's updated file record. Do not encode a file twice merely because it moved to Archive.
   - If the source is already at or below 5 GB and meets its applicable quality rules, copy nothing and encode nothing.
   - If it exceeds 5 GB, try a quality-led encode and assess its final size. Do not force an output to 5 GB by continually lowering bitrate or resolution. If the quality floor fails, keep the original in Current and report the exception.
   - For a 4K HDR source, first assess 4K output under the ceiling. If its picture quality is inadequate, test a 1080p version with original aspect ratio, valid HDR signaling, multichannel audio, and all English subtitles. Test the output on AsterTV before any unattended replacement. If neither version passes, keep the source in Current.
   - Compare English subtitle tracks and flags before and after encoding. Stage and verify sidecars with the video. A missing or unsupported track blocks replacement.
4. Keep files in the two arr-managed roots and calculate archive status from a
   persisted first-seen import date, not filesystem modification time. The
   existing physical Archive roots seed a separate, one-time legacy Archive
   flag because ARR's migration `dateAdded` does not preserve their original
   age. For future transfers, persist ARR's new file `dateAdded` at first
   sight so an optimization cannot reset the view clock. For TV, the youngest
   new episode in a season must be at least four
   calendar months old before that season can be called Archive; a later
   episode resets only its own season. If exact rolling views are needed
   inside Jellyfin, pilot API-managed collections or tags and verify their
   presentation on the actual client. Jellyfin's ordinary Latest Media view
   is useful but does not enforce the four-month rule.
5. If physical archive folders are retained instead, move a whole movie through Radarr. Sonarr manages a series under one folder, so season-by-season moves are incompatible with a single Sonarr-managed series path. An entire series can move only when no season needs to remain Current.
6. Never classify an output over the archive size ceiling as Archive. Oversized or unverifiable files stay in Current and appear in an actionable report.
7. Detect genuinely missing or corrupt files separately. A missing monitored file may be reacquired through arr; corruption must first be verified and quarantined, since arr cannot infer it from resolution or file size alone.
8. Pilot on one movie and one completed series, then check Jellyfin visibility, arr monitoring and file records, RSS/search behavior, quality, and rollback before enabling a schedule.

## Privacy and security design

Keep media processing local. Reuse existing private network paths and the
narrowest available service identities. Store API keys outside Git and omit
private media details from logs and evidence. No new public ingress, DNS or
firewall change is expected. This project produces no speech, so the Aster
canonical voice requirement is not applicable. Any new Aster UI must follow
the HomeLab Aster UI style guide.

## Pre-start risk assessment — provisional

| Risk | Likelihood / impact | Control and stop condition |
|---|---|---|
| Irreversible quality, HDR, audio or subtitle loss | Medium / high | Keep source or verified checkpoint through pilot; compare streams and playback; stop on mismatch. |
| Arr sees a replacement as missing or upgradable | Medium / high | Inspect profiles and file records; pilot one title through refresh/RSS; stop on unplanned download. |
| Jellyfin loses watch state or household visibility | Medium / medium | Back up state and test actual TV client before changing libraries. |
| Concurrent jobs rewrite the same file | Medium / high | Inventory schedules and use one lock; stop on overlap. |
| 5 GB forces poor quality for long/grainy media | High for exceptions / medium | Keep original in Current and report exception. |
| Single-copy media cannot be restored | Medium / high | Verify checkpoint and isolated restore before replacement; stop if unavailable. |
| Secrets enter logs or Git | Low / high | Use redacted discovery and a pre-commit secret review. |

Affected systems: TrueNAS media, Radarr, Sonarr, Jellyfin, Bazarr, Doctor and
their backups. At planning time, current versions, job health, free space,
exact mounts, backup status and household client behavior were unverified.
Stream A is authorized for the bounded scope above from the scheduled start;
the live M0 assessment must resolve these unknowns before media replacement.
The non-waivable stop conditions still apply.

**Live risk update, 2026-11-05:** Radarr 6.4.4.10685, Sonarr 4.0.20.3014 and
Jellyfin 12.1.0 are responding; Bazarr and Profilarr are healthy. `Media/data`
has approximately 14.1 TB available. The media, Jellyfin and Docker-volume
datasets now have fresh named snapshots with proportional isolated restore
proof. The disabled legacy jobs are the only project production mutation.
Jellyfin was recently restarted amid separate AsterTV checkpoint activity, so
the M1 view pilot must avoid concurrent client/server changes. No new network
path, public exposure, credential transfer or irreversible action is needed.

## Persistence and resume plan

Use a versioned bounded state file recording source identity, original import
time, stream manifest, candidate output, verification and acceptance. Keep
partial output outside Jellyfin libraries; use a lock, atomic acceptance,
timeouts and idempotent resume. Persist no keys or raw private output. On
resumption reread this project, Git status and live state before replay.

## Milestones and completion gates

- [x] **M0 — Live discovery and risk acceptance:** inspect arr profiles, roots,
  schedules, sample streams/subtitles, backup health and Jellyfin client.
  Gate: evidence resolves ownership and recovery unknowns.
- [ ] **M1 — Current/Archive view pilot:** one movie and two seasons of one
  series, without file moves. Gate: expected TV-client display with unchanged
  arr monitoring and Jellyfin watch state.
- [ ] **M2 — Acquisition policy pilot:** 1080p/HDR/5.1 preference, legacy
  fallback, upgrade cutoffs and no mass search. Gate: suitable selection with
  no larger replacement of an accepted encode.
- [ ] **M3 — Optimizer pilot:** one compression authority, 4K then good 1080p
  fallback, English regular/forced/SDH/sidecar subtitles, size exceptions and
  interrupted-run recovery. Gate: verified playback, arr continuity and rollback.
- [ ] **M4 — Bounded rollout:** activate schedule only after backup and Doctor
  checks pass. Gate: repeated production runs and no collateral upgrades.
- [ ] **M5 — Graduation:** complete handover, restore proof, regression,
  efficiency review, records and accepted limitations.

Checkboxes are evidence claims and remain open until implementation,
validation, documentation and applicable backup work are complete.

## Validation and evaluation

Use synthetic SDR/HDR, stereo/5.1, aspect-ratio, English subtitle and damaged
sources; include one that cannot meet 5 GB acceptably. Test no-op on compliant
files, 4K-to-1080p fallback, interruption/restart, missing mounts, stale arr
metadata and a late episode resetting only its season's age. Pilot real media
only after a recovery checkpoint. Verify AsterTV playback, storage savings,
GPU load, household browsing and two independent production-path passes before
graduation.

## Observability and maintenance

Doctor should report stale runs, backlog, oversized Current exceptions,
stream-verification failures and arr/Jellyfin drift with actionable non-secret
output. Reconcile Beszel coverage for affected services and avoid duplicate
alerts. Name the maintenance owner and review compatibility after major updates.

## Backup, restore and rollback

Verify protected arr/Jellyfin databases, optimizer configuration/state and
media checkpoint before production work. Prove a proportional isolated
restore. Do not inherit the old compactor's `--no-snapshot` policy without a
new accepted risk decision. Roll back one layer at a time: disable new
schedule, restore prior helper/profile, reconcile arr records, then restore
media/Jellyfin state if needed.

## Documentation and systems-of-record impact

| Integration | Planned change or not-applicable reason |
|---|---|
| HomeLab Doctor | Add backlog, failure, ownership and view-drift checks. |
| Monitoring/Beszel | Reconcile service coverage and alert ownership. |
| Backup and recovery | Protect and restore-test application, optimizer and pilot media state. |
| NetBox | Check existing service/host facts; no new device or address expected. |
| Human wiki | Update lifecycle and recovery guidance. |
| Aster mirror | Refresh derived knowledge with provenance after authoritative docs change. |
| Operational reference/runbooks | Update job, profile, subtitle and recovery procedures. |
| Repository portfolio/changelog | Add this project to `docs/projects/README.md`; record dated milestones. |
| Diagrams/rack | Likely not applicable: no physical or topology change. |
| Homepage | Likely not applicable: no new service; consider an exception-report link. |
| Authentication | Review current service identities; no new human login expected. |
| DNS/certificates/firewall | Not applicable if existing private paths suffice; verify live. |
| Schedules | Replace overlapping encoders and prove missed-run/lock behavior. |
| Security inventory | Check credentials outside Git and file permissions. |
| AI administration | No new AI service; retain existing broker/human recovery boundary. |

## User-facing handover

Before graduation, give Jason a plain-language guide to Current/Archive views,
the 5 GB exception status, monitoring/upgrades, missing or damaged files and
subtitle failures. Record exact Jellyfin/AsterTV launch path and authentication
after the live pilot, then validate through a household walkthrough.

## Graduation criteria

All gates pass; arr ownership/monitoring persists; accepted files retain
required video/audio/English subtitles; the actual TV client distinguishes
Current and Archive; size exceptions and backups work; Doctor and records
reflect live state; residual risks are accepted. Only then retire the old jobs
or physical archive roots.

## Evidence log

- **2026-11-06 — M1 full-inventory preview, still unpublished:** refreshed
  read-only Sonarr and AsterTV Bedroom Kodi inventories. Sonarr has 223 series,
  5,646 episode files and 535 populated season groups; Kodi has 217 shows.
  A unique TVDB provider ID matches 196 Sonarr series to one Kodi show. The
  other 27 comprise 22 absent Kodi TVDB IDs and five duplicated Kodi TVDB
  IDs. Fourteen have no media and need no Kodi view while remaining monitored;
  the other 13 contain 292 episode files, so publishing a partial replacement
  view would hide content. Kodi exposes no alternate
  provider ID in these show records; all show paths use the Jellyfin plugin
  item identifier. Six held titles match exactly once by title, but title
  alone is insufficient identity proof. A Jellyfin item-ID/provider-ID bridge
  or equivalent verified reconciliation is required before full publication.
  The pre-project `Media/data` ZFS snapshot contains all 4,329 current
  physical Archive TV file paths, including the two whose ARR `dateAdded`
  changed after 2026-11-04. Those two dates therefore do not prove new
  episodes; verified baseline membership keeps them eligible as legacy Archive
  files. Fourteen of 1,317 Current TV files are absent from that snapshot.
  A pure fail-closed TV plan now holds ambiguous series with media, skips
  monitored series without media, applies the youngest episode and exact
  5 GB rule per season, and refuses publication while any media-bearing series
  is held. Season 0 Specials are rendered explicitly. A read-only
  preview yielded 130 Current and 368 Archive season nodes, including five
  Specials nodes, across 183 matched media-bearing series; publication
  remained blocked by 13 held media-bearing series. Thirty-one synthetic
  media-lifecycle tests pass. The
  Radarr, Sonarr and Jellyfin containers, Kodi client and recovery snapshot
  were present; legacy cron jobs 4 and 6 remained disabled. No client menu,
  Jellyfin library, ARR record or media file changed.
- **2026-11-06 — Reversible oversized Archive sample:** after Jason approved
  the specific Forgejo push, the M1/optimizer-contract candidate reached
  Forgejo main and its GitHub mirror at `d5946684a1c3b0aa0f20b2f167b1b6d280719c4e`.
  Rechecked live state: Radarr, Sonarr and Jellyfin containers running; legacy
  cron jobs 4 and 6 disabled; `Media/data` recovery snapshot present. Of the
  six directly probeable oversized Archive MKVs, the smallest is 5.74 GB,
  106.9 minutes, 1080p SDR HEVC, with English six-channel E-AC-3 and one
  English SubRip stream. A 90-second software x265 sample was staged outside
  the libraries at 5.3 Mb/s nominal video bitrate. The output was 58,962,519
  bytes over 92.081 seconds, retained six-channel audio and the English
  subtitle, and decoded successfully. A 30-second aligned source/output SSIM
  check scored 0.980282. This single scene is not representative enough to
  infer full-film size or subjective quality; no source, ARR record, Jellyfin
  library or watch state was changed. The temporary sample was removed.
  Before any source replacement, test varied scenes, full-film size and
  subtitle content, assess picture and playback on AsterTV, take a fresh
  recovery checkpoint, then verify ARR continuity and rollback.
- **2026-11-06 — User correction and oversized Archive inventory:** Jason
  directed that every file already over 5 GB in Archive be evaluated for
  transcoding/compression; ARR dates can govern future transfers. The 19
  oversized Archive movies total 749,956,862,257 bytes and reach 93.4 GB
  individually. Aggregate formats: six MKV, six M2TS and seven ISO. The ISO
  files cannot be probed by ffprobe as video containers and require verified
  main-feature extraction before any encode. Of the 12 directly probeable
  files, four are HDR, six have English surround audio and six have English
  embedded subtitles; the probe found five English PGS and four English
  SubRip streams. The existing 1.9 GB compactor caps at 1080p and
  verifies neither complete English subtitle retention nor ARR continuity,
  so it remains disabled. No file was transcoded or moved. A fresh recovery
  checkpoint and single-file pilot are required before replacement.
- **2026-11-06 — Undeployed optimizer acceptance contract:** added a pure
  manifest comparison that rejects outputs over the exact 5 GB ceiling,
  unnecessary recompression of compliant sources, an unacceptable resolution
  or aspect change, HDR loss or invention, English 5.1 downmix, English audio
  loss, missing English/unknown subtitle tracks or flags, and changed sidecars.
  Dolby Vision profile 5 is held for a separate colour-safe path. Ten new
  synthetic tests pass, bringing the local media-lifecycle test count to 24.
  Decode spot checks, visual quality on AsterTV, subtitle content verification,
  ARR file-record continuity and fresh recovery checkpoints remain necessary
  before any source replacement. This contract has not been deployed.
- **2026-11-06 — M0 synchronized and M1 lab probe:** Jason approved the
  specific M0 evidence push. Forgejo had first advanced to unrelated brand
  documentation commit `d9fe346`; the media-only commit was rebased without
  conflict, pushed as `00fc34dba141c29c6b38f4a5bdb8a11b1c119c0e`, and
  both Forgejo and its GitHub mirror reported that exact SHA. On AsterTV
  Bedroom, a disposable Kodi smart-playlist pilot selected one Current movie
  and two seasons of one series through client-native rules. Read-only
  `Files.GetDirectory` returned one movie and 20/26 episodes for the two season
  lists. Every temporary playlist was removed, with no home-menu, library,
  watch-state or ARR mutation. An aggregate playlist referring to a nested
  season playlist returned zero items, so this alone does not establish a
  usable whole-library season view. M1 remains open. Kodi's official smart
  [playlist rules](https://kodi.wiki/view/Smart_playlists/Rules_and_groupings)
  support episode `tvshow` and `season` filters, but
  its `match` mode combines rules only as all or one; further client design is
  needed for a union of exact eligible seasons.
- **2026-11-06 — M1 client-node feasibility:** a second disposable pilot on
  AsterTV Bedroom used Kodi video nodes instead of an aggregate smart
  playlist. A nested `Archive TV` → `Series` → `Season` hierarchy returned
  one series folder, two season folders and the same 20/26 episode counts
  through the client's own read-only JSON-RPC directory API. The node files
  were automatically removed; the home menu, Kodi database, Jellyfin, ARR
  records, media and watch state were not edited. This supports a generated
  client presentation over two ARR-managed physical roots. It does not yet
  prove the four-calendar-month eligibility calculation, the 5 GB ceiling,
  Jellyfin-web presentation or visual navigation on the TV. The next pilot
  must use real ARR import dates and checked file sizes, then verify the
  displayed Current and Archive paths on the client. Kodi's
  [video-node format](https://kodi.wiki/view/Video_nodes) documents the
  nested folder structure used here.
- **2026-11-06 — M1 policy candidate:** Jason chose to keep older low-resolution
  titles visible in Archive while seeking upgrades. Added pure, undeployed
  age-and-size and Kodi TV-node renderers under `scripts/video-archiver` with
  fourteen synthetic tests. The policy uses four calendar months, the exact
  5,000,000,000-byte ceiling, the youngest first-seen import in a TV season,
  and fails closed on missing
  time or size. Tests cover month-end rollover, size boundary and a new
  episode resetting only its own season, a grandfathered legacy Archive
  title and a new episode resetting a grandfathered season. The node tests
  validate a series split across Current and Archive seasons, XML escaping
  and ambiguous-title rejection. All fourteen tests pass. Stream quality
  and subtitle acceptance remain independent gates for new encodes. This
  code does not move, rewrite, tag or schedule any media.
- **2026-11-06 — Import-time provenance risk:** Radarr has 821 movie files and
  Sonarr has 5,646 episode files; all expose `dateAdded`, size and the fields
  needed for season grouping. But every recorded `dateAdded` falls in
  August–November 2026 after the ARR/Jellyfin migration. A direct four-month
  rule therefore classifies **zero** movies and **zero** of 535 seasons as
  Archive, despite 742 movies and 4,329 episode files currently living in
  physical Archive roots. The existing Archive roots provide a one-time
  provenance baseline: 723 of those movies and 394 whole seasons are at or
  below the 5,000,000,000-byte ceiling. Nineteen movies already in the
  physical Archive exceed the ceiling and must be treated as Current view
  exceptions until a safe optimization or accepted resolution. No series has
  files split across Current and Archive physical roots. The policy candidate
  retains a separate legacy-Archive flag instead of falsifying the import
  time. A new episode in such a season resets only that season's view age.
  The baseline and replacement ledger need to be persisted and verified
  before any bulk view migration; this read-only count does not authorize one.
- **2026-11-06 — Live import drift since Stream A start:** 31 movie files were
  newly imported into the physical Archive Movies root, but none is a newly
  added Radarr movie record; these are upgrades of existing titles. Two of
  those new files exceed 5 GB. Sixteen TV episode files were newly imported,
  two of them into the physical Archive TV root within one season. A legacy
  Archive flag should persist for an upgraded movie, while a new episode
  must make its own season Current for four calendar months. The existing
  physical Jellyfin libraries cannot express those exceptions; this is a
  current view-drift risk, not evidence that the old archiver jobs restarted.
  No media or ARR record was changed by this inspection.
- **2026-11-06 — ARR-to-Kodi identity check:** AsterTV Bedroom exposes TVDB
  IDs for 213 of 217 Kodi show entries and IMDb IDs for 1,055 of 1,067 movie
  entries. Five TVDB and eight IMDb IDs occur more than once in the Kodi
  library. Provider IDs can anchor a safer match than display title for most
  entries, but missing and duplicate IDs must fail closed during the pilot;
  a title-only bulk join could classify the wrong media. No Kodi record was
  edited.
- **2026-11-06 — M0 gate passed:** Forgejo main was still at the planning SHA
  at gate time;
  TrueNAS confirms legacy jobs 4 and 6 still disabled, with Radarr, Sonarr,
  Bazarr and Profilarr healthy and Jellyfin running. AsterTV Bedroom's installed
  Aster skin has four separate home playlists: TV Shows, Movies, Archive TV
  and Archive Movies. They filter Kodi library tags inherited from the four
  current Jellyfin libraries. Kodi's read-only API counted 83 Current shows,
  134 Archive shows, 80 Current movies and 987 Archive movies. This proves the
  actual client displays separate views today. The same Kodi 22 schema has a
  `tag` field for shows but no episode-level `tag` setter, so a four-month
  season-level virtual view needs a different client representation or a
  Jellyfin collection/plugin pilot; simply retagging whole series would not
  satisfy the season rule. M0 ownership and recovery questions are resolved
  sufficiently for a bounded M1 lab pilot. No media, ARR profile, Jellyfin
  library or Kodi setting changed during this gate. Local commit and remote
  synchronization are recorded separately; Forgejo push still needs immediate
  approval under `AGENTS.md`.
- **2026-11-05 — M0 resume:** Forgejo `main` still points to planning commit
  `67efb28b015630a8ce3b3baf9b612c17bb719fe7`; local M0 evidence remains
  unpushed. TrueNAS confirmed both old cron jobs disabled. Radarr, Sonarr,
  Bazarr and Profilarr were healthy; Jellyfin was running but had restarted
  within the preceding five hours. The three unmonitored Radarr entries all
  lack files and are in the Current root; none is a playable file that was
  accidentally left unmonitored. Sonarr now reports 5,634 episode files, two
  more than the prior baseline. Jellyfin's six configured libraries remain
  Movies, Shows, Music, Archive Movies, Archive TV and Collections. Separate
  AsterTV/Jellyfin checkpoint activity was observed, so changes to Jellyfin
  views need coordination with that concurrent work. No profile, media or
  Jellyfin change was made during this check.
- **2026-11-05 — AsterTV Bedroom read-only check:** the client at
  `192.168.1.140` is reachable over established SSH and Kodi 22.0 RC1 responds
  to its local TCP JSON-RPC endpoint. Its video library reports 1,065 movies
  and 6,313 episodes. This establishes a usable lab client for the view pilot,
  but library counts do not prove that Current and Archive appear as distinct
  household views. The client was not navigated or changed.
- **2026-11-04 — M0 started and legacy rewrite jobs paused:** the start gate
  had passed before live access. Forgejo `main` remained at planning commit
  `67efb28b015630a8ce3b3baf9b612c17bb719fe7`; local checkout was clean.
  TrueNAS clock showed MST (`-07:00`), one hour ahead of Vancouver PST. The
  age-based archiver cron job 4 (01:30, Mon–Sat) processed zero items in its
  latest run. The archive compactor cron job 6 (08:00 daily) had replaced three
  files on 2026-11-03, reducing 11,347,356,468 bytes to 4,464,060,680 bytes
  under the superseded ~1.9 GB-per-file target and `--no-snapshot` policy.
  Disabled job 6 before its 08:00 TrueNAS run and job 4 afterward; verified
  both `enabled=false` and no helper process active. These reversible schedule
  changes prevent further legacy media rewrites while the replacement policy
  is built. Do not re-enable either job under its old settings.
- **2026-11-04 — ARR baseline:** Radarr 6.4.4.10685 has 954 movies, 951
  monitored, 819 with files and 132 monitored/missing. Sonarr 4.0.20.3014 has
  223 monitored series and 5,632 episode files. Both still register Current
  and Archive roots. Every listed quality profile has `upgradeAllowed=false`,
  contrary to the desired upgrade policy. Three Radarr titles are unmonitored;
  their reason must be reviewed before changing them. No mass search or
  profile mutation occurred.
- **2026-11-04 — Recovery baseline:** the daily `Media@auto` snapshot does not
  cover the child `Media/data` dataset. Existing Radarr/Sonarr built-in backups
  were dated 2026-11-02. Created and verified fresh named ZFS snapshots of
  `Media/data`, `Media/appdata/jellyfin`, and `Media/ix-apps/docker` at 08:10
  TrueNAS time. Verified isolated temporary restores of a Radarr config file,
  a Jellyfin config file and a complete media subtitle sidecar by byte
  comparison; no restored file was put back into production. A client-visible
  Jellyfin pilot remains open before any media replacement.
- **2026-11-04 — Read-only stream sample:** Radarr reports 83 movie files over
  5,000,000,000 bytes. Of these, 28 are labeled 1080p remux, 25 1080p WEBDL,
  19 BR-DISK, seven 1080p Blu-ray, three unknown and one 2160p WEBDL. This
  disproves the assumption that oversized files are only 4K Blu-ray rips.
  A sampled 20.1 GB 4K HDR file has PQ/BT.2020 and English 5.1 audio but no
  English subtitle stream or sidecar. A sampled 44.8 GB 1080p remux has
  multiple English audio tracks and English PGS tracks including forced; the
  optimizer must retain those PGS tracks and flags in a compatible container.
  A sampled ~2.0 GB SD file has 720×404 video, stereo audio and no subtitles;
  it remains playable pending a genuine upgrade. No file was modified.
- **2026-11-02 — Planning and authorization:** inspected the helper code,
  portfolio and `Project-Creation-Standard.md`; cloned Forgejo main for this
  planning commit. Jason authorized Stream A completion with a hard execution
  start gate of 2026-11-04 01:00 America/Vancouver. TrueNAS remained
  unreachable from this workspace. No production change. Next safe action
  after the start gate: perform M0 from a HomeLab workspace with read-only
  lab access, then verify the live risk controls before any mutation.

## Open decisions and blockers

- Live TrueNAS access is available through an approved SSH path. The legacy
  rewrite schedules are disabled; this is the only live configuration change
  so far. Fresh snapshots and proportional isolated restore proofs exist.
- M1 must prove a season-level Current/Archive client representation without
  disturbing concurrent AsterTV/Jellyfin work. Kodi's existing tag-based
  show playlists cannot split one series by season because its episode API
  has no tag setter. A disposable per-season playlist worked on AsterTV
  Bedroom, while a playlist-of-playlists aggregator did not; the full view
  and four-month eligibility calculation remain unproven. The full-inventory
  preview matches 196 of 223 Sonarr series and refuses publication until 13
  media-bearing identity mismatches are reconciled through Jellyfin item IDs
  or other verified evidence. Profile design
  must resolve ARR's disabled upgrades;
  the three unmonitored movies are missing files, not playable archive files.
  No media file or ARR profile has been changed yet.
- Nineteen existing Archive movie files exceed 5 GB and are now an explicit
  optimization backlog, including seven ISO disc images requiring main-feature
  extraction. The old compactor cannot meet the new quality and subtitle
  safeguards. A single-file optimizer pilot and a fresh checkpoint precede
  any bulk processing; failures remain playable as Current exceptions.
- M0 evidence is synchronized to Forgejo and its GitHub mirror at `00fc34d`.
  The M1/optimizer-contract candidate was subsequently synchronized at
  `d594668` by a separate user-approved push. This latest sample evidence is
  local only. Repository instructions require immediate authorization for each
  further Forgejo push.
- The user wants the best file below 5 GB, with no compression solely to minimize size. They authorize a good 1080p version when 4K cannot meet the ceiling. The user prefers moving whole seasons after their youngest episode reaches four months, or keeping only two physical folders with separate Current/Archive views; the latter is recommended pending a Jellyfin client pilot.

## Close-out

Open. Record final architecture, owner, recovery references and deferred work
after graduation.
