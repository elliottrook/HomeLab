# Video Duplicate/Quality-Upgrade Finder Project

> Status: Proposed — not yet authorized
>
> Project owner: Jason
>
> Proposed: 2026-09-15
>
> Authorization stream: not yet selected — Stream M or Stream A to be chosen by
> Jason before implementation begins

## Purpose and desired outcome

Identify movie/TV titles in the Movies/Shows/Archive Movies/Archive TV
libraries where a low-bitrate, SD, or otherwise degraded copy exists
alongside — or instead of — a healthier release (higher bitrate, higher
resolution, remux/4K), and produce a reviewable report so Jason can decide
whether to request a quality-upgrade acquisition. This is a
**quality-upgrade finder**, not a duplicate-file finder: the problem it
targets is "we're holding onto a worse copy of a title than we could have,"
not "we accidentally filed the same file twice."

## Relationship to Jellyfin-Library-Integrity-Automation — read this first

[Jellyfin-Library-Integrity-Automation.md](completed%20projects/Jellyfin-Library-Integrity-Automation.md)
already built and validated a duplicate/gap-fill detector, and its own
"Out of scope" section states, verbatim:

> Movie/TV folder-structure or duplicate-file detection — no such problem has
> actually been observed in Archive Movies, Archive TV, Movies, or Shows;
> inventing a speculative check for a problem that hasn't occurred is
> explicitly against this project's own stated design principle.

That project's whole design principle, stated in its Purpose section, is:
**"This project does not invent new checks speculatively. Every detector it
implements corresponds to a problem that was actually found and fixed by hand
first."** No movie/TV duplicate problem has been found and fixed by hand in
this lab. This proposal is, in plain terms, exactly the kind of speculative
check that sibling project's design principle says not to build.

**This charter does not pretend otherwise.** It exists because a
quality-upgrade finder is arguably a different, more useful problem than the
one that project solved (accidental duplicate album filing in a
Lidarr-managed library), for reasons specific to how movies/TV are acquired
in this lab:

- Movies and TV are acquired opportunistically over time via Radarr/Sonarr
  from whatever release is available at request time. A title requested
  early (before a `REMUX`/`4K`/well-encoded release existed) can sit
  indefinitely at a lower quality than what's now obtainable, with nothing
  in the current pipeline ever re-checking it — Radarr/Sonarr's own upgrade
  logic ([ARR-Stack-Operational-Reference.md](../reference/ARR-Stack-Operational-Reference.md))
  only fires on a **quality profile cutoff**, which is a per-title,
  human-configured setting, not a library-wide sweep for "is something
  measurably better available now."
- This is structurally different from the music library's accidental-filing
  problem (same content, filed twice by folder-scatter or import mistakes) —
  here every "duplicate" candidate is, by construction, two *different*
  encodes of the same title, and the interesting output is a quality
  comparison and upgrade recommendation, not a delete decision.
- Video-Library-Archiving already proves the opposite failure mode exists in
  this exact library set: it found "a pre-existing duplicate of Shawshank (a
  loose 2020 file from the original Plex migration) already sitting in
  `archive-movies`" as an incidental discovery during its own unattended run
  ([Video-Library-Archiving.md](<completed projects/Video-Library-Archiving.md>)
  Evidence log, 2026-08-08/09 entry), flagged there as "a future cleanup, not
  a video-archiver bug." That is one real, observed instance of exactly the
  duplicate-file class of problem in this library set — not zero evidence,
  though not a systematic finding either.

That said, this is **one incidentally-found duplicate, not a measured,
library-wide problem.** Unlike the music-library detector — which formalized
checks that had already found and fixed 271 orphans, 79 scatter candidates,
and multiple real duplicate pairs by hand before any code was written — this
project has no comparable evidence base. **Jason's explicit buy-in that the
problem is real and worth building for is required before Milestone 1
begins**, and Milestone 1 itself should be a measurement pass (how many
candidates actually exist) before any remediation logic is written, so that
buy-in is based on a real number rather than a guess.

## Current state and evidence

