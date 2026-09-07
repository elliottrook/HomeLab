# Jellyfin Library Integrity Automation Project

> Status: In progress — Milestones 1 and 2 complete, Milestone 3's unattended
> schedule is installed and running; awaiting two consecutive clean
> Wednesday runs before that milestone closes
>
> Project owner: Jason
>
> Last updated: 2026-09-07

## Purpose

Between 2026-09-06 and 2026-09-07, a series of real, previously-invisible
data-integrity problems were found and fixed by hand in the Jellyfin music
library: 271 orphaned tracks with no album container, a library-wide
featured-artist folder-scatter bug affecting 79 candidate albums (17
consolidated automatically, 13 real duplicate/gap-fill pairs resolved with
evidence, dozens of false positives correctly ruled out), missing album
art for 30 albums, and — separately — a Jellyfin built-in maintenance task
that silently deleted movie collections on two different server restarts.
Full history: [04-Operations.md](../04-Operations.md) ("Music must be
foldered by album" through "Jellyfin startup cleanup task is disabled").

Every one of those fixes was a one-off manual investigation. This project
turns the checks and remediation logic already developed and validated
against the real library into a **standing, scheduled program** — so the
same classes of problem are caught automatically going forward, on all
Jellyfin libraries, rather than only when something looks visibly wrong
enough for a human to go digging.

This project does not invent new checks speculatively. Every detector it
implements corresponds to a problem that was actually found and fixed by
hand first; there is no movie/TV-specific foldering or duplicate check
proposed here, because no such problem has actually been observed in those
libraries — only the collection-count regression class of issue, which
did affect them.

## Completion outcome

The project is complete only when:

- a tool exists that scans the Jellyfin Music library for orphaned tracks
  (no album container), featured-artist folder scatter, missing album art,
  and candidate duplicate/gap-fill album pairs, using the same evidence
  standard developed by hand (real track-duration comparison, not
  filename guessing) for anything that isn't purely additive;
- the tool separately checks collection and playlist counts against the
  last known-good run and against Plex's preserved source manifests, to
  catch a recurrence of the startup-task deletion class of issue on any
  Jellyfin library, not just music;
- every **safe, reversible, purely organizational** correction (foldering
  orphaned tracks, consolidating scattered album folders, extracting
  embedded album art) runs unattended and is logged;
- every **irreversible or judgment-dependent** correction (deleting a
  confirmed duplicate album, resolving an ambiguous edition-vs-duplicate
  case) is queued into a reviewable report instead of being applied
  automatically, and nothing in that queue is acted on until a human
  approves it — see Architecture decisions below for why this project
  does not follow Video-Library-Archiving's fully-unattended precedent for
  this specific category;
- the pipeline has been validated against a real, human-supervised run
  before being handed to the unattended Sunday 3am schedule; and
- the schedule, its resource limits, its logs, and its failure-reporting
  path are documented for ongoing operation.

## Authoritative baseline

Recorded 2026-09-07 from this session's own real, already-validated work
(no new discovery needed — this is a summary of what was already proven
against production):

- [x] Music library root: `/mnt/Media/data/media/music` (host path),
  Jellyfin library ID `7e64e319657a9516ec78490da03edccb`. 757 albums,
  8,185 tracks, 0 orphan tracks as of the last check this session.
- [x] Jellyfin creates one album entity per physical folder it scans —
  confirmed root cause of the featured-artist scatter bug. Tags alone
  never fix this; foldering does.
- [x] Lidarr manages most of this library (255 artists) at
  `/mnt/Media/data/media/music`. `renameTracks` and the Kodi/Emby metadata
  consumer are now both enabled (2026-09-06/07), verified via Lidarr's own
  `/rename` preview API against a real multi-artist track — future
  Lidarr-driven imports will not recreate the scatter problem. This
  project's detectors exist for content that predates that fix, or that
  arrives outside Lidarr's own pipeline (see 04-Operations.md).
- [x] Neither `ffprobe` nor `mutagen` currently exist on TrueNAS (both were
  removed with the Plex-to-Jellyfin migration's tool cleanup). This
  session wrote working from-scratch FLAC/MP3/M4A duration readers instead
  — validated against known-real tracks, with two real bugs caught and
  fixed before trusting results (sorted-duration misalignment; an MPEG
  Layer III/I frame-size formula mix-up). These become the starting point
  for this project's tooling rather than reintroducing an external
  dependency.
- [x] Jellyfin's `Clean up collections and playlists` scheduled task has
  its `StartupTrigger` cleared (2026-09-06) after it destroyed 73 then 71
  movie collections across two server restarts. The task still exists and
  could be re-triggered by a future config change or Jellyfin update —
  this project's collection-count check exists specifically to catch that
  if it ever happens again, independent of whether the trigger stays off.
- [x] Preserved migration manifests (`plex-movie-collections.json`,
  `plex-to-jellyfin-movie-map.json`) live in
  `~/lab/private-backups/plex-jellyfin-migration/` on the Mac, not on
  TrueNAS — they were the actual basis for both collection-recovery
  incidents. This project's collection-check needs read access to the same
  data; see Architecture decisions for where that lives going forward.
- [x] A dedicated, persistent Jellyfin API key (`jellyfin-integrity`) was
  created 2026-09-07 and stored in `config.json` (mode 600) on TrueNAS;
  the temporary key used for Milestone 1 testing was revoked immediately
  after (see Safety and credentials).
- [x] TrueNAS's Cron Job feature was tested and confirmed working for this
  tool 2026-09-07 (`midclt call cronjob.create`, id `2`).

## Architecture decisions

These are **proposed**, based on direct precedent from this session's
real work, and need Jason's confirmation before Milestone 1 begins —
unlike Video-Library-Archiving's decisions, these have not yet been
discussed and agreed.

### Safe corrections run unattended; irreversible ones don't

Video-Library-Archiving's own architecture note explicitly chose "no
per-batch human approval queue" for its transcode-and-archive pipeline,
because every step there is either non-destructive until a final verified
atomic move, or goes through Radarr/Sonarr's own authoritative delete API.

This project makes a **different** choice for one category only: deleting
a confirmed duplicate album. The evidence standard developed this session
(track-by-track duration matching) is strong, but it is not infallible —
*Still Crazy After All These Years* looked like a candidate duplicate by
every filename/folder signal and turned out to be a genuinely different
master (96kHz/24-bit vs 44.1kHz/16-bit), only caught because a human
looked at the actual comparison output before anything was deleted. An
unattended weekly job that deletes music autonomously on a false positive
is a real, not hypothetical, risk with this exact detector.

So: orphan-track foldering, scattered-album consolidation (moving files
within the library, never deleting), and embedded-art extraction all run
fully unattended, same philosophy as Video-Library-Archiving. Duplicate-
album detection also runs unattended, but only produces a dated report
with full evidence (track counts, per-track duration deltas, proposed
keeper/delete) for Jason to review; nothing is deleted until that report
is explicitly approved, at which point the tool applies exactly what was
reviewed — not a fresh re-scan that could pick up different candidates.

### Runs on TrueNAS, reusing this session's own validated code

The detectors and duration readers already exist, in scratchpad form, and
have been run against the real production library successfully. This
project formalizes them into an installed tool rather than rewriting from
a design spec — same precedent as Video-Library-Archiving reusing the
Plex migration's `ffmpeg` install instead of re-sourcing a new binary.

### Collection-count check needs the preserved manifests reachable from TrueNAS

The two collection-deletion incidents were only recoverable because the
Plex-to-Jellyfin migration's manifests were preserved outside Git, on the
Mac. A TrueNAS-resident scheduled job checking collection counts can
detect a drop, but cannot itself recover from one without those manifests
being reachable from TrueNAS too. **Confirmed by Jason and done 2026-09-07:** both manifests copied
read-only (mode 600) into `/mnt/Media/data/tools/jellyfin-integrity/reference/`
on TrueNAS, in addition to (not instead of) their existing home in
`~/lab/private-backups/`.

## Approved target layout

Proposed, following the `/mnt/Media/data/tools/` precedent Video-Library-
Archiving already established:

```text
/mnt/Media/data/
├── media/music/                       # Untouched except via this tool's
│                                       #   own safe-correction actions
└── tools/
    └── jellyfin-integrity/            # This project's self-contained install
        ├── check_integrity.py         # Main entry point
        ├── lib/
        │   ├── duration.py            # FLAC/MP3/M4A readers (from this session)
        │   ├── orphans.py             # Orphan-track detector + folderer
        │   ├── scatter.py             # Featured-artist scatter detector + consolidator
        │   ├── artwork.py             # Embedded-art extractor
        │   └── duplicates.py          # Duplicate/gap-fill detector (report-only)
        ├── reference/                 # Read-only copy of the two manifests above
        ├── reports/                   # Dated JSON + human-readable run reports
        └── config.json                # API keys (mode 600, outside Git)
```

## Scope

- Scan the Music library for tracks with no `AlbumId` (orphans) and
  auto-foldered them under `Artist/Album (Year)/`, using each track's own
  embedded `ALBUM` tag — the exact method validated this session.
- Scan for albums whose tracks are split across more than one physical
  folder that isn't a legitimate multi-disc pattern (`Disc N`, `CD NN`,
  `Vinyl NN`, `Digital Media NN`), using the same distinction logic
  validated this session (370-folder library scan, 117 candidates
  narrowed to 42 real stub folders + 14 stray `Compilations` tracks).
  Auto-consolidate confirmed stray/stub cases (small fragment into an
  obviously-larger real copy); queue anything ambiguous for review rather
  than guessing.
- Detect candidate duplicate albums and gap-fill cases via real per-track
  duration comparison (not filename or track-count matching alone).
  Auto-apply gap-fills (moving a uniquely-held track into an otherwise-
  complete copy — never deletes anything in this case). Queue confirmed
  duplicates for human-approved deletion.
- Extract embedded cover art into `cover.jpg`/`cover.png` for any album
  missing artwork, where at least one track carries embedded art.
- Check Jellyfin box-set and playlist counts against the previous run and
  flag a large unexplained drop (the startup-task-deletion signature) on
  **any** Jellyfin library, not just music.
- Verify Jellyfin's `Clean up collections and playlists` task's trigger
  configuration hasn't reverted to enabled (config-drift check, cheap to
  include given the API is already being called).
