# Video Library Archiving Project

> Status: Proposed — Milestone 1 (discovery/dry-run) complete; no destructive action taken
>
> Project owner: Jason
>
> Last updated: 2026-09-07

## Purpose

Radarr/Sonarr-acquired movies and television ("current" library, `/mnt/Media/data/media/movies`
and `/mnt/Media/data/media/tv`) are stored at their original acquired size — typically 5–25 GB
per file. Once a title has been sitting in the current library for a while, that size is no
longer buying anything: nobody is actively re-watching a freshly-added file six months later at
its original bitrate. This project automatically downconverts eligible current-library files to
roughly 1–2 GB and relocates them into the `archive-movies`/`archive-tv` roots that the
[Plex-to-Jellyfin media migration project](<completed projects/Plex-to-Jellyfin-Media-Migration.md>) already created,
freeing space in the current library on a rolling basis without any manual intervention once the
automation is trusted.

This is a **separate project** from the Plex-to-Jellyfin migration. That project explicitly lists
"transcoding media merely to complete the migration" as out of scope — this project exists
precisely to transcode, on an ongoing basis, after a title has aged out of active rotation. It
reuses that project's archive directories and naming conventions rather than duplicating them.

## Completion outcome

The project is complete only when:

- a tool exists that identifies current-library files whose Radarr/Sonarr-recorded import date is
  older than the configured age threshold;
- that tool transcodes each eligible file to a target size, verifies the result before touching
  anything else, and only then relocates it into the matching archive root;
- Radarr's and Sonarr's own state (file records, monitoring) is updated through their APIs so
  neither app treats an archived file as missing or attempts to re-acquire it;
- a failure at any stage leaves the original file completely untouched and produces a clear log
  entry rather than a partial or corrupted result;
- the pipeline has been validated end-to-end on at least one real movie and one real TV episode
  under human supervision before being handed to an unattended schedule; and
- the unattended schedule, its resource limits, and its logs are documented for ongoing operation.

## Authoritative baseline

Recorded 2026-08-30 via read-only inspection (no state changed):

- [x] Live media stack is the `dockge`-managed `new_arr` compose project at
  `/mnt/Media/appdata/dockge/new_arr/compose.yaml`, `MEDIA_PATH=/mnt/Media/data`.
- [x] Radarr owns `/mnt/Media/data/media/movies` (host path); folder naming is Radarr's default
  `Title (Year) {tmdb-####}/`.
- [x] Sonarr owns `/mnt/Media/data/media/tv` (host path); folder naming is Sonarr's default
  `Series Name/Season ##/`.
- [x] `archive-movies` and `archive-tv` already exist at `/mnt/Media/data/archive-movies` and
  `/mnt/Media/data/archive-tv`, created and ACL'd (`truenas_admin:apps`, `750`) by the
  Plex-to-Jellyfin migration project. This project writes into those same roots.
- [x] A second, older compose stack exists at `/mnt/Media/docker/docker-compose.yml`, mounting
  `/mnt/Media/media` (no `data/`) directly. Container names collide with the live `new_arr` stack,
  so only one can be running at a time; the live one is `new_arr` (confirmed against
  `MEDIA_PATH`). The old stack/path look like dead leftovers. **Not touched by this project** —
  flagged as a separate follow-up to confirm and clean up.
- [x] No `ffmpeg`, `ffprobe` or `HandBrakeCLI` is currently installed on TrueNAS.
- [x] TrueNAS: 12 cores, 31 GiB RAM. At the time of this check the box was under real memory
  pressure (28/31 GiB used) because Milestone 3 of the Plex-to-Jellyfin migration
  (an overnight archive-video `rsync`) was actively running. This project's tooling must not be
  deployed or scheduled to run concurrently with that migration's remaining overnight work.
