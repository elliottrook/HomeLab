# Video Library Archiving Project

> Status: In progress — Milestones 1-2 complete; Milestone 3's unattended schedule is installed
> and running (Mon-Sat 01:30), started ahead of its own review-first gate on Jason's direction
>
> Project owner: Jason
>
> Last updated: 2026-09-08

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
expect.

**Confirmed by live testing (2026-09-08), not just the generated API docs: delete-file alone is
NOT enough.** `DELETE /episodefile/{id}` removes the file record but leaves the parent episode
`monitored: true` with `hasFile: false` — a "monitored but missing" state that risks Sonarr
re-searching for and re-downloading the very file this tool just archived (confirmed the risk was
real for the one episode this affected before the fix landed: queue was still empty, but Sonarr's
next scheduled missing-episode search would have found and grabbed it). Fixed: `_delete_source()`
now also calls Sonarr's `PUT /episode/monitor` (or Radarr's `PUT /movie/editor`) with
`monitored: false` immediately after the delete-file call, using the movie's/episode's own id
(distinct from the file id — `Candidate.arr_parent_id`, resolved for episodes via a
`episodeFileId -> episode id` lookup since the episodefile resource has no reverse reference to its
parent episode).

### Age comes from Radarr/Sonarr, not the filesystem

Eligibility is based on `movieFile.dateAdded` / `episodeFile.dateAdded` as reported by each app's
API — the actual recorded import event — rather than filesystem `mtime`, which can be disturbed by
re-imports, hardlink operations, or unrelated metadata refreshes.

**Threshold revised 2026-09-08 (Jason): 4 months, not 6.** `age_threshold_days` changed from 182 to
122 (same day-count approximation convention as before). For movies this changes nothing
structurally — still measured from that file's own `dateAdded`.

**TV eligibility is now anchored per-season, not per-episode (Jason, 2026-09-08).** The original
per-file design meant a season airing/downloading episode-by-episode over many weeks would archive
piecemeal — and worse, could take that same span of weeks just to finish moving once every episode
individually aged out, on top of the threshold itself. `find_episode_candidates()` now groups a
series' episode files by season, computes the **earliest** `dateAdded` within that season as the
season's start, and makes the whole season eligible together once that anchor point is old enough
— not each file against its own `dateAdded`. A season now ages out and moves as a single unit,
matching how a viewer actually thinks about "have I moved on from this season" rather than "have I
moved on from this specific episode file."

### Transcoding runs on TrueNAS, GPU-accelerated via the Jellyfin container

**Originally designed as a software-only encode** (see git history for that version of this
section) because "no GPU exists anywhere in the lab yet" — that plan was superseded 2026-09-08.
That assumption was checked again during Milestone 2 (2026-09-08) rather than trusted from the
2026-08-30 baseline, and turned out to be stale: an Intel Arc A380 had landed on this host
(`lspci`/`/dev/dri/renderD128` present, device nodes dated 2026-09-05) without this doc being
updated. Confirmed by live testing that changes the design:

- Software `libx265` 2-pass `medium`-preset encoding took **~1h42m for a single ~54-minute 1080p
  episode** — impractical for a whole-library job.
- The Jellyfin container already has `/dev/dri` passed through (`docker inspect jellyfin` shows
  `HostConfig.Devices`) and its own `jellyfin-ffmpeg` build already has VAAPI/QSV support compiled
  in — Jellyfin was already using this GPU for its own transcoding, just not exposed to this tool.
- Running `hevc_vaapi` through `docker exec jellyfin ...` (no separate install needed) hit
  **~21.6x real-time** on the same episode (~54 min of content encoded in ~2.5 minutes) — the
  difference between impractical and comfortably fits a nightly batch window.
- `hevc_vaapi`'s default rate control **ignores `-b:v` outright** and produced ~20-30 Mbps output
  against a 3.3 Mbps target in initial testing — confirmed necessary: explicit `-rc_mode VBR` plus
  `-maxrate`/`-bufsize` (same ratio convention as the software path: 1.5x/2x the target).