- Run every Wednesday at 03:00 via a TrueNAS-native Cron Job, logging a
  dated, human-readable report plus a machine-readable JSON log per run.
  (Originally proposed as Sunday 03:00; changed 2026-09-07 — Sunday
  carries the weekly ZFS scrub, which starts at 00:00 and historically
  finishes ~02:46, right up against that window, plus the daily 04:30
  backup-pull rsync. Wednesday avoids the scrub entirely.)

## Out of scope

- Any transcoding, downconversion, or re-encoding of media — that is
  Video-Library-Archiving's job, not this project's, and this project
  must not compete with it for the same media files or scheduled window.
- Movie/TV folder-structure or duplicate-file detection — no such problem
  has actually been observed in Archive Movies, Archive TV, Movies, or
  Shows; inventing a speculative check for a problem that hasn't occurred
  is explicitly against this project's own stated design principle above.
- Automatically deleting anything Jellyfin or Lidarr doesn't already
  consider a duplicate/orphan by this project's own evidence standard.
- Retiring or replacing Lidarr's own `renameTracks`/metadata-consumer
  fix — that's already done and confirmed working; this project exists
  for content those settings can't reach (pre-existing files, anything
  added outside Lidarr's own import pipeline).
- Building a general-purpose Jellyfin/Lidarr dashboard or UI — this is a
  scheduled backend check with a report, not an interactive tool.
