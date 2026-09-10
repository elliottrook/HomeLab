# Media Archive Backup to Synology

> Status: **Declined 2026-09-10 — not proceeding.** Jason decided not to
> back up the media archive. Kept as a scoping record in case this is
> revisited later, not an active or queued project.
>
> Project owner: Jason
>
> Last updated: 2026-09-10

## Purpose

Back up TrueNAS's `archive-movies` and `archive-tv` datasets (the
downconverted, long-term media archive produced by the
[Video Library Archiving project](Video-Library-Archiving.md)) to the main
Synology (`gowest`, `192.168.20.41`), giving this media a second copy on a
separate physical device without relying on IDrive e2 capacity or cost.

## Why this exists

`archive-movies` and `archive-tv` currently exist only on TrueNAS's `Media`
pool — a single copy, protected by that pool's own RAIDZ2 redundancy against
a *disk* failure, but not against pool-level corruption, an operator
mistake, or loss of the pool itself. Unlike the family documents/config data
`Backup-Architecture-Redesign.md` protects, this data is:

- **Large** — 5.6 TB combined today (2.2 TB movies, 3.4 TB TV) and growing,
  since the archiving project continuously ages more current-library
  content into these roots.
- **Not irreplaceable in the same sense** as family photos or documents —
  most of it could in principle be re-acquired or re-downconverted — but
  represents real, deliberate work (encoding time, curation) that Jason
  wants protected rather than redone.
- **Explicitly excluded from the encrypted IDrive e2 relay** by that
  project's own documented policy ("Frigate recordings, media libraries and
  unrelated NAS data are excluded" — see `docs/05-Backups.md`), both for
  cost (IDrive e2 capacity/egress) and because off-site protection isn't
  proportionate to this data's replaceability.

A same-site, second-device copy is the right tier of protection for this
data — better than nothing, cheaper and simpler than off-site, and gowest
has the headroom for it today.

## Relationship to `Backup-Architecture-Redesign.md` — read this before building anything

This project's direction is the **reverse** of every leg in the sibling
redesign project, and appears to directly contradict one of its explicit,
deliberate architecture decisions:

> "`gowest` is a source, never a destination. No backup data lands on
> either Synology going forward."

That decision existed to eliminate a real, diagnosed problem: **Hyper
Backup's own dedup/compression/encryption processing** — not the Synology
hardware itself, and not "being a destination" in the abstract — was what
destabilized the Backup Synology (starved at 484 MB RAM) and was suspected
to strain `gowest` too when both units ran Hyper Backup simultaneously.

**This project proposes resolving the tension, not overriding the
decision:** use plain `rsync`, the same mechanism already proven stable on
this hardware for months and reused successfully by every leg of the
redesign, and never Hyper Backup, for this new leg. If that holds, `gowest`
becomes a destination for exactly one thing — a large, mostly-static,
already-downconverted media mirror with no versioning/dedup workload — a
categorically different load profile than what actually caused the original
instability. This is a design proposal for Jason to confirm, not a
unilateral reinterpretation of the redesign's decision: **do not build this
without that confirmation**, since it does touch a rule that project stated
in writing.

If Jason prefers to keep `gowest` strictly source-only regardless of
mechanism, the alternative is a fourth TrueNAS-side destination (e.g. a
second on-TrueNAS dataset/pool, if one existed) or accepting single-copy
protection for this data — both are reasonable positions this document does
not presume to override.

## Authoritative baseline (live, 2026-09-10)

- `archive-movies`: 2.2 TB (`/mnt/Media/data/archive-movies` on TrueNAS).
- `archive-tv`: 3.4 TB (`/mnt/Media/data/archive-tv` on TrueNAS).
- TrueNAS `Media` pool: 21.8 TB total, 17.0 TB allocated (**77% used**, 4.82
  TB free) — comfortable to read from, but this pool is not itself loose on
  space; worth keeping in mind for any future TrueNAS-side growth, though
  irrelevant to this project since TrueNAS is a read-only source here.
- `gowest` (`/volume1`): 11 TB total, 1.4 TB used, **9.1 TB free (14% used)**
  — comfortably fits 5.6 TB today, with headroom to spare as the archive
  grows, but growth rate isn't yet quantified (see Milestone 1).
- `gowest` already hosts real production data (Synology Drive, Immich,
  and whatever Milestone 6 of `Backup-Synology-Decommission.md` eventually
  decides about family-cloud placement) — this project's write footprint
  should be sized and monitored against that shared capacity, not treated
  as if `gowest` were empty.

## Architecture decisions (proposed)

- **Plain `rsync`, never Hyper Backup** — see the tension section above.
  This is the load-bearing decision the whole proposal rests on.