- [x] Radarr/Sonarr API keys and installed versions retrieved 2026-09-07, read-only, kept out of
  Git and never printed to any log. **Correction to this baseline's original assumption:** the
  actual `config.xml` location is not `/mnt/Media/appdata/{radarr,sonarr}/` (that path only holds
  each app's *appdata*, e.g. custom scripts/backups) — the real config, including `ApiKey`, lives
  in the container's `/config` mount, which resolves on the host to
  `/mnt/.ix-apps/docker/volumes/<per-app-volume-id>/_data/config.xml` (found via
  `docker inspect radarr|sonarr --format '{{range .Mounts}}...'`). Installed versions: Radarr
  `6.3.0.10514-ls314`, Sonarr `4.0.19.2979-ls322` (both `lscr.io/linuxserver.io` images, `/api/v3`
  confirmed reachable and returning valid data for `GET /movie`, `GET /series`,
  `GET /episodefile`). The exact `DELETE /moviefile/{id}` / `DELETE /episodefile/{id}` semantics
  (whether it also unmonitors, effect on the parent entry) are still **not** confirmed against
  generated API docs — deliberately deferred; only GET endpoints were exercised during this
  read-only dry-run milestone, consistent with the delete-endpoint confirmation being required
  before Milestone 2, not Milestone 1.

## Architecture decisions

These were confirmed with Jason on 2026-08-30 before any implementation:

### Radarr/Sonarr stay authoritative for file deletion

The tool never calls `rm` on a file inside the current library directly. Once a transcoded,
verified copy exists in the archive root, the tool calls Radarr's
`DELETE /api/v3/moviefile/{id}` (or Sonarr's equivalent `episodefile` endpoint), which is the
apps' own designed mechanism for removing a tracked file — it keeps each app's database and the
filesystem in agreement by construction, rather than the tool guessing at what state Radarr/Sonarr
expect. The exact delete semantics (does it also unmonitor, does it affect the parent movie/series
entry) must be confirmed against the actually-installed API version's generated documentation
before Milestone 2 begins, not assumed from general Radarr/Sonarr knowledge.

### Age comes from Radarr/Sonarr, not the filesystem

Eligibility is based on `movieFile.dateAdded` / `episodeFile.dateAdded` as reported by each app's
API — the actual recorded import event — rather than filesystem `mtime`, which can be disturbed by
re-imports, hardlink operations, or unrelated metadata refreshes.

### Transcoding runs on TrueNAS, in software, today

No GPU exists anywhere in the lab yet (Proxmox's GPU is planned but not landed — this design does
not assume it). Transcoding runs as a plain CPU (x265) encode directly on TrueNAS, avoiding a
staging round-trip to another host for no current benefit. If a GPU lands on a host with access to
this storage later, hardware encoding is a follow-up optimization, not a blocker to shipping this
now.

**Tool substitution:** the request used HandBrake as the reference transcoder. This design uses
`ffmpeg`/`ffprobe` with `libx265` instead — the same encoder library HandBrake itself uses
underneath, but as a static Linux binary from the same publisher (johnvansickle.com, linked from
ffmpeg.org) already sha/md5-verified and installed once for the Plex-to-Jellyfin migration's
`beets`/Milestone 4 work. Reusing an already-vetted binary avoids introducing a second unreviewed
third-party download for equivalent output quality. Flagging this substitution explicitly in case
HandBrake's specific preset behavior or GUI-adjacent tooling was actually wanted.

### Fully unattended once trusted, but not on day one of deployment

Steady-state operation is a scheduled job with **no per-batch human approval queue** — this was an
explicit choice over a review-gated design. That governs ongoing operation, not the first
deployment: like the UPS project's shutdown-threshold work, the trigger mechanism gets a
supervised live test on real data before it is left to run alone (see Milestones 2–3 below). This
mirrors this repository's standing rule that irreversible or production-affecting automation earns
a validated dry run before it is trusted unattended.

## Milestone 1 findings (2026-09-07)

Two real bugs and one design-level problem were found while getting the dry run to actually run
against live data — recorded here since the reasoning behind each fix matters for anyone touching
this tool later.

### Bug: dry-run required `ffprobe` already installed, contradicting the Milestone 1 gate

As originally written, `_process_one()` in `pipeline.py` called `probe()` (which shells out to
`ffprobe`) for every candidate even in dry-run mode, in order to log a projected bitrate/resolution
plan. That directly contradicted this doc's own Milestone 1 gate ("do not install `ffmpeg`/
`ffprobe`... until the dry-run candidate list has been reviewed") — the dry run as shipped could
not have run at all before that install. **Fixed**: dry-run mode now reports only what the Radarr/
Sonarr APIs already provide (title, source path, size, `dateAdded`, planned archive destination)
and never calls `ffprobe`. The projected bitrate/resolution plan is now only computed during an
actual `--execute` run (Milestone 2 territory), which is when `ffmpeg`/`ffprobe` are installed
anyway.

### Bug: candidate discovery compared container paths against host paths

Radarr's and Sonarr's REST APIs report `path` fields as seen from *inside each app's own
container* (e.g. `/media/movie/media/movies/Obsession (2026)/...` for Radarr,
`/media/tv/media/tv/Rick and Morty/...` for Sonarr — confirmed via `docker inspect`, both
containers bind-mount the same host directory, `/mnt/Media/data`, at different container mount
points). The original `candidates.py` compared these container paths directly against the
host-path config values (`movies_current_root`, `tv_current_root`), so every candidate silently
failed the `relative_to()` check and was skipped — the first dry run returned 0 candidates with no
error, which would have looked like "nothing eligible yet" rather than "broken." **Fixed**: added
`host_data_root`, `radarr_container_root`, `sonarr_container_root` to config, and a
`_to_host_path()` translation step in `candidates.py` applied to every path read from either API
before any comparison or filesystem/`ffprobe` use.

### Design finding: the Plex→Jellyfin migration reset `dateAdded` library-wide

With the path bug fixed, the dry run at the real 182-day threshold still returned 0 candidates.
Confirmed this is correct, not a bug: the Plex-to-Jellyfin media migration (completed 2026-09-01)
reimported the entire library into Radarr/Sonarr, resetting `movieFile.dateAdded`/
`episodeFile.dateAdded` for every file to August/September 2026 — the oldest recorded
`movieFile.dateAdded` across the whole library is 2026-08-04. Under the current design ("Age comes
from Radarr/Sonarr, not the filesystem" — chosen specifically to avoid disturbance from
re-imports), **no file will become eligible until roughly February–March 2027**, regardless of a
title's real age. Checked whether filesystem `mtime` still reflects genuine history as a possible
alternative signal: it does (e.g. *The Shawshank Redemption*'s file has an `mtime` of April 2021),
though at least one file has an obviously corrupt `mtime` (*The Boy and the Heron*, timestamped
~2097) that would need explicit filtering if `mtime` were ever used.

**Decision (Jason, 2026-09-07): keep the `dateAdded`-based design as-is for the actual project.**
No further action needed until dates naturally age past the threshold; revisit later if the delay
becomes a real problem. For validation purposes only, confirmed the pipeline mechanics work
end-to-end using a throwaway config with `age_threshold_days` temporarily set to 30 (see Evidence
log) — the real `config.json` on TrueNAS was never modified and stays at the documented 182-day
threshold.

## Approved target layout

Reuses the Plex-to-Jellyfin migration's archive roots and naming conventions exactly, so a single
Jellyfin library scan (once Archive Movies/Archive TV libraries exist — that project's Milestone 5)
picks up both former-Plex archive content and downconverted current-library content
indistinguishably:

```text
/mnt/Media/data/
├── media/
│   ├── movies/              # Radarr-managed, current, untouched by this project except via API
│   └── tv/                  # Sonarr-managed, current, untouched by this project except via API
├── archive-movies/          # Former Plex movies + downconverted current movies land here
├── archive-tv/              # Former Plex TV + downconverted current TV lands here
└── tools/
    └── video-archiver/      # This project's self-contained tool install (proposed path)
```

Archive-side naming preserves the source folder/file naming Radarr/Sonarr already used
(`Title (Year) {tmdb-####}/…`, `Series Name/Season ##/…`) so the archive libraries scan cleanly
without a rename pass.

## Scope

- Query Radarr and Sonarr for current-library files whose recorded import date exceeds the
  configured age threshold (default 6 months).
- Transcode eligible video to H.265, targeting roughly 1–2 GB, using an adaptive bitrate/resolution
  calculation driven by source duration (not a single fixed setting that overshoots long content or
  wastes bits on short content).
- Preserve subtitle streams/sidecar files and pass through compact audio; re-encode audio only when
  the source audio track itself is large (lossless/high-bitrate tracks).
- Verify every transcoded file (duration match, valid stream, non-zero size) before anything
  irreversible happens.
- Move the verified file into the matching archive root using the source's existing naming.
- Remove the file from Radarr/Sonarr's tracking via each app's own file-delete API call, only after
  the archive copy is confirmed on disk.
- Log every decision and action (candidate list, transcode result, verification result, API result)
  to a structured, reviewable report.
- Run on a schedule with a bounded per-run batch size and resource-aware guards.

## Out of scope

- Any change to the Plex-to-Jellyfin migration project's own milestones, timeline, or in-flight
  overnight jobs.
- Deleting or modifying the former-Plex archive content that project already copied.
- Retiring, deleting, or renaming Radarr/Sonarr movie or series entries themselves — only the file
  record for an individual eligible file.
- Upscaling, re-tagging, or otherwise "fixing" archive metadata beyond what's needed for a clean
  Jellyfin scan.
- Cleaning up the stale `/mnt/Media/docker/docker-compose.yml` stack (flagged as a follow-up, not
  this project's job).
- GPU/hardware-accelerated transcoding (no GPU exists yet; noted as a future optimization only).

## Safety and credentials

- The tool never deletes or modifies a file inside the current library directly — only Radarr's or
  Sonarr's own delete-file API call does that, and only after the archive copy is verified.
- Every transcode writes to a temporary filename inside the destination archive directory (same
  filesystem as the final path) and is only atomically renamed into place after verification —
  never an in-place overwrite, never a partially-written file visible at the final path.
- Any failure at any stage (probe, encode, verify, move, API call) aborts processing for that one
  file, leaves the original completely untouched, and logs the error. It never retries destructive
  steps automatically or guesses at a recovery action.
- Radarr/Sonarr API keys are read from each app's own `config.xml` on the host or from an
  environment variable at run time — never committed to Git, never written to the log files this
  tool produces.
- Runs are serialized via a lockfile; an overlapping scheduled run is skipped rather than started
  concurrently.
- Each scheduled run is capped at a configurable maximum file count so a misconfiguration cannot
  process the entire library unattended in one pass.
- The tool is not deployed to TrueNAS, and no cron/systemd schedule is installed, until Milestone 2
  (supervised live test) has passed — see Milestones below.

## Tooling decision

- `ffmpeg`/`ffprobe` (static build, already vetted for this pool of projects) for probing and
  transcoding — substituted for the referenced HandBrake per the note above.
- `requests` (Python) against the Radarr v3 and Sonarr v3 REST APIs for candidate discovery and
  file deletion.
- Self-contained install under `/mnt/Media/data/tools/video-archiver/`, matching the `beets`
  precedent from Milestone 4 of the Plex-to-Jellyfin project — no changes to TrueNAS's system
  Python or packages.
- A structured JSON-lines log per run, plus a human-readable summary, retained under the tool's own
  directory (not committed to Git — contains full local paths).

## Milestone 1 — Discovery and dry-run candidate list

- [x] Confirm the installed Radarr and Sonarr API versions — done 2026-09-07 (Radarr
  `6.3.0.10514-ls314`, Sonarr `4.0.19.2979-ls322`). The exact delete-file endpoint behavior against
  generated API docs is **still open** — intentionally deferred to before Milestone 2, since
  Milestone 1 only exercised GET endpoints.
- [x] Retrieve API keys from each app's `config.xml` (read-only) and store them outside Git — done
  2026-09-07; see the corrected `config.xml` location noted in the Authoritative baseline above.
- [x] Implement candidate discovery (`--dry-run`, the tool's default mode): list every file whose
  `dateAdded` exceeds the age threshold, its current size, and its would-be archive destination
  path — with no transcoding, moving, or API writes. Done, after fixing the two bugs described in
  "Milestone 1 findings" below (dry-run's incidental `ffprobe` dependency, and the container-vs-host
  path mismatch).
- [x] Run the dry run against the real Radarr/Sonarr data and review the candidate list together
  before proceeding — done 2026-09-07. At the real 182-day threshold: 0 candidates, confirmed
  correct (see findings below, not a bug). At a temporary 30-day test threshold: 411 real
  candidates (14 movies, 397 episodes, ~927.5 GB), correct source/destination paths, 0 failures.
- [x] Confirm destination free space in `archive-movies`/`archive-tv` is sufficient for the
  expected first-batch volume — 3.3 TB free on the shared `Media/data` pool (71% used, 11 TB
  total), confirmed 2026-09-07.
- [x] Confirm this milestone's work does not run concurrently with the Plex-to-Jellyfin migration's
  remaining overnight jobs (check `ps`/`docker` state on TrueNAS before each dry run) — confirmed
  no `rsync`/`beets`/`ffmpeg`/`handbrake` processes running 2026-09-07; that migration project is
  also now fully Complete, so this concern no longer applies going forward.

### Gate

Do not install `ffmpeg`/`ffprobe` or write anything to TrueNAS until the dry-run candidate list has
been reviewed and looks correct — right files, right ages, right destinations, no current-library
files with unexpectedly old `dateAdded` values that would indicate a data-quality problem in this
approach.

**Gate passed 2026-09-07** for the tool's code and its own self-contained directory under
`/mnt/Media/data/tools/video-archiver/` (Python source + `config.json`, no `ffmpeg`/`ffprobe`
binary). `ffmpeg`/`ffprobe` remain not installed — that stays Milestone 2's job.

## Milestone 2 — Supervised live test

- [ ] Install the self-contained `ffmpeg`/`ffprobe` build under
  `/mnt/Media/data/tools/video-archiver/`.
- [ ] Run the full pipeline — transcode, verify, move, Radarr/Sonarr delete-file call — against
  exactly one already-identified movie file and one already-identified TV episode file, with a
  human watching each step.
- [ ] Confirm the archived file plays correctly in a media player (or via `ffprobe`/a manual
  Jellyfin scan of the archive root) before considering the test successful.
- [ ] Confirm Radarr/Sonarr no longer show the file as present, do not report it as missing or
  trigger a re-download, and the parent movie/series entry is in the expected state.
- [ ] Confirm the original file is gone from the current library only after every prior check
  passed.
- [ ] Record actual achieved output size, encode duration, and CPU/memory load observed during the
  test.

### Gate

Both test files must pass every check above before any unattended schedule is installed. A single
failure at this stage means fixing the pipeline and repeating the supervised test, not proceeding
to Milestone 3 with a known issue.

## Milestone 3 — Unattended schedule

- [ ] Install a scheduled job (cron or systemd timer) on TrueNAS running the tool in `--execute`
  mode with the agreed batch-size cap and age threshold.
- [ ] Confirm the schedule does not overlap with other heavy scheduled jobs on TrueNAS (backups,
  scrubs, the Plex-to-Jellyfin migration's remaining work).
- [ ] Add a HomeLab Doctor check (or equivalent) for the tool's log freshness/error rate, matching
  the `check_nut`/`check_backup_age` pattern used elsewhere in this repo.
- [ ] Run unattended for an initial observation period; review logs for unexpected failures or
  candidate-selection surprises before calling this milestone closed.

### Gate

The schedule is considered production-ready only after at least one full unattended run completes
cleanly and its log is reviewed.

## Milestone 4 — Documentation and closeout

- [ ] Record final tool location, config, schedule, and log location in the operations
  documentation.
- [ ] Add the tool's config/state to the existing backup plan if it should survive a TrueNAS
  rebuild.
- [ ] Update this project's status to `Complete` only after Milestone 3's gate passes and
  documentation is current.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Radarr/Sonarr re-acquire a file the tool just archived | Use each app's own delete-file API rather than a bare filesystem delete, so its tracking state stays consistent |
| A failed/truncated transcode gets treated as archived | Verify duration/size/exit code before the atomic rename into the final archive path; never leave a partial file at the final name |
| Original file lost before the archive copy is confirmed good | Strict ordering: verify archive copy first, only then call the delete API — never the reverse |
| Unattended job runs away and processes the whole library at once | Hard per-run file-count cap, configurable and logged |
| Tool competes for I/O/CPU with other scheduled TrueNAS work | Lockfile serialization; schedule placement reviewed against existing jobs in Milestone 3 |
| Quality target (1–2 GB) undershoots on very long content or overshoots on short content | Adaptive bitrate computed from actual source duration, not a fixed setting |
| API keys leak into Git or logs | Read from `config.xml`/environment only; log files never include key values |

## Evidence log

| Date | Milestone | Evidence | Result | Operator |
|---|---|---|---|---|
| 2026-08-30 | 0 (design) | Read-only recon: live compose stack, archive root ACLs, host resources, tool availability | Recorded above | Claude |
| 2026-09-07 | 1 | Pre-check: no `rsync`/`beets`/`ffmpeg`/`handbrake` running on TrueNAS; Radarr/Sonarr containers up | Clear to proceed | Claude |
| 2026-09-07 | 1 | Retrieved Radarr/Sonarr API keys read-only from actual `config.xml` locations; versions confirmed (Radarr 6.3.0.10514-ls314, Sonarr 4.0.19.2979-ls322) | Keys never printed/committed; corrected baseline's assumed `config.xml` path | Claude |
| 2026-09-07 | 1 | Deployed tool code (no `ffmpeg`/`ffprobe`) to `/mnt/Media/data/tools/video-archiver/`; ran `--dry-run` against real data at production 182-day threshold | 0 candidates — confirmed correct, not a bug (see Milestone 1 findings: Plex→Jellyfin migration reset `dateAdded` library-wide) | Claude |
| 2026-09-07 | 1 | Fixed dry-run's incidental `ffprobe` dependency and the container-vs-host path mismatch in `candidates.py`/`config.py`/`pipeline.py`; redeployed and reran dry run | Path resolution and candidate discovery confirmed correct | Claude |
| 2026-09-07 | 1 (test only) | Ran `--dry-run` against a throwaway config (`age_threshold_days` 30 instead of production 182, deleted after use) to validate pipeline mechanics end-to-end | 411 real candidates (14 movies, 397 episodes, ~927.5 GB), correct source/destination paths, 0 failures. Production `config.json` never modified | Claude |
| 2026-09-07 | 1 | Confirmed destination free space | 3.3 TB free / 11 TB total on `Media/data` pool | Claude |

## References

- [Plex-to-Jellyfin media migration project](<completed projects/Plex-to-Jellyfin-Media-Migration.md>)
- [Radarr API documentation](https://radarr.video/docs/api/)
- [Sonarr API documentation](https://sonarr.tv/docs/api/)
- [ffmpeg documentation](https://ffmpeg.org/documentation.html)
- [HomeLab backup design](../05-Backups.md)