- Fixing the remaining `Unknown Artist / Unknown Album` stray tracks
  (already documented as not worth chasing) or supplying artwork for
  albums confirmed to have none embedded — those need a human to actually
  find art, which this project cannot automate.

## Safety and credentials

- A dedicated Jellyfin API key (named clearly, e.g. `jellyfin-integrity`)
  is created once for this project and stored in
  `/mnt/Media/data/tools/jellyfin-integrity/config.json` (mode `600`,
  root-readable only, never committed to Git) — unlike every key used
  interactively this session, this one is **not** revoked after use, since
  it backs a recurring unattended job. It needs no more than the
  Library/Items/Collections/Playlists scopes this tool actually calls.
- Lidarr's existing API key is reused read-only for this project's
  scatter/duplicate detection (it doesn't need to call anything on
  Lidarr's write side) — no new Lidarr key.
- Every file-moving action (foldering, consolidation, gap-fill) writes a
  full before/after manifest to `reports/` before touching anything,
  exactly matching this session's own dry-run-then-apply pattern, so any
  run's changes can be audited or reversed by hand.
- No action in this project ever calls a raw filesystem delete on a
  candidate duplicate. Deletion only happens after explicit human
  approval of a specific dated report, and only for exactly the files
  listed in that report — never a fresh re-scan at approval time that
  could silently pick up something different.
- Runs are serialized via a lockfile; a run that hasn't finished by the
  next Sunday's trigger is left alone rather than started concurrently.
- Each run is capped at a configurable maximum number of file-moving
  actions, so a bug or unexpected library-wide change can't silently
  reorganize the entire library unattended in one pass.
- The tool is not scheduled on TrueNAS until Milestone 2's supervised
  live run has passed.

## Tooling decision

- Pure Python 3, no external dependencies beyond the standard library —
  this session's own from-scratch FLAC/MP3/M4A duration readers, already
  written and validated, become `lib/duration.py` directly. This
  deliberately avoids reintroducing `ffprobe`/`mutagen` as dependencies
  that could vanish again in a future cleanup, per the precedent of them
  already having been removed once this session.
- Self-contained install under `/mnt/Media/data/tools/jellyfin-integrity/`,
  matching the `beets`/`video-archiver` precedent — no changes to
  TrueNAS's system Python.
- Jellyfin and Lidarr REST APIs via the standard library's `urllib` (same
  approach used successfully throughout this session), not a third-party
  client library.
