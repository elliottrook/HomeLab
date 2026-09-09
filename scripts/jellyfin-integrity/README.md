# jellyfin-integrity

Scans the Jellyfin Music library for orphaned tracks, featured-artist folder scatter, missing
album art, and candidate duplicate/gap-fill albums, using the same evidence standard (real
track-duration comparison, not filename guessing) developed and validated by hand in
2026-09-06/07. Also checks Jellyfin collection/playlist counts for the startup-task-deletion
regression, on any library. Design and safety rationale:
[`docs/projects/Jellyfin-Library-Integrity-Automation.md`](../../docs/projects/Jellyfin-Library-Integrity-Automation.md).

Deployed and scheduled on TrueNAS at `/mnt/Media/data/tools/jellyfin-integrity/` (this directory
is the source of truth in git; the TrueNAS copy is the deployed, running instance and carries its
own `config.json` and `reports/`, neither of which is committed here).

## What it does, per run

1. Forces a Jellyfin library scan and waits for it to finish. Jellyfin's own `/Items` catalog is a
   cache of the filesystem and was directly observed to still report a track under a folder that
   had already been deleted from disk in an earlier manual fix — every detector below reads that
   catalog, so a stale scan silently reintroduces false positives no matter how correct the
   detector logic is.
2. **Orphans**: any track with no `AlbumId` gets foldered into `Artist/Album (Year)/` using
   Jellyfin's own read of its `Album`/`AlbumArtist`/`ProductionYear` tags. Always safe — never
   overwrites, only moves a loose file into a new subfolder.
3. **Scatter**: albums split across more than one physical folder (excluding legitimate
   `Disc N`/`CD NN`/`Vinyl NN`/`Digital Media NN` subfolders) are auto-consolidated only when
   unambiguous — a small folder whose top-level name isn't a real Lidarr-managed artist, with no
   track-number collision against the real destination. Anything else is queued for review.
4. **Artwork**: albums with no `cover.jpg`/`cover.png`/`folder.jpg`/`folder.png` get one extracted
   from the first track carrying embedded art (FLAC `PICTURE`, MP3 `APIC`, MP4 `covr`). Purely
   additive.
5. **Duplicates/gap-fills**: comparably-sized candidate folder pairs (same or diacritic-normalized
   Artist+Album tag) are compared track-by-track via real decoded duration (±2s tolerance). A
   gap-fill (one side has tracks the other is missing entirely, no mismatches) auto-applies —
   moves the missing tracks in, never deletes. A confirmed duplicate (every shared track matches,
   no extras either side) is only ever written to the dated report; **nothing is ever deleted
   automatically** — see the project doc's *Still Crazy After All These Years* case for why.
6. **Collections/playlists**: current `BoxSet`/`Playlist` counts are compared against the last run's
   baseline (`reports/collections_baseline.json`); a drop of more than 10% is flagged. The
   `Clean up collections and playlists` task's own trigger list is also checked for drift back to
   enabled.
7. Writes a dated JSON + human-readable report to `reports/`, and (in `--apply` mode, if any
   action was taken) forces one more library scan so the results are visible immediately instead
   of waiting for the next scheduled run.

Every file-moving action writes a full manifest to `reports/` *before* touching anything. Nothing
in this tool ever calls a raw filesystem delete.

## Setup

Pure Python 3 standard library — no `ffprobe`/`mutagen`/pip install, deliberately (both were
removed from TrueNAS during the Plex-to-Jellyfin cleanup and should not be reintroduced;
`lib/duration.py` is a from-scratch FLAC/MP3/M4A reader, validated against synthetic
known-duration fixtures including ID3v2/ID3v1 tags, padding bits, and MPEG2/2.5 low-samplerate
frames).

Copy `config.example.json` to `config.json` (mode 600, **not committed to git** — it holds the
Jellyfin and Lidarr API keys). Fill in:

- `jellyfin.api_key` — a dedicated key, created via Dashboard → API Keys, named `jellyfin-integrity`.
  Persistent — unlike every other key used during this project's development, this one is not
  revoked after use, since it backs the recurring unattended job.
- `lidarr.api_key` — Lidarr's own existing key, reused read-only. Find it in the running
  container's actual mounted config (`docker inspect lidarr` to find the real `/config` volume —
  there was a stale, unmounted `config.xml` elsewhere on this host during development that had the
  wrong key).

## Usage

Dry run (default — reports findings, changes nothing):

```bash
python3 check_integrity.py --config config.json
```

Live run, applying safe corrections up to the configured (or overridden) action cap:

```bash
python3 check_integrity.py --config config.json --apply --max-actions 100
```

Exit codes: `0` clean, `2` fatal (bad key/host — fails loudly rather than silently skipping a
check), `3` a collection/playlist count alert or cleanup-task trigger drift was found (still
completed the run; needs human attention).

## Scheduling

Installed as a TrueNAS-native Cron Job (`midclt call cronjob.create`, id `2`), Wednesday 03:00 —
deliberately not Sunday, which carries the weekly ZFS scrub (starts 00:00, historically finishes
~02:46) and the daily 04:30 backup-pull rsync.

## Monitoring

`lab doctor`'s `check_jellyfin_integrity` (in `scripts/doctor.sh`) reads the latest report over
SSH and fails if the last run logged any action errors, a collection/playlist alert, or
cleanup-task trigger drift; warns if no run has landed in >200 hours (the weekly cadence plus
slack).

## Safety notes

- Duplicate-album *deletion* is never automatic — always a human-approved report, applied exactly
  as reviewed (never a fresh re-scan at approval time that could pick up something different).
- A lockfile (`reports/.lock`, `fcntl.flock`) prevents overlapping runs.
- `--max-actions` bounds the blast radius of a single run across every file-moving action
  combined (orphan foldering + scatter consolidation + gap-fills + art extraction).
- Scope is Music only. No movie/TV foldering or duplicate detection — no such problem has been
  observed in those libraries; only the collection/playlist count check applies to them.
