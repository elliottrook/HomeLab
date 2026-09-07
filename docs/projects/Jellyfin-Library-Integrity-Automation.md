# Jellyfin Library Integrity Automation Project

> Status: Proposed — design and tooling drafted from real fixes already
> validated in production; no unattended schedule installed yet
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
- [ ] A dedicated, persistent Jellyfin API key for this tool has not been
  created — every check and fix this session used a temporary key
  generated for that session and revoked afterward. This project needs a
  key that persists across scheduled runs (see Safety and credentials).
- [ ] TrueNAS's own Cron Job feature (used for the `config.save` export
  earlier) has not yet been tested for a Python-script trigger — needs
  confirming before Milestone 3.

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
being reachable from TrueNAS too. **Proposed:** copy the specific
manifests needed for recovery (`plex-movie-collections.json`,
`plex-to-jellyfin-movie-map.json`) into this project's own tool directory
on TrueNAS as a read-only reference copy, in addition to (not instead of)
their existing home in `~/lab/private-backups/`. This needs Jason's
confirmation since it's a second copy of migration-project data living in
a new location.

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
- Run every Sunday at 03:00 via a TrueNAS-native Cron Job, logging a
  dated, human-readable report plus a machine-readable JSON log per run.

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

- [ ] Extract this session's scratchpad scripts (duration readers, orphan
  detector/folderer, scatter detector/consolidator, art extractor,
  duplicate comparator) into the proposed `lib/` module structure.
- [ ] Re-run every detector in dry-run mode against the current, already-
  cleaned library and confirm it reports **zero** findings — the expected
  state, since this session's manual work already fixed everything found.
- [ ] Deliberately re-introduce one known-fixed case in a disposable test
  copy (e.g. a synthetic loose-file orphan) and confirm the tool detects
  and would correctly folder it, without running against the real library.
- [ ] Confirm the collection/playlist-count check correctly reads the
  current Jellyfin state as its first "last known good" baseline.

### Gate

Every detector must show zero false positives against the current,
already-clean library, and correctly catch the synthetic re-introduced
case, before any code is allowed to modify a real file.

## Milestone 2 — Supervised live run

- [ ] Create the dedicated `jellyfin-integrity` Jellyfin API key.
- [ ] Run the full tool once, by hand, with a human watching, in
  `--apply` mode against the real library — expected to make zero changes
  and produce a clean report, since the library is already fixed.
- [ ] Validate the failure path: deliberately point the tool at a wrong
  API key or an unreachable host and confirm it fails loudly and safely
  rather than silently skipping a check.
- [ ] Confirm the duplicate-detection report format is genuinely reviewable
  — Jason reads one real (even if empty) report and confirms it contains
  enough evidence to make an approve/reject call without re-deriving the
  comparison by hand.

### Gate

The supervised run must complete cleanly, the failure-path test must fail
safely, and the report format must be confirmed reviewable before an
unattended schedule is installed.

## Milestone 3 — Unattended Sunday 3am schedule

- [ ] Install the TrueNAS Cron Job for Sunday 03:00, running the tool in
  `--apply` mode with the agreed per-run action cap.
- [ ] Confirm the schedule doesn't overlap with other heavy Sunday jobs
  (ZFS scrub, existing backup pulls) — check TrueNAS's own scheduled task
  list before finalizing the time.
- [ ] Add a HomeLab Doctor check for this tool's log freshness/error rate,
  matching the `check_nut`/`check_backup_age` pattern.
- [ ] Run unattended for at least two consecutive Sundays and review both
  logs before calling this milestone closed.

### Gate

Two consecutive clean unattended runs, both reviewed, required before this
milestone passes.

## Milestone 4 — Documentation and closeout

- [ ] Record final tool location, config, schedule, and report location in
  04-Operations.md.
- [ ] Add the tool's config/reference manifests to the existing backup
  plan if they should survive a TrueNAS rebuild.
- [ ] Update this project's status to `Complete` only after Milestone 3's
  gate passes and documentation is current.

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

## References

- [04-Operations.md — full history of the manual fixes this project formalizes](../04-Operations.md)
- [Plex-to-Jellyfin media migration project](<completed projects/Plex-to-Jellyfin-Media-Migration.md>)
- [Video Library Archiving project — architectural precedent for safe-automation design](Video-Library-Archiving.md)
- [Lidarr API documentation](https://lidarr.audio/docs/api/)
- [Jellyfin API documentation](https://api.jellyfin.org/)
- [HomeLab backup design](../05-Backups.md)