- **Avoid DSM's SSH-transport `rsync` server entirely, not just Hyper
  Backup.** The `gowest`-homes leg of the redesign project already hit a
  wall here from the *other* direction: DSM's own `rsync` binary, invoked
  in server mode over plain SSH exec (regardless of push or pull), refused
  with an undocumented daemon-style module-permission error, and no
  amount of account/permission fixing worked around it — the pivot that
  actually worked was NFS export + a plain local `rsync` cron job on the
  *other* end. The same obstacle should be expected here since it's the
  same DSM `rsync` binary on the same host, just now needing to *receive*
  instead of send. Proposed mechanism, mirroring that precedent: `gowest`
  exposes a share (SMB, matching the pattern just proven for the Home
  Assistant redirect, or NFS, matching the pattern proven for the
  `gowest`-homes leg — Milestone 1 should pick one, not assume) that
  TrueNAS mounts read/write, with a local `rsync` cron job on **TrueNAS**
  doing the actual copy — TrueNAS already runs the other three cron/rsync
  legs, so this keeps the automation on the side of the architecture
  that's proven to work, rather than trying to make DSM the active side
  again.
- **Dedicated, narrowly-scoped account on `gowest` for this one
  destination folder** — matching every other credential in this repo's
  backup pipeline (`homelab-backup`, `truenas-pull`, `ha-backup`), not a
  reuse of an administrative account.
- **One-way, TrueNAS → `gowest` only.** `gowest` never becomes a source for
  this data; the archive roots are read-only from `gowest`'s perspective.
- **No versioning/retention beyond a plain mirror**, at least initially —
  this data doesn't need multi-version rollback the way family documents
  do (a downconverted file doesn't get incrementally edited); a corrupted
  or deleted source file should be caught by monitoring and re-synced or
  re-downconverted, not recovered from history. Revisit only if a real
  need for versioning surfaces.
- **Doctor coverage and failure-only alerting** from day one, matching
  every other leg — a silent stall here is exactly the kind of gap this
  repo's own history (the AP Switch outage, `Media Backup`'s six quiet
  days) keeps finding the hard way.

## Scope

- Confirm the mechanism (SMB vs NFS export from `gowest`) and the
  destination folder/share name.
- Create a dedicated `gowest` account and share, scoped to only this
  destination path.
- Configure a TrueNAS-side cron job (matching the `gowest`-homes leg's
  pattern) to mirror `archive-movies` and `archive-tv` into it.
- Measure actual growth rate over a representative period (the archiving
  project runs Mon–Sat at 01:30) before treating today's 9.1 TB of gowest
  headroom as a long-term planning number.
- Add Doctor coverage (freshness + a repeat of the file-mtime lesson
  learned on `check_backup_redesign_truenas` — use job/marker-based
  freshness, not raw file mtime, since a quiet archiving day would
  otherwise look identical to a broken sync).
- Validate with a real restore test (recover a file from the `gowest` copy,
  verify it byte-matches the TrueNAS source) before considering this
  leg complete.

## Out of scope

- Any change to the Video Library Archiving project's own downconversion
  logic, schedule, or age thresholds.
- Off-site protection for this data — explicitly and deliberately excluded,
  per the existing IDrive e2 media-exclusion policy.
- Frigate recordings or any other media library not covered by
  `archive-movies`/`archive-tv`.
- Deciding Immich/family-cloud placement on `gowest`
  (`Backup-Synology-Decommission.md` Milestone 6) — this project should be
  sized with that still-open question in mind, not resolve it.

## Milestone 1 — Discovery and mechanism decision

- [ ] Get Jason's explicit confirmation on the core proposal (plain rsync
      to `gowest`, resolving rather than overriding the source-only
      decision) before any configuration work begins.
- [ ] Decide SMB vs NFS for the `gowest`-side share, based on which proves
      as reliable as its precedent when actually tried.
- [ ] Measure `archive-movies`/`archive-tv` growth over at least one week
      of real archiving-project activity, not assumed from today's
      snapshot.
- [ ] Confirm `gowest`'s other production workloads' headroom needs before
      committing capacity to this project.
- [ ] Design the dedicated account/share and its permission scope.

### Gate

Do not create any account, share, or scheduled job on either host until
Jason has explicitly confirmed the core proposal above in writing here.

**Gate not passed — project declined instead.** Jason decided 2026-09-10
not to back up the media archive at all, rather than confirming or
rejecting the specific gowest-as-destination proposal above. No account,
share, or scheduled job was ever created; `archive-movies` and
`archive-tv` remain single-copy on TrueNAS, protected only by that pool's
own RAIDZ2 redundancy, matching the accepted-risk framing already
documented for other media in `docs/05-Backups.md`. Revisit this document
if that decision changes.