- TrueNAS's native Cron Job (middleware `cronjob.create`), the same
  supported mechanism already used for the `config.save` export earlier
  in this repo's history — not a raw crontab edit.
- Dated JSON-lines log per run plus a human-readable summary, retained
  under the tool's own `reports/` directory (not committed to Git —
  contains full local paths and album/track titles).

## Milestone 1 — Formalize the detectors, dry-run only

- [x] Wrote the `lib/` module structure fresh (`duration.py`, `orphans.py`,
  `scatter.py`, `artwork.py`, `duplicates.py`, `jellyfin.py`, `lidarr.py`,
  `paths.py`, `collections_check.py`) — the prior session's scratchpad
  scripts referenced here no longer existed (that session's scratchpad
  directory is ephemeral and had already been cleaned up), so this was a
  rewrite from the documented behavior above rather than a literal
  extraction. Every reader/extractor/classifier was validated against
  synthetic, byte-level ground-truth fixtures (known-in-advance durations
  and embedded art for FLAC/MP3/M4A, including ID3v2/ID3v1 tags, the
  padding bit, and MPEG2/2.5 low-samplerate frames) before being trusted
  against real data — see `scripts/jellyfin-integrity/README.md`.
- [x] Ran every detector in dry-run mode against the real library
  2026-09-07. First pass surfaced two real bugs the gate exists to catch:
  a path-translation double-prefix bug (`/media/media/music/...` handled
  incorrectly, which would have made every file-move target wrong) and a
  stale-Jellyfin-catalog bug (`/Items` still reported a track under
  `Compilations/Bad`, a folder already deleted from disk in an earlier
  manual fix — fixed by forcing and waiting for a fresh library scan
  before every run). After both fixes, the dry-run did **not** show
  literal zero findings — it found real (spot-checked against the actual
  filesystem, confirmed genuine) new duplicate/gap-fill/scatter
  candidates that accumulated via Lidarr's continuing imports since the
  baseline above was recorded hours earlier, plus 63 albums missing art
  (22 auto-fillable). Nothing was auto-applied to anything ambiguous —
  scatter's auto-consolidate count was 0 on the real run. Reviewed and
  accepted as expected library drift, not detector false positives.