**Mechanism**: `ffmpeg_bin`/`ffprobe_bin` in config point at small wrapper scripts
(`scripts/video-archiver/bin/*-jellyfin-wrapper.sh`) that translate host paths under
`host_data_root` to the Jellyfin container's own `/media` mount point and `docker exec jellyfin
/usr/lib/jellyfin-ffmpeg/{ffmpeg,ffprobe}` with the translated arguments. This avoids downloading
any new third-party binary (the original HandBrake-substitution rationale below still applies to
*which* encoder is used, `libx265`/`hevc_vaapi`, just not to how it's installed) and reuses a
binary the lab already runs and trusts for exactly this kind of work.

Also switched from 2-pass to **single-pass** encoding as part of the same change — the 2-pass
design's precision (an exact target bitrate) was never needed given the target is already a size
*range* (`target_size_min/max_bytes`), and dropping the redundant analysis pass roughly halves the
work regardless of software vs. GPU encoding.

**Tool substitution (still applies):** the original request used HandBrake as the reference
transcoder. This design uses `ffmpeg`/`ffprobe` instead — HandBrake's own `libx265` encoder
underneath for the (now-fallback) software path, `hevc_vaapi` for the GPU path — because `ffmpeg`
is scriptable and already present via the Jellyfin container, avoiding a second third-party
install for equivalent output. Flagging this substitution explicitly in case HandBrake's specific
preset behavior or GUI-adjacent tooling was actually wanted.

### Fully unattended once trusted, but not on day one of deployment

Steady-state operation is a scheduled job with **no per-batch human approval queue** — this was an
explicit choice over a review-gated design. That governs ongoing operation, not the first
deployment: like the UPS project's shutdown-threshold work, the trigger mechanism gets a
supervised live test on real data before it is left to run alone (see Milestones 2–3 below). This
mirrors this repository's standing rule that irreversible or production-affecting automation earns
a validated dry run before it is trusted unattended.

### Only one audio track and English-only subtitles are kept, not every stream (2026-09-08)

Found via a real supervised test, not speculatively: `Ready or Not: Here I Come`, a "Multi AVC"
REMUX, carries **11 audio streams** (English, French x2, Spanish x2, German, Italian, plus extra
English commentary/stereo tracks). The original design mapped and reserved budget for every audio
stream regardless of count (`-map 0:a?`). For this file that reserved ~5056 kbps of audio budget
against a total ~1948 kbps size budget for the whole 108-minute movie — audio alone was already
2.6x over budget before any bits went to video. `compute_bitrate_plan()` correctly computed the
resulting video bitrate as the 100 kbps floor (`below_quality_floor: true`), but nothing acted on
that signal — the pipeline went ahead, ran a real GPU encode, and only failed afterward at
`verify_output`'s size check (several "copy"-mode source tracks passed through at their original
600+ kbps each pushed the actual output to ~3.9 GB against a 2 GiB cap). Source was never touched
(confirmed: file present, unchanged size, archive destination never created, work_dir temp file
cleaned up) — the safety design held, this was a wasted encode, not a data-safety failure.

**Fixed (Jason's call, 2026-09-08): keep exactly one audio track — the source's own flagged
default, falling back to the first English track, falling back to the first stream if neither
exists — and drop the rest entirely** rather than trying to fit a prioritized subset. A personal
archive doesn't need 5+ foreign-language 5.1 tracks preserved at full bitrate. `AudioStreamInfo`
now carries `is_default`/`language` (from ffprobe's `disposition.default` and `tags.language`);
`_select_primary_audio_stream()` picks the one to keep; `BitratePlan` carries a single
`selected_audio_input_index` instead of a per-stream list. Verified against the real 11-track
layout before redeploying: video bitrate recovered to 1564 kbps at full 1080p (was 100 kbps/480p),
estimated output ~1.47 GiB (was ~3.9 GiB).

**Subtitles: Jason also asked to make sure English subtitles are kept** — same
over-inclusive pattern existed there too (`-map 0:s?` kept every subtitle track regardless of
language). Unlike audio, subtitle streams are negligible in size, so there's no budget reason to
pick just one — `Probe` now carries per-subtitle `language`, and every English-tagged subtitle
stream is kept (the real file had 3: likely a plain track, an SDH track, and a forced track),
non-English ones dropped.

Re-ran the same real file after the fix: succeeded cleanly, 34.9 GB → 1.77 GB (94.9% smaller),
full 1080p retained, single English 5.1 track (EAC3), all 3 English subtitle tracks present,
verified via direct `ffprobe` on the output plus the same Radarr/Jellyfin checks as the `72 HOURS`
test.

### Manual "archive now" override via Radarr/Sonarr's own tags (2026-09-08)

Jason's request: a way to archive a specific movie or a show he's finished watching immediately,
without waiting out `age_threshold_days`. Considered building new UI for this; rejected in favor of
reusing Radarr's/Sonarr's own tag system, which Jason already has open regularly — no new interface
needed.

A movie (Radarr) or series (Sonarr) tagged `archive-now` (label configurable via
`archive_now_tag_label`, resolved to that app's numeric tag id via its own `/api/v3/tag` endpoint at
the start of every run — labels are what a human manages, ids aren't stable across a tag being
deleted and recreated) becomes eligible for archiving on the very next run, regardless of age. A
missing/unresolvable tag is never an error — it just means no override is available that run, and
normal age-based eligibility proceeds as before.

**Confirmed by Jason (2026-09-08): TV granularity is whole-series only, not per-season.** Sonarr's
tag model applies at the series level; tagging a series means "I'm fully done with this show,"
archiving every eligible season together, the same as if every season had simply aged out on its
own. Per-season tagging was considered and explicitly declined as unnecessary for now.

Validated end-to-end 2026-09-08 (dry-run only, nothing executed): tagged a real movie (`Obsession`,
`dateAdded` 2026-08-04, nowhere near the 122-day threshold) with `archive-now` via the Radarr API,
confirmed it appeared as the sole dry-run candidate with the correct source/destination paths, then
reverted the tag — proving the override path works independently of the age path, without touching
any real file. `archive-now` tags created in both apps (Radarr id 2, Sonarr id 1); both currently
unused (no title actually tagged by Jason yet).

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

## Milestone 2 findings (2026-09-07/08)

The GPU-vs-software pivot and the missing-unmonitor bug are covered above under Architecture
decisions, since both changed the design, not just the code. Three more bugs and one follow-up gap
surfaced running the real pipeline against the `Furious` season (8 real episodes, `--execute`, not
`--dry-run`):

### Bug: `.partial` temp filename broke ffmpeg's output-format autodetection

`dst_tmp` was named `<archive filename>.mkv.partial` — ffmpeg's muxer picks the output container
format from the filename extension, and `.partial` isn't one it recognizes. The very first real
`--execute` run got all the way through a full 2-pass software encode (~1h42m) only to fail at the
last step: "Unable to choose an output format." **Fixed**: the temp name now keeps `.mkv` as the
real trailing extension (`<name>.partial.mkv`), plus an explicit `-f matroska` flag as a backstop
so this can't recur even if naming changes again later.

### Bug: re-encoding could make an already-small file bigger

`Furious` S01E07's source was already a low-bitrate 0.29 GB x265 encode. Re-encoding it at this
project's target bitrate produced a 1.43 GB file — nearly 5x *larger*, the opposite of the
project's purpose. **Fixed**: `_process_one()` now checks `candidate.size_bytes <=
target_size_max_bytes` before transcoding; if already at or under the target, the file is relocated
via a straight copy instead of being re-encoded. (This one already-affected episode's original
source is gone — Sonarr's delete-file call deletes the underlying file, not just the database
record — so it wasn't retroactively re-fixed; the content itself is fully intact and playable, just
larger than ideal. Flagged to Jason, no action taken per his call.)

### Bug: writing the in-progress temp file inside the monitored archive folder confused Jellyfin

The temp output was originally written directly inside the destination archive directory (as
`<final name>.partial.mkv`) before being atomically renamed. Jellyfin's *real-time* library monitor
watches `archive-tv`/`archive-movies` and indexed that `.partial.mkv` filename while the encode was
still in progress; once the finished file was renamed to its real name, Jellyfin's database still
pointed at the temp filename, which no longer existed — every playback attempt failed with "Could
not find file." **Fixed**: the temp file now stages in `work_dir` (outside every Jellyfin library
entirely), and the only write Jellyfin's monitor ever observes inside the archive tree is the
single atomic rename into the final path.

### Follow-up: leftover Jellyfin `.trickplay` cache and empty current-library folders

Radarr/Sonarr's delete-file API only removes the video file itself, not Jellyfin's own per-file
`.trickplay` thumbnail-preview cache folder living alongside it in the current library. Once every
real episode file in `Furious` was archived, that leftover cache folder was still enough content
for Jellyfin's scanner to keep showing an empty "Furious" entry in the main Shows library. Also
discovered `POST /Items/{id}/Refresh` only refreshes metadata for items Jellyfin already knows
about — it does **not** reconcile the filesystem, so it never actually cleared the stale entry no
matter how many times it was called. The real fix needed Jellyfin's actual "Scan Media Library"
scheduled task (`POST /ScheduledTasks/Running/{scan_task_id}`), the same task id the
`jellyfin-integrity` tool's own config already relies on for this. **Fixed** two ways: (1)
`_cleanup_leftovers()` now runs after every successful archive+delete, removing the `.trickplay`
folder and then climbing upward removing any directory left empty, stopping at (never including)
the configured current-library root; (2) `run()` triggers one real library-scan task at the end of
a batch (not per-file, and skipped for dry runs / when nothing was archived) via a new
`video_archiver/jellyfin_client.py`, using a third API key (`JELLYFIN_API_KEY`) alongside Radarr's
and Sonarr's.

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
    └── video-archiver/      # This project's self-contained tool install
        ├── bin/              # ffmpeg/ffprobe-jellyfin-wrapper.sh (docker exec into jellyfin)
        ├── work/              # In-progress temp output — never inside a Jellyfin-monitored path
        ├── logs/
        └── video_archiver/    # Python package (config, candidates, pipeline, transcode, ...)
```