- No duplicate/quality-detection tooling exists for movies/TV. Jellyfin-
  Library-Integrity-Automation's `lib/duplicates.py` exists only for the
  Music library and is explicitly out of scope for reuse here without
  substantial redesign — see Scope below for why the logic itself doesn't
  transfer directly.
- Library roots (confirmed via `docs/04-Operations.md`):

  | Library | Path | Managed by |
  |---|---|---|
  | Movies (current) | `/mnt/Media/data/media/movies` | Radarr |
  | Shows (current) | `/mnt/Media/data/media/tv` | Sonarr |
  | Archive Movies | `/mnt/Media/data/archive-movies` | Not ARR-managed (former Plex library) |
  | Archive TV | `/mnt/Media/data/archive-tv` | Not ARR-managed (former Plex library) |

- Radarr/Sonarr each expose file-quality metadata (resolution, codec,
  quality profile, `mediaInfo` bitrate/video codec) through their APIs,
  already used read-only by this session's Aster ARR-manager work and by
  Video-Library-Archiving's own `Probe`/candidate logic
  ([ARR-Stack-Operational-Reference.md](../reference/ARR-Stack-Operational-Reference.md)).
  This is the natural source of quality facts for the current-library half
  of this project's scope.
- Archive Movies/Archive TV are **not** tracked by Radarr/Sonarr at all (they
  predate the ARR-managed current library and were migrated wholesale from
  Plex). Quality facts for those two roots would have to come from directly
  probing the files (`ffprobe`, already trusted and installed via the
  Jellyfin container per Video-Library-Archiving) rather than an ARR API.
- Video-Library-Archiving already runs a GPU-accelerated transcode job
  Mon–Sat 01:30 against `/mnt/Media/data/media/{movies,tv}` on TrueNAS's
  Intel Arc A380 (via the Jellyfin container) — any new scheduled job
  touching the same paths must not compete with that window for I/O or GPU.
  Jellyfin-Library-Integrity-Automation already occupies Wednesday 03:00 for
  its own (Music-only) library scan.
- Video-Library-Archiving's architecture explicitly favors **no per-batch
  human approval queue for reversible, non-destructive actions**, but
  **does** require human approval for irreversible actions — see that
  project's Architecture decisions ("Fully unattended once trusted, but not
  on day one of deployment"). Jellyfin-Library-Integrity-Automation went
  further for its one irreversible action class (duplicate album deletion):
  detection runs unattended, but deletion is **never** automatic — only a
  reviewable report is produced, and a human approves an exact dated report
  before anything is deleted. This project's own irreversible action
  (deleting/replacing a lower-quality file) is at least as consequential as
  that precedent, arguably more so given movies/TV files are far larger and
  not proactively refetched the way a Lidarr-managed album might be — so it
  adopts the same never-auto-delete rule (see Architecture below).

## Scope

- Scan the current Movies/Shows libraries (via Radarr/Sonarr's own quality
  metadata — resolution, video codec, source type/edition tag, and file
  size/bitrate) for titles where a measurably better release is verifiably
  obtainable — not merely "this file is small," but "this file is
  measurably below what this exact title is now available at" (see
  Architecture below for how "measurably better" is defined and how
  overreach is avoided).
