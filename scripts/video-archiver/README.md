# video-archiver

Downconverts aged Radarr/Sonarr current-library video (movies/TV) to roughly 1–2 GB and hands the
result to the `archive-movies`/`archive-tv` roots created by the Plex-to-Jellyfin migration
project. Design and safety rationale: [`docs/projects/Video-Library-Archiving.md`](../../docs/projects/Video-Library-Archiving.md).

**Do not schedule this unattended yet.** Per that project's Milestone 2 gate, a real movie file
still needs a supervised run before the milestone is considered closed (TV has been validated —
a full 8-episode season archived successfully). See the project doc's Evidence log for what's been
run so far.

## What it does, in order, per eligible file

1. Asks Radarr/Sonarr for every current-library file whose `dateAdded` is older than the age
   threshold — anchored on the **earliest** `dateAdded` within a season for TV, so a season ages
   out and moves as one unit rather than piecemeal per episode; per-file for movies.
2. If the file is already at or under `target_size_max_bytes`, skips straight to relocating it
   as-is (step 5) — re-encoding an already-small file can only make it bigger, confirmed by a real
   case where a 0.29 GB source became a 1.43 GB archive copy.
3. Otherwise, probes the source with `ffprobe`, computes a video bitrate and (if needed) a
   downscale target from the source's actual duration, then transcodes with a single-pass
   GPU-accelerated (`hevc_vaapi`) `ffmpeg` encode into a temporary file inside `work_dir` — outside
   every Jellyfin library, so Jellyfin's real-time monitor never sees the in-progress file (it did
   once, and kept a stale "Could not find file" entry after the real file was renamed into place).
4. Verifies the result (duration matches the source within tolerance, file is a sane size, probes
   cleanly) before doing anything else.
5. Atomically renames the verified file into its final archive path.
6. Calls Radarr's `DELETE /api/v3/moviefile/{id}` (or Sonarr's `episodefile` equivalent) — the
   apps' own file-delete API, so their database and the filesystem never disagree — **and then
   unmonitors the parent movie/episode** via the same app's API. Delete-file alone leaves it
   monitored with no file, which risks Radarr/Sonarr re-searching for and re-downloading the file
   just archived; confirmed this was a real risk, not a theoretical one.
7. Removes Jellyfin's leftover per-file `.trickplay` thumbnail-preview cache folder (delete-file
   doesn't touch it) and climbs upward removing any directory left empty, stopping at the
   configured current-library root.
8. Logs every candidate, decision, and outcome as JSON lines under `log_dir`.

Once a whole batch finishes (not per-file), triggers Jellyfin's actual "Scan Media Library"
scheduled task — confirmed necessary: `POST /Items/{id}/Refresh` only refreshes metadata for items
already known, it does not reconcile the filesystem, so it never cleared a fully-emptied series
out of the main library on its own.

Any failure at any step aborts just that one file, leaves the original completely untouched, and
is logged — it never retries a destructive step automatically.

## Setup

Requires `python3` and `requests` (already present system-wide on TrueNAS — no venv needed):

```bash
pip install -r requirements.txt   # only if requests isn't already available
```

`ffmpeg`/`ffprobe` are reached through `bin/{ffmpeg,ffprobe}-jellyfin-wrapper.sh` — these
translate a host path under `host_data_root` to the Jellyfin container's own `/media` mount and
run it via `docker exec jellyfin /usr/lib/jellyfin-ffmpeg/{ffmpeg,ffprobe}`. This reuses a build
the lab already runs and trusts (with hardware VAAPI encoding already compiled in) instead of
downloading a separate static binary. No install step needed as long as the `jellyfin` container
is running with `/dev/dri` passed through (`docker inspect jellyfin` — already the case here).

Copy `config.example.json` to a real config (e.g. `config.json`) and adjust paths if needed — the
defaults already match this repo's documented TrueNAS layout. **Do not put API keys in this file.**
They're read from the environment on purpose:

```bash
export RADARR_API_KEY="..."     # from Radarr's config.xml (docker volume, not appdata — see project doc)
export SONARR_API_KEY="..."     # same, for Sonarr
export JELLYFIN_API_KEY="..."   # from Jellyfin's own API key management
```

## Usage

Dry run (default — lists candidates and their planned archive destination, changes nothing; does
**not** call `ffprobe`, so it works even before `ffmpeg`/`ffprobe` access is set up):

```bash
python3 -m video_archiver.cli --config config.json
```

Live run, capped at the configured (or overridden) batch size:

```bash
python3 -m video_archiver.cli --config config.json --execute --max-files 3
```

Useful flags: `--library {movies,tv,both}`, `--max-files N`, `-v` for debug logging.

## Scheduling (Milestone 3 — not yet installed)

Once Milestone 2's gate fully passes (movie side still outstanding), a systemd timer or cron entry
runs the tool in `--execute` mode on a schedule, e.g.:

```cron
0 4 * * * cd /mnt/Media/data/tools/video-archiver && python3 -m video_archiver.cli --config config.json --execute >> logs/cron.log 2>&1
```

Pick a time window that does not overlap other heavy scheduled TrueNAS work (backups, scrubs).

## Safety notes

- The tool never calls `rm` on a current-library file itself — only Radarr/Sonarr's own
  file-delete API does that, and only after the archive copy is verified on disk.
- A lock file (`lock_file` in config) prevents overlapping runs; if a run exits uncleanly, confirm
  no process is actually still running before removing it by hand.
- `max_files_per_run` bounds the blast radius of a single scheduled invocation.
- GPU encoding (`hevc_vaapi`) requires explicit `-rc_mode VBR` plus `-maxrate`/`-bufsize` — its
  default rate control ignores the target bitrate outright (confirmed: ~20-30 Mbps output against
  a 3.3 Mbps target without it).