Archive-side naming preserves the source folder/file naming Radarr/Sonarr already used
(`Title (Year) {tmdb-####}/…`, `Series Name/Season ##/…`) so the archive libraries scan cleanly
without a rename pass.

## Scope

- Query Radarr and Sonarr for current-library files whose recorded import date exceeds the
  configured age threshold (default ~4 months — revised 2026-09-08, see Architecture decisions),
  anchored per-season for TV.
- Also treat a movie/series tagged `archive-now` in Radarr/Sonarr's own UI as eligible immediately,
  regardless of age — added 2026-09-08, see Architecture decisions.
- Skip transcoding (relocate as-is instead) any file already at or under the target size — added
  2026-09-08 after re-encoding inflated an already-small file (see Milestone 2 findings).
- Transcode remaining eligible video to H.265, targeting roughly 1–2 GB, using an adaptive
  bitrate/resolution calculation driven by source duration (not a single fixed setting that
  overshoots long content or wastes bits on short content). GPU-accelerated (`hevc_vaapi`) via the
  Jellyfin container as of 2026-09-08 — see Architecture decisions.
- Preserve subtitle streams/sidecar files and pass through compact audio; re-encode audio only when
  the source audio track itself is large (lossless/high-bitrate tracks).
- Verify every transcoded file (duration match, valid stream, non-zero size) before anything
  irreversible happens.