- Scan Archive Movies/Archive TV (via direct file probing, since they are
  outside ARR's authority) for the same signal, understanding these are
  post-archival by design — a file in Archive Movies is *expected* to be
  Video-Library-Archiving's downconverted 1-2GB output, not a quality
  problem. This project's Archive-library check is therefore narrower: it
  looks only for the pre-existing-accidental-duplicate class (two different
  files for the same title, one clearly redundant/lower-quality, in the same
  root) — the same class the Shawshank incidental finding represents — not
  "should this archived copy be upgraded," which would directly conflict
  with Video-Library-Archiving's whole purpose of intentionally trading
  quality for space in that root.
- Produce a dated, human-readable report (matching the
  `video-archiver`/`jellyfin-integrity` `reports/` convention) listing each
  candidate with real evidence: current resolution/codec/size, the specific
  better release identified and how it was identified, and — for the
  Archive-library duplicate check — a same-title match confirmed by
  Radarr/Sonarr's own unique identifiers (TMDB/TVDB id), not filename
  fuzzy-matching alone.
- Nothing in this project ever deletes, moves, or replaces a file
  automatically. All output is a reviewable report; any actual upgrade
  acquisition remains a human (or separately-authorized Seerr/Radarr/Sonarr)
  decision.

## Out of scope

- Automatically deleting, replacing, or re-acquiring any file. This project
  produces a report; it does not integrate with Radarr's/Sonarr's search or
  grab pipeline to fetch a replacement. (A follow-on project could propose
  that, with its own risk assessment — not this one.)
- Re-implementing or extending Jellyfin-Library-Integrity-Automation's
  Music-library duplicate detector against a different path. The evidence
  standard there (byte-level audio duration comparison between two files
  claiming to be the same album) doesn't transfer: a "quality-upgrade"
  candidate here is, by definition, two encodes with *different* runtimes
  measured in bitrate/resolution terms, not two files expected to be
  byte-for-byte/duration-identical. Building a new detector, not adapting the
  existing one, is required — and is exactly why this needs its own charter
  rather than a scope note in the sibling project.
- Any transcoding, downconversion, or re-encoding — that is exclusively
  Video-Library-Archiving's job.
- Competing with Video-Library-Archiving's Mon–Sat 01:30 window or
  Jellyfin-Library-Integrity-Automation's Wednesday 03:00 window for TrueNAS
  I/O or the Arc A380 GPU.
- Treating Archive Movies/Archive TV's intentionally-downconverted files as
  "quality problems" — that would misunderstand and undermine
  Video-Library-Archiving's entire purpose.
- A general library dashboard or UI. This is a scheduled backend check with
  a report, matching the sibling project's own explicit non-goal.
- Building this before Jason has confirmed the problem is worth solving —
  see the buy-in requirement above.

## Authority model

- Radarr/Sonarr remain authoritative for current-library file quality facts
  and for any future acquisition decision. This project only reads their
  APIs; it never writes.
- This project's own report is authoritative only for its own findings —
  it is evidence for a human decision, not itself an action.

## Architecture and data flows (proposed)

### Defining "measurably better" without over-triggering

The single hardest design problem here — and the reason this needs real
discussion rather than a straightforward port of the music logic — is
avoiding a flood of low-value false positives. A naive "flag anything under
1080p" check would likely flag a large fraction of an opportunistically-
acquired library and produce a report nobody can usefully act on. Proposed
approach, **not yet validated against real data**:

- Compare against Radarr's/Sonarr's own configured quality profile cutoff
  for that title, where set — a title already at or above its own configured
  cutoff is not a candidate, since Jason has already told the ARR stack what
  "good enough" means for it.
- For titles below cutoff, or with no meaningful cutoff configured, flag
  only where the gap is large by an explicit, tunable threshold (e.g., SD
  source with a widely-available HD/4K release, or a bitrate an order of
  magnitude below what the resolution would normally carry) — not a small
  bitrate difference between two reasonable encodes.
- Do not attempt to determine "is a better release actually available right
  now" by querying Prowlarr/indexers directly as part of the detection pass
  — that conflates a passive library-quality audit with an active search,
  which is a materially different (and more sensitive, indexer-facing)
  capability. This project reports "this file is below a healthy bar," not
  "here is the exact release to grab" — narrowing scope deliberately, per
  the least-privilege/minimum-change principle. A confirmed-available-upgrade
  check could be a scoped follow-on once the passive audit's actual
  usefulness is proven.

This narrows the project considerably relative to a naive read of "quality-
upgrade finder," and that narrowing is deliberate: it is easier to widen
scope later from a working, low-noise report than to walk back a
noisy one.

### Archive-library duplicate check

- Match candidates across Archive Movies/Archive TV and their current-library
  counterparts (Movies/Shows) using Radarr's/Sonarr's own TMDB/TVDB ids as
  the join key, not filename similarity — avoiding the kind of fuzzy-match
  false positive the music project explicitly guarded against
  (`Still Crazy After All These Years` looking like a duplicate by every
  filename signal but being a genuinely different master).
- Flag only same-title files that are redundant in the sense that one is
  clearly a strict subset/inferior copy of the other (matching
  Video-Library-Archiving's own "pre-existing duplicate of Shawshank"
  finding pattern) — not every title that happens to exist in both an
  archive and current root, since that's the expected steady state once
  Video-Library-Archiving ages a title out.

### Runs where, and on what schedule

- Following the `/mnt/Media/data/tools/` precedent (both
  `video-archiver` and `jellyfin-integrity` install there on TrueNAS), this
  tool's read-only scan is a natural fit for the same location — but its
  actual schedule must be chosen to avoid the two existing windows (Mon–Sat
  01:30 GPU transcode, Wednesday 03:00 music integrity scan). Proposed:
  a different night's early-morning slot, confirmed against TrueNAS's own
  scheduled-job table the same way Jellyfin-Library-Integrity-Automation
  checked before settling on Wednesday.
- Because Archive-library file probing (`ffprobe`) is read-only and
  comparatively cheap next to a transcode, this project's I/O footprint
  should be much lighter than either sibling job — but that assumption
  should be measured, not assumed, during Milestone 1.

## Privacy and security design

- Read-only against Radarr/Sonarr APIs and the filesystem; no write
  capability to any ARR API, and no filesystem write beyond this project's
  own `reports/` directory.
- A dedicated, least-privilege API key per ARR app (or reuse of an existing
  read-only key if one already exists for this purpose) — never a shared
  admin credential, matching the `jellyfin-integrity`/`jellyfin-integrity`
  key-per-service pattern.
- No content is sent anywhere off this network; reports stay local.
- Run logs/reports are retained outside Git (contain local paths and
  titles), matching existing convention.

## Pre-start risk assessment

- **Objective, scope, exclusions, stream:** as above. Recommend Stream M —
  this project has no prior validated evidence base (unlike its music
  sibling), so each step should be reviewed rather than pre-authorized in
  bulk, at least through Milestone 1's measurement.
- **Affected systems:** Radarr, Sonarr (read-only API), TrueNAS filesystem
  (read-only against Movies/Shows/Archive Movies/Archive TV).
- **Users/data:** Jason's movie/TV library metadata and quality facts only —
  no personal data beyond media titles already visible in Radarr/Sonarr.
- **Current versions/dependencies/known consumers:** Radarr 6.3.0.10514,
  Sonarr 4.0.19.2979 (per
  [ARR-Stack-Operational-Reference.md](../reference/ARR-Stack-Operational-Reference.md));
  no new dependency needed beyond `ffprobe`, already installed and trusted
  via the Jellyfin container.
- **Confidentiality/secret-handling risk:** low — same as sibling projects;
  new API keys are mode-600, not committed, and never echoed into logs.
- **Availability/integrity/privacy/recovery risk:** none from the detection
  pass itself (read-only). The real risk in this whole problem space is
  entirely in a *future* remediation step (deleting/replacing a file based on
  a false-positive "worse copy" judgment) — which is explicitly out of scope
  for this project. This charter's scope boundary is itself the primary risk
  control.
- **Irreversible/destructive operations:** none in this project's scope.
  Should a follow-on remediation project ever be proposed, it inherits the
  Jellyfin-Library-Integrity-Automation precedent: report-then-human-approval,
  never automatic deletion, and would need its own charter and its own
  pre-start risk assessment — not an extension bolted onto this one.
- **Expected auth/firewall/DNS/storage/external-service changes:** none.
- **Recovery checkpoint/rollback/abort:** not applicable — no state-changing
  action exists in this project's scope to roll back.
- **Test strategy:** validate the "measurably better" threshold logic against
  synthetic/known test cases first (a deliberately-SD file vs. a
  deliberately-4K file, a title already at cutoff, a title with no cutoff
  configured) before running against the real library, matching the sibling
  project's synthetic-fixture-then-real-dry-run gate.
- **Likely service interruption:** none expected — read-only API calls and
  file probes only.
- **Backup/Doctor/monitoring/NetBox/wiki/documentation impacts:** see
  integration checklist below.
- **Unresolved decisions requiring Jason's acceptance before Milestone 1:**
  1. **Whether this problem is real enough to build for at all** — the
     central buy-in question this charter cannot answer on its own, given
     the sibling project's explicit "don't invent speculative checks"
     principle and this project's thin evidence base (one incidental
     finding, not a measured pattern).
  2. The exact "measurably better" threshold definition (see Architecture) —
     needs to be tuned against real Radarr/Sonarr data, not assumed.
  3. Whether an active "is a better release actually obtainable right now"
     check (via Prowlarr/indexers) is ever wanted, given this charter
     deliberately excludes it from the first version.
  4. Scheduling window, once TrueNAS's current job table is re-checked.

