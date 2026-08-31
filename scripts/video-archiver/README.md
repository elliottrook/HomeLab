# video-archiver

Downconverts aged Radarr/Sonarr current-library video (movies/TV) to roughly 1–2 GB and hands the
result to the `archive-movies`/`archive-tv` roots created by the Plex-to-Jellyfin migration
project. Design and safety rationale: [`docs/projects/Video-Library-Archiving.md`](../../docs/projects/Video-Library-Archiving.md).

**Do not deploy or run this against production yet.** Per that project's Milestone 1/2 gates, this
needs a reviewed dry run and a supervised single-file live test before it is installed on a
schedule.

## What it does, in order, per eligible file

1. Asks Radarr/Sonarr for every current-library file whose `dateAdded` is older than the age
   threshold.
2. Probes the source with `ffprobe`, computes a video bitrate and (if needed) a downscale target
   from the source's actual duration, so a 90-minute movie and a 22-minute episode both land in
   the configured size range instead of one fixed setting overshooting or undershooting.
3. Transcodes with a 2-pass `ffmpeg`/`libx265` encode into a temporary file inside the destination
   archive directory.
4. Verifies the result (duration matches the source within tolerance, file is a sane size, probes
   cleanly) before doing anything else.
5. Atomically renames the verified file into its final archive path.
6. Only then calls Radarr's `DELETE /api/v3/moviefile/{id}` (or Sonarr's `episodefile` equivalent)
   — the apps' own file-delete API, so their database and the filesystem never disagree.
7. Logs every candidate, decision, and outcome as JSON lines under `log_dir`.

Any failure at any step aborts just that one file, leaves the original completely untouched, and
is logged — it never retries a destructive step automatically.

## Setup

```bash
python3 -m venv /mnt/Media/data/tools/video-archiver/venv
/mnt/Media/data/tools/video-archiver/venv/bin/pip install -r requirements.txt
```

`ffmpeg`/`ffprobe` are not installed system-wide. Install the same vetted static build already used
for `beets` in the Plex-to-Jellyfin migration (johnvansickle.com, linked from ffmpeg.org — verify
sha/md5 against the publisher's manifest before extracting) into
`/mnt/Media/data/tools/video-archiver/bin/`, matching `config.example.json`'s `ffmpeg_bin`/
`ffprobe_bin` paths.

Copy `config.example.json` to a real config (e.g. `config.json`) and adjust paths if needed — the
defaults already match this repo's documented TrueNAS layout. **Do not put API keys in this file.**
They're read from the environment on purpose:

```bash
export RADARR_API_KEY="..."   # from /mnt/Media/appdata/radarr/config.xml
export SONARR_API_KEY="..."   # from /mnt/Media/appdata/sonarr/config.xml
```

## Usage

Dry run (default — lists candidates and the transcode plan for each, changes nothing):

```bash
venv/bin/python -m video_archiver.cli --config config.json
```

Live run, capped at the configured (or overridden) batch size:

```bash
venv/bin/python -m video_archiver.cli --config config.json --execute --max-files 3
```

Useful flags: `--library {movies,tv,both}`, `--max-files N`, `-v` for debug logging.

## Scheduling (Milestone 3 — not yet installed)

Once Milestone 2's supervised live test has passed, a systemd timer or cron entry runs the tool in
`--execute` mode on a schedule, e.g.:

```cron
0 4 * * * cd /mnt/Media/data/tools/video-archiver && venv/bin/python -m video_archiver.cli --config config.json --execute >> logs/cron.log 2>&1
```

Pick a time window that does not overlap other heavy scheduled TrueNAS work (backups, scrubs, and
— while it's still running — the Plex-to-Jellyfin migration's overnight jobs).

## Safety notes

- The tool never calls `rm` on a current-library file itself — only Radarr/Sonarr's own
  file-delete API does that, and only after the archive copy is verified on disk.
- A lock file (`lock_file` in config) prevents overlapping runs; if a run exits uncleanly, confirm
  no process is actually still running before removing it by hand.
- `max_files_per_run` bounds the blast radius of a single scheduled invocation.