- Move the verified file into the matching archive root using the source's existing naming.
- Remove the file from Radarr/Sonarr's tracking via each app's own file-delete API call, only after
  the archive copy is confirmed on disk — and unmonitor the parent movie/episode in the same step
  (added 2026-09-08; delete-file alone leaves it monitored, see Architecture decisions).
- Clean up Jellyfin's leftover per-file `.trickplay` cache and any now-empty current-library
  directories after each successful archive, then trigger one real Jellyfin library-scan task at
  the end of a batch — added 2026-09-08, see Milestone 2 findings.
- Log every decision and action (candidate list, transcode result, verification result, API result)
  to a structured, reviewable report.
- Run on a schedule with a bounded per-run batch size and resource-aware guards.

## Out of scope

- Any change to the Plex-to-Jellyfin migration project's own milestones, timeline, or in-flight
  overnight jobs.
- Deleting or modifying the former-Plex archive content that project already copied.
- Retiring, deleting, or renaming Radarr/Sonarr movie or series entries themselves — only the file
  record for an individual eligible file (and its monitored flag).
- Upscaling, re-tagging, or otherwise "fixing" archive metadata beyond what's needed for a clean
  Jellyfin scan.
- Cleaning up the stale `/mnt/Media/docker/docker-compose.yml` stack (flagged as a follow-up, not
  this project's job).
- ~~GPU/hardware-accelerated transcoding~~ — **no longer out of scope as of 2026-09-08.** The
  design baseline this exclusion was written against ("no GPU exists yet") turned out to be stale;
  see Architecture decisions.

## Safety and credentials

- The tool never deletes or modifies a file inside the current library directly — only Radarr's or
  Sonarr's own delete-file API call does that, and only after the archive copy is verified.
- The in-progress temp output is staged in `work_dir`, never inside a Jellyfin-monitored library
  path (revised 2026-09-08 — originally staged inside the destination archive directory, which let
  Jellyfin's real-time monitor index the temp filename mid-encode; see Milestone 2 findings), and
  is only atomically renamed into its final archive path after verification — never an in-place
  overwrite, never a partially-written file visible at the final path.
- Any failure at any stage (probe, encode, verify, move, API call) aborts processing for that one
  file, leaves the original completely untouched, and logs the error. It never retries destructive
  steps automatically or guesses at a recovery action.
- Radarr/Sonarr/Jellyfin API keys are read from each app's own config on the host or from an
  environment variable at run time — never committed to Git, never written to the log files this
  tool produces.
- Runs are serialized via a lockfile; an overlapping scheduled run is skipped rather than started
  concurrently.
- Each scheduled run is capped at a configurable maximum file count so a misconfiguration cannot
  process the entire library unattended in one pass.
- No cron/systemd schedule is installed until Milestone 2's gate passes in full (movie side still
  outstanding as of 2026-09-08) — see Milestones below. The tool's code and config are deployed to
  TrueNAS and have processed real files under human supervision, which is exactly what Milestone 2
  asks for before that gate.

## Tooling decision

- `ffmpeg`/`ffprobe` for probing and transcoding — substituted for the referenced HandBrake per the
  note above. As of 2026-09-08, reached via small wrapper scripts
  (`scripts/video-archiver/bin/{ffmpeg,ffprobe}-jellyfin-wrapper.sh`) that translate host paths and
  `docker exec` into the already-running Jellyfin container's own `jellyfin-ffmpeg` build — not a
  separately downloaded static binary (superseded plan, see Architecture decisions).
- `requests` (Python) against the Radarr v3, Sonarr v3, and (as of 2026-09-08) Jellyfin REST APIs
  for candidate discovery, file deletion/unmonitor, and post-batch library rescans.
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

- [x] Install `ffmpeg`/`ffprobe` access under `/mnt/Media/data/tools/video-archiver/` — done
  2026-09-07/08, via the Jellyfin-container wrapper scripts rather than a separately downloaded
  static build (see Architecture decisions and Tooling decision).
- [x] Run the full pipeline — transcode, verify, move, Radarr/Sonarr delete-file call — against a
  real TV episode, with a human watching each step — done 2026-09-07/08, then extended (with
  explicit direction) to all 8 episodes of `Furious` Season 1 once the mechanics were validated on
  the first one.
- [x] **Movie side — done 2026-09-08**, via the `archive-now` tag override (Jason tagged
  `72 HOURS (2026)` through Radarr's own UI, rather than via age): source was a 2.08 GB MP4, already
  under `target_size_max_bytes`, so this exercised the movie code path (Radarr, `movies_current_root`,
  no season-grouping — genuinely different code from the TV runs above) *and* the relocate-as-is
  path together, both for the first time. Watched end-to-end: probe → straight copy (no transcode,
  `already_small_enough: true`) → verify → atomic rename into `archive-movies/72 HOURS (2026)/` →
  Radarr delete-file + unmonitor → leftover cleanup (source folder now gone entirely) → post-batch
  Jellyfin scan. 0 failures on the first attempt.
- [x] Confirm the archived file plays correctly — done 2026-09-08, after fixing the temp-file/
  Jellyfin-indexing bug (see Milestone 2 findings) that caused "Could not find file" on every
  playback attempt. Verified via the actual Jellyfin UI (per this repo's standing rule to verify
  in the live UI, not just a backend check), not just `ffprobe`.
- [x] Confirm Radarr/Sonarr no longer show the file as present, do not report it as missing or
  trigger a re-download — done 2026-09-08, after fixing the missing-unmonitor bug (see Architecture
  decisions). Confirmed via the Sonarr API (`monitored: false, hasFile: false`) for every archived
  episode, not just the file-list check.
- [x] Confirm the original file is gone from the current library only after every prior check
  passed — confirmed for all 8 `Furious` episodes; each was independently verified in the run log
  (`archived` event) before its Sonarr delete-file call.
- [x] Record actual achieved output size, encode duration, and CPU/memory load observed during the
  test — see Evidence log. GPU (`hevc_vaapi`) encode: ~21.6x real-time (~54 min episode in ~2.5
  min). Software (`libx265` 2-pass, pre-pivot): ~1h42m for the same file — recorded because it's
  the reason the GPU pivot happened, not because it's the shipped path.

### Gate

**Passed 2026-09-08 — both TV and movie sides now exercised.** The original gate text ("both test
files") anticipated needing one of each; TV passed cleanly on the first fully-fixed run (`S01E03`)
and again across the remaining 6 episodes, movie passed cleanly on its first-ever run (`72 HOURS`) —
no repeat failures after each earlier bug's fix landed, consistent with "fix the pipeline and repeat
the supervised test" rather than proceeding with a known issue. **Update 2026-09-08: the
movie-transcode path (the one gap noted above) is now exercised too** — `Ready or Not: Here I Come`
(32.5 GiB REMUX) went through a real GPU transcode, catching and fixing a real bug (the 11-audio-
track budget issue, see Architecture decisions) on the first attempt, then succeeding cleanly on
the second. Every code path in this pipeline — TV transcode, movie relocate-as-is, movie transcode
— has now been run against real data under supervision.

## Milestone 3 — Unattended schedule

- [x] Installed a TrueNAS-native Cron Job (`midclt call cronjob.create`, id `4`) — Monday-Saturday
  01:30, `--execute` mode, `max_files_per_run: 5` and `age_threshold_days: 122` from the already-
  deployed `config.json` (both set during Milestone 1/2 work, unchanged here). Runs via a wrapper
  script (`run-scheduled.sh`) that sources API keys from a mode-600 `.env` file rather than putting
  them in the cron command string itself, which would otherwise be visible via `ps aux` and
  TrueNAS's own cron job table (`midclt call cronjob.query`) while running.
- [x] Checked for overlap 2026-09-08: daily backup-pull rsync runs 04:30 every day (comfortable
  margin — 5 files at GPU-encode speed, ~5-6 min worst case each, finishes well under an hour);
  `jellyfin-integrity`'s Wednesday 03:00 run is also clear. **Deliberately skips Sunday entirely**
  (`dow: 1-6`) to avoid the weekly ZFS scrub (00:00 start, historically finishes ~02:46) — same
  reasoning `jellyfin-integrity` used to move off its own originally-proposed Sunday slot.
- [x] Added `check_video_archiver` to `scripts/doctor.sh` 2026-09-08, matching the
  `check_jellyfin_integrity` pattern: reads the latest `logs/run-*.jsonl`, fails and names each
  failed title by name (not just a count) if the last run had any failures, warns if no run has
  landed in 48+ hours. Verified against both a clean real run and a synthetic failure log before
  restoring the live log to its clean state.
- [ ] Run unattended for an initial observation period; review logs for unexpected failures or
  candidate-selection surprises before calling this milestone closed. **Explicitly not gated on
  first** — Jason directed installing the schedule and leaving it running unattended immediately
  rather than waiting for a review period first, given Milestone 2's gate (including the
  `archive-now` tag override) had just passed cleanly on real data. Noted here rather than silently
  treating the normal process as followed.

### Gate

**Schedule is live and running unattended as of 2026-09-08, on Jason's explicit direction, ahead of
this milestone's own originally-stated review-first gate.** The Lab Doctor check above is the
safety net in place of that initial observation period — it will surface any real failure by name
in the next daily 8:15am scheduled report. Still worth an eventual look at accumulated logs once a
few real (not synthetic) unattended runs have happened, the same way `jellyfin-integrity`'s
two-consecutive-clean-runs check is scheduled.

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
| Re-encoding an already-small file makes it bigger, not smaller | Skip transcoding (relocate as-is) when source size is already at/under `target_size_max_bytes` — added 2026-09-08 after this happened for real (`Furious` S01E07) |
| Delete-file leaves the parent monitored, risking Radarr/Sonarr re-downloading the archived file | Unmonitor via each app's own API in the same step as delete-file, using the movie's/episode's own id — added 2026-09-08 after confirming this was genuinely happening |
| Jellyfin indexes an in-progress temp file and ends up pointing at a name that no longer exists | Stage the temp output in `work_dir`, outside every Jellyfin library — added 2026-09-08 after this broke playback for real |
| Leftover Jellyfin `.trickplay` cache / empty folders keep a fully-archived series visibly present (with 0 episodes) in the current library | Clean up cache + empty directories after each archive, then trigger Jellyfin's actual Scan Media Library task at the end of a batch — added 2026-09-08 |
| `hevc_vaapi`'s default rate control ignores the target bitrate outright | Explicit `-rc_mode VBR` plus `-maxrate`/`-bufsize`, confirmed necessary by direct testing (30 Mbps vs. a 3.3 Mbps target without it) |

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
| 2026-09-07 | 2 | Ran full `--execute` pipeline against real `Furious` S01E04 (2.1 GB) with software `libx265` 2-pass `medium` | Both passes completed but failed at the final mux step (`.partial` extension bug); ~1h42m elapsed before the failure — source confirmed untouched, nothing written to archive/Sonarr state | Claude |
| 2026-09-07 | 2 | Investigated why encode was so slow (177% CPU on a 12-core box); found the Jellyfin container had a real, unused Intel Arc A380 GPU (`/dev/dri`, landed ~2026-09-05, undocumented) | Pivoted design to GPU (`hevc_vaapi`) via the Jellyfin container — see Architecture decisions | Claude |
| 2026-09-07 | 2 | Direct `ffmpeg` VAAPI test against real `S01E04`: default rate control | ~20-30 Mbps output vs. 3.3 Mbps target — confirmed `-rc_mode VBR` + `-maxrate`/`-bufsize` needed | Claude |
| 2026-09-07 | 2 | Re-ran full pipeline: `S01E04` then `S01E03`, GPU + `.partial`-extension fix + single-pass | Both succeeded end-to-end (transcode, verify, archive, Sonarr delete-file); ~3-4 min each | Claude |
| 2026-09-07 | 2 | Confirmed `S01E04`'s Sonarr entry after archiving: `monitored: true, hasFile: false` | Found and fixed the missing-unmonitor bug (see Architecture decisions); manually corrected this one episode via the Sonarr API before the code fix landed | Claude |
| 2026-09-07 | 2 | Ran remaining 6 `Furious` episodes (S01E01, E02, E05-E08) through the fixed pipeline, per Jason's explicit "move the whole season" direction | 6/6 succeeded, 0 failed; all 8 episodes of the season now archived, all originals removed, all correctly unmonitored | Claude |
| 2026-09-08 | 2 | Discovered `S01E07`'s archived size (1.43 GB) was larger than its source (0.29 GB) via the run log | Found and fixed the already-small-enough bug (see Milestone 2 findings); this one episode's original is already gone (Sonarr's delete-file removes the physical file) so left as-is per Jason's call — content intact, just larger than ideal | Claude |
| 2026-09-08 | 2 | Season-anchor + 4-month threshold change implemented (Jason's direction) in `candidates.py`/`config.example.json`; deployed | Not yet exercised against real data at the new threshold — will apply to the next real eligible batch | Claude |
| 2026-09-08 | 2 | Jason reported archived `Furious` episodes wouldn't play in Jellyfin | Found and fixed the temp-file/Jellyfin-indexing bug (see Milestone 2 findings); confirmed fixed via the live Jellyfin UI ("It's playing now") | Claude |
| 2026-09-08 | 2 | Jason reported an empty "Furious" entry still visible in the main Shows library | Found and fixed the leftover `.trickplay`/stale-library-state gap (see Milestone 2 findings); manually cleaned up the one already-affected case, then built the fix into the pipeline (`_cleanup_leftovers()` + automatic post-batch Jellyfin scan-task trigger) so future runs don't need manual follow-up | Claude |
| 2026-09-08 | 2 | Verified `Furious` fully gone from the main Shows library after the real Scan Media Library task (not `Items/Refresh`, which doesn't reconcile the filesystem) completed | Confirmed via the Jellyfin API | Claude |
| 2026-09-08 | — | Built the `archive-now` tag override (Jason's request): created the tag in both apps, added `archive_now_tag_label` to config, tag-resolution + eligibility-bypass logic in `candidates.py`. Tagged real movie `Obsession` (well under the age threshold) via the Radarr API, ran `--dry-run`, confirmed it was the sole candidate with correct paths, then reverted the tag | Feature validated end-to-end, dry-run only — nothing executed against a real file via this path yet. Tags exist in both apps, unused (0 titles tagged by Jason) | Claude |
| 2026-09-08 | 2 | Jason tagged `72 HOURS (2026)` via Radarr's own UI and asked for a supervised `--execute` run, watched step by step | First real movie through the pipeline, and the first real use of the `archive-now` override. 0 failures: relocated as-is (already under target size), verified, archived, source folder gone, Radarr `monitored: false, hasFile: false`, single clean Jellyfin entry at the archive path (105 min runtime, valid H.264/AAC streams, correct file size) confirmed via the Jellyfin API. Closes Milestone 2's previously-outstanding movie-side gate | Claude |
| 2026-09-08 | 3 | Jason directed installing the unattended schedule and leaving it running immediately, without a review-first observation period. Built a mode-600 `.env` + wrapper script (`run-scheduled.sh`) rather than putting API keys in the cron command string; verified the wrapper end-to-end while 0 candidates were eligible (a true no-op test); installed Cron Job id `4` (Mon-Sat 01:30, skips Sunday's ZFS scrub); added `check_video_archiver` to `doctor.sh`, verified against both a real clean log and a synthetic failure log | Schedule live; Lab Doctor is the safety net standing in for the skipped initial-observation-period gate — will name any real failure by title in the next daily report | Claude |
| 2026-09-08 | — | Jason tagged `Ready or Not: Here I Come` (32.5 GiB, a "Multi AVC" REMUX) and asked for a supervised `--execute` run to exercise the never-yet-tested real-transcode path (every prior run had either transcoded TV or relocated an already-small movie). First attempt failed cleanly at `verify_output` — found and fixed the 11-audio-track budget bug (see Architecture decisions); source was untouched throughout | First real GPU transcode of a movie: 34.9 GB → 1.77 GB, full 1080p retained, single English 5.1 track, all 3 English subtitles kept, non-English audio/subtitle tracks correctly dropped. Verified via direct `ffprobe` on the output, Radarr (`monitored: false, hasFile: false`), and the Jellyfin API (108 min runtime matching source exactly, single clean entry) | Claude |

## References

- [Plex-to-Jellyfin media migration project](<completed projects/Plex-to-Jellyfin-Media-Migration.md>)
- [Radarr API documentation](https://radarr.video/docs/api/)
- [Sonarr API documentation](https://sonarr.tv/docs/api/)
- [Jellyfin API documentation](https://api.jellyfin.org/)
- [ffmpeg documentation](https://ffmpeg.org/documentation.html)
- [ffmpeg VAAPI encoding wiki](https://trac.ffmpeg.org/wiki/Hardware/VAAPI)
- [HomeLab backup design](../05-Backups.md)