- [x] Equivalent coverage for "deliberately re-introduce one known-fixed
  case" was done via synthetic mock-data tests exercising each detector's
  actual decision logic directly (orphan folder-path computation, scatter
  auto-consolidate vs. queued-for-review, multi-disc-subfolder exclusion,
  duplicate/gap-fill/ambiguous classification) rather than against a
  disposable copy of the real library.
- [x] Collection/playlist-count check confirmed reading current Jellyfin
  state and persisting it as the first baseline
  (`reports/collections_baseline.json`).

### Gate

Passed 2026-09-07, with two real bugs caught and fixed by this gate
before any code touched a real file — see above.

## Milestone 2 — Supervised live run

- [x] Created the dedicated `jellyfin-integrity` Jellyfin API key
  2026-09-07.
- [x] Ran the full tool once, by hand, in `--apply` mode against the real
  library 2026-09-07. Not zero changes, per Milestone 1's finding above:
  applied 22 embedded-art extractions and 1 gap-fill move (a Carrie
  Underwood *Storyteller* track present in one folder but missing from
  another), 23/50 actions used. Verified against the real filesystem
  (manifest written before the move, file confirmed moved, cover.jpg
  confirmed a valid JPEG) and against Jellyfin's own API afterward (the
  album's `ImageTags.Primary` now reflects the extracted cover).
- [x] Validated the failure path 2026-09-07: a bad API key and an
  unreachable host both failed loudly with a clear message and exit code
  2, no silent skip.
- [x] Duplicate-detection report sent to Jason for review (7 candidate
  pairs, each with matched/mismatched track counts and per-track
  duration deltas); confirmed reviewable.

### Gate

Passed 2026-09-07.

## Milestone 3 — Unattended Wednesday 3am schedule

