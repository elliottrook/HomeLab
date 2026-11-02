# Aster media lifecycle redesign

> Status: Ready — planning record only; implementation starts no earlier than
> Wednesday 2026-11-04 01:00 America/Vancouver (PST)
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
- Prefer genuine 1080p, HDR and 5.1 audio for new acquisitions. Do not manufacture HDR or surround sound by upscaling or upmixing older sources.
- Retain Current and Archive views in Jellyfin. Preferred layout: one physical `tv` root and one physical `movies` root, with age-based views rather than file moves. This needs a client-specific view pilot before migration.
- Preserve genuine HDR and a usable 5.1 track when compressing. Preserve 4K if it remains visually sound under the limit; if it cannot, a good 1080p version is authorized. Never upscale or upmix an older source.
- Retain every English subtitle track, including forced and SDH variants, and any external English subtitle sidecar. Preserve language, forced and hearing-impaired flags. If a subtitle cannot be retained in the output container, fail the encode and report it; do not silently retry without subtitles or delete the source.
- Treat 5,000,000,000 bytes per file as an Archive ceiling, not an encoding target. Do not recompress a compliant file just to make it smaller. With virtual views, oversized files stay in Current even after four months.
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
4. Keep files in the two arr-managed roots and calculate archive status from the original import date, not filesystem modification time. For TV, the youngest episode in a season must be at least four months old before that season can be called Archive; a later episode resets only its own season. If exact rolling views are needed inside Jellyfin, pilot API-managed collections or tags and verify their presentation on the actual client. Jellyfin's ordinary Latest Media view is useful but does not enforce the four-month rule.
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
their backups. Current versions, job health, free space, exact mounts,
credentials, backup status and household client behavior are unverified.
Stream A is authorized for the bounded scope above from the scheduled start;
the live M0 assessment must resolve these unknowns before any production
mutation. The non-waivable stop conditions still apply.

## Persistence and resume plan

Use a versioned bounded state file recording source identity, original import
time, stream manifest, candidate output, verification and acceptance. Keep
partial output outside Jellyfin libraries; use a lock, atomic acceptance,
timeouts and idempotent resume. Persist no keys or raw private output. On
resumption reread this project, Git status and live state before replay.

## Milestones and completion gates

- [ ] **M0 — Live discovery and risk acceptance:** inspect arr profiles, roots,
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

- **2026-11-02 — Planning and authorization:** inspected the helper code,
  portfolio and `Project-Creation-Standard.md`; cloned Forgejo main for this
  planning commit. Jason authorized Stream A completion with a hard execution
  start gate of 2026-11-04 01:00 America/Vancouver. TrueNAS remained
  unreachable from this workspace. No production change. Next safe action
  after the start gate: perform M0 from a HomeLab workspace with read-only
  lab access, then verify the live risk controls before any mutation.

## Open decisions and blockers

- This Codex workspace cannot reach `ssh truenas` (`Operation not permitted`), so live arr settings and job health have not been inspected.
- The project plan is being prepared in a fresh Forgejo clone; no production code or configuration has been changed.
- The user wants the best file below 5 GB, with no compression solely to minimize size. They authorize a good 1080p version when 4K cannot meet the ceiling. The user prefers moving whole seasons after their youngest episode reaches four months, or keeping only two physical folders with separate Current/Archive views; the latter is recommended pending a Jellyfin client pilot.

## Close-out

Open. Record final architecture, owner, recovery references and deferred work
after graduation.