## Persistence plan

- Per-title scan results recorded in a durable, schema-versioned state file
  so repeat runs can report new candidates versus previously-seen ones
  without needing to reprocess unchanged titles from scratch — mirroring
  Jellyfin-Library-Integrity-Automation's `reports/collections_baseline.json`
  pattern.

## Milestones

All unchecked — nothing has been built. **Milestone 1 requires Jason's
explicit buy-in before it begins**, per the buy-in requirement above.

### Milestone 0 — Buy-in checkpoint (gate before any code is written)

- [ ] Present this charter to Jason, including the explicit acknowledgment
  that this proposes exactly the kind of speculative check
  Jellyfin-Library-Integrity-Automation's own design principle argues
  against, and the quality-upgrade framing that distinguishes it.
- [ ] Get explicit confirmation the problem is worth measuring (not
  necessarily worth building the full remediation-adjacent tooling yet —
  just worth spending Milestone 1's measurement effort).

### Gate

Jason's explicit go-ahead to proceed to Milestone 1, recorded in this
document's evidence log.

### Milestone 1 — Measurement pass (read-only, no remediation logic yet)

- [ ] Query Radarr/Sonarr for every current-library title's quality profile,
  cutoff status, resolution, and file size/bitrate.
- [ ] Compute, using a first-draft "measurably better" threshold (see
  Architecture), how many titles would actually be flagged — the real
  number this charter cannot supply in advance.
- [ ] Separately scan Archive Movies/Archive TV against Movies/Shows via
  TMDB/TVDB id join to count real accidental-duplicate candidates (the
  Shawshank-pattern check).
- [ ] Present the real candidate counts and a sample of flagged titles to
  Jason before writing any further tooling — this is the evidence Milestone
  0's buy-in was necessarily provisional on.

### Gate

A real, measured candidate count exists (not a guess), and Jason confirms
the numbers justify continuing to a reportable tool, before Milestone 2.

### Milestone 2 — Reviewable report tool

- [ ] Build the read-only scanning tool producing a dated, human-readable
  report plus machine-readable JSON log, following the
  `video-archiver`/`jellyfin-integrity` `reports/` convention.
- [ ] Validate against synthetic/known test cases (see Pre-start risk
  assessment's test strategy) before trusting output against the real
  library.
- [ ] Run once, supervised, against the real library and have Jason review
  the actual report content for usefulness and false-positive rate.

### Gate

A supervised real run produces a report Jason judges low-noise and useful
enough to schedule.

### Milestone 3 — Scheduled unattended reporting

- [ ] Choose a schedule window confirmed not to conflict with
  Video-Library-Archiving (Mon–Sat 01:30) or Jellyfin-Library-Integrity-
  Automation (Wednesday 03:00).
- [ ] Install via TrueNAS-native Cron Job, matching existing precedent.
- [ ] Add a HomeLab Doctor check for run freshness/failure, matching the
  `check_video_archiver`/`check_jellyfin_integrity` pattern.

### Gate

At least one clean unattended run, reviewed, with no schedule conflict
observed.

### Milestone 4 — Documentation and closeout

- [ ] Record final tool location, schedule and report location in
  `docs/04-Operations.md`.
- [ ] Close out the integration impact checklist below with actual evidence.

## Validation plan

- Functional: synthetic known-good/known-bad test cases validate the
  threshold logic before real-library use; real-run report reviewed by Jason
  for actual usefulness, not just "it produced output."
- False-positive review: the Milestone 2 supervised run is explicitly a
  false-positive audit, given this project's thin prior evidence base —
  mirroring how the music duplicate detector's real dry run caught
  `Still Crazy After All These Years` as a false positive before trusting
  the detector further.
- Regression: confirm the tool makes zero write calls to Radarr/Sonarr and
  zero filesystem writes outside its own `reports/` directory (verifiable via
  a read-only test double or dry-run mode with write calls disabled/logged
  rather than executed).
- Performance: confirm the scan's I/O/API load doesn't measurably interfere
  with normal Radarr/Sonarr/Jellyfin operation or the two existing scheduled
  jobs.

## Observability and maintenance (integration impact checklist)

- **HomeLab Doctor** — add a check (e.g. `check_video_quality_finder`)
  reading the latest report for staleness/failure, matching existing
  `check_video_archiver`/`check_jellyfin_integrity` pattern.
- **Monitoring/alerting** — covered via HomeLab Doctor; no separate
  Prometheus/Grafana metric proposed given this is a low-frequency batch
  report, not a live service.
- **Backup and recovery** — not applicable with reason: the tool produces
  regenerable reports from live Radarr/Sonarr/filesystem state; no
  irreplaceable state exists to back up beyond the tool's own small config
  (API keys), which follows the existing mode-600/not-in-Git convention and
  can be added to the existing backup pipeline if non-trivial to recreate.
- **NetBox** — not applicable with reason: no new physical device or VM;
  this runs as a script under the existing `/mnt/Media/data/tools/`
  convention on TrueNAS, an already-inventoried host.
- **Human wiki** — add a short operator page once built, describing report
  location and how to read a flagged candidate.
- **Aster mirror/snapshot** — mirror this project document once accepted,
  non-authoritative, same as other project docs.
- **Operational reference and runbooks** — add to `docs/04-Operations.md`
  once implemented.
- **Repository documentation** — update this document's own status as
  milestones close; portfolio table maintained separately per this task's
  instructions.
- **Diagrams/rack records** — not applicable with reason: no physical or
  topology change.
- **Homepage/service discovery** — not applicable with reason: scheduled
  backend report tool, not an interactive service, matching sibling
  projects' own scoping.
- **Authentication/authorization** — least-privilege, read-only API keys per
  ARR app; no new admin credential.
- **DNS, certificates and firewall** — not applicable with reason: no new
  network-facing endpoint; runs against existing internal APIs already
  reachable from TrueNAS itself.
- **Automation and schedules** — TrueNAS-native Cron Job, scheduled to avoid
  the two existing library-maintenance windows, with a non-overlap lock
  matching sibling-project precedent.
- **Security inventory** — any new API key recorded the same way
  `jellyfin-integrity`'s key is; no secret ever appears in report content or
  log filenames.

## Evidence log

No implementation work has occurred; this document is the initial proposal.

## References

- [Jellyfin Library Integrity Automation — sibling project, its explicit out-of-scope statement and design principle this charter must reckon with](completed%20projects/Jellyfin-Library-Integrity-Automation.md)
- [Video Library Archiving — Shawshank incidental-duplicate finding, GPU/scheduling precedent to avoid colliding with](<completed projects/Video-Library-Archiving.md>)
- [ARR Stack Operational Reference — Radarr/Sonarr quality metadata and canonical library roots](../reference/ARR-Stack-Operational-Reference.md)
- [Plex-to-Jellyfin media migration — Archive Movies/Archive TV provenance](<completed projects/Plex-to-Jellyfin-Media-Migration.md>)
- [04-Operations.md — library paths and video-archiver operational details](../04-Operations.md)
- [HomeLab Project Creation Standard](../Project-Creation-Standard.md)