- [x] Installed the TrueNAS Cron Job (`midclt call cronjob.create`, id
  `2`) for Wednesday 03:00, running `check_integrity.py --config
  config.json --apply` with the per-run action cap set in `config.json`
  (started at 50 as a conservative Milestone-1 default, raised to 100 on
  Jason's instruction 2026-09-07).
- [x] Checked TrueNAS's own scheduled jobs 2026-09-07: found a real
  conflict with the originally-proposed Sunday 03:00 slot (ZFS scrub
  starts Sunday 00:00, historically finishes ~02:46 per `zpool status`;
  daily backup-pull rsync runs 04:30 every day). Moved to Wednesday 03:00
  on Jason's instruction, which avoids the scrub entirely.
- [x] Added `check_jellyfin_integrity` to `scripts/doctor.sh`
  2026-09-07, matching the `check_nut`/`check_backup_age` pattern — reads
  the latest report over SSH, fails on any action error, collection/
  playlist alert, or cleanup-task trigger drift, warns if no run has
  landed in >200 hours.
- [ ] Run unattended for at least two consecutive Wednesdays and review
  both logs before calling this milestone closed. *(Not yet possible —
  needs real calendar time; first scheduled run is the next Wednesday.)*

### Gate

Two consecutive clean unattended runs, both reviewed, still required
before this milestone passes — not yet met.

## Milestone 4 — Documentation and closeout

- [x] Recorded final tool location, config, schedule, and report location
  in [04-Operations.md](../04-Operations.md) 2026-09-07.
- [x] Added to the existing backup pipeline 2026-09-07, on Jason's
  instruction: `scripts/backup/jellyfin-integrity.sh` (matching the
  `nut.sh`/`proxmox.sh` pattern) pulls `config.json` and both `reference/`
  manifests from TrueNAS into `~/lab/private-backups/jellyfin-integrity/`;
  `check_backup_age "Jellyfin Integrity" ... 192` added to `doctor.sh`.
  Run once already to create the initial backup.
- [ ] Update this project's status to `Complete` only after Milestone 3's
  gate passes (two consecutive clean Wednesday runs) and documentation is
  current.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Duplicate-detection false positive deletes a genuinely different edition | Detection queues a report; deletion never happens automatically, only on explicit human approval of that specific report |
| From-scratch duration readers have an undiscovered bug on some format/encoder | Milestone 1's dry run against the already-known-clean real library must show zero findings before any write action is trusted |
| Unattended job runs away and reorganizes the whole library at once | Hard per-run action-count cap, configurable and logged |
| Tool competes for I/O with Sunday ZFS scrub or backup pulls | Schedule placement checked against existing TrueNAS jobs in Milestone 3 |
| Collection-count check has no recovery data if it fires on a library other than music | Migration manifests mirrored into the tool's own `reference/` directory, not just the Mac-side backup |
| API key leaks into Git or logs | Stored in a mode-600 file outside Git; log files never include key values |
| Jellyfin's startup cleanup task re-enables itself after an update | Config-drift check re-verifies the trigger state every run, independent of whether it was ever re-enabled |

## Evidence log

| Date | Milestone | Evidence | Result | Operator |
|---|---|---|---|---|
| 2026-09-06/07 | 0 (basis) | Every detector and correction this project formalizes was already run against the real production library by hand — see [04-Operations.md](../04-Operations.md) | 271 orphans fixed, 79 scattered-album candidates resolved, 30 missing-art cases reduced to 21, 2 collection-deletion incidents recovered | Claude |
| 2026-09-07 | 1 | Dry-run against real library, iterated to fix 2 real bugs found by the gate (path double-prefix, stale Jellyfin catalog) | 0 orphans, 6 scatter candidates (0 auto), 68 duplicate-candidate pairs (7 queued, 1 gap-fill), 63 albums missing art (22 fillable) — all real, spot-checked against the filesystem, not false positives | Claude |
| 2026-09-07 | 2 | Supervised `--apply` run, human watching; failure-path test (bad key, unreachable host) | 22 art extractions + 1 gap-fill applied (23/50 actions), verified on disk and via Jellyfin's own API; both failure-path tests failed loudly with exit code 2 | Claude |
| 2026-09-07 | 3 (partial) | TrueNAS Cron Job installed, Lab Doctor check added, schedule conflict check performed | Cron id `2`, Wednesday 03:00 (moved off the original Sunday 03:00 proposal after finding it overlapped the weekly ZFS scrub); `check_jellyfin_integrity` added to `scripts/doctor.sh` | Claude |

## References

- [04-Operations.md — full history of the manual fixes this project formalizes](../04-Operations.md)
- [Plex-to-Jellyfin media migration project](<completed projects/Plex-to-Jellyfin-Media-Migration.md>)
- [Video Library Archiving project — architectural precedent for safe-automation design](Video-Library-Archiving.md)
- [Lidarr API documentation](https://lidarr.audio/docs/api/)
- [Jellyfin API documentation](https://api.jellyfin.org/)
- [HomeLab backup design](../05-Backups.md)
