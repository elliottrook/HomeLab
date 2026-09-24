# Archive Large-File Compaction

> Status: Active — pilot passed; nightly schedule live from 2026-09-24 02:00
>
> Owner: Jason | Proposed and started: 2026-09-24 | Stream A — Autonomous
> within this document's scope, following Jason's direct instruction to
> create and run the process. Non-waivable stop conditions still apply.
>
> Builds on [Video Library Archiving](completed%20projects/Video-Library-Archiving.md)
> (GPU pipeline, lock, logging) and the
> [archive duplicate cleanup](../runbooks/Archive-Library-Dedupe-2026-09-24.md).

## Purpose and desired outcome

Jason (2026-09-24): "review the same archive folders and identify files larger
than 2.5 GB ... using the auto archiving process with the GPU ... create a
process to transcode all large files down ... maintain the highest resolution
as possible - 1080p is preferred."

The desired outcome:
- every file in `archive-movies`/`archive-tv` ends up at or below ~2.3 GB;
- resolution is kept wherever the size budget allows, and 4K becomes 1080p;
- HDR stays HDR;
- Jellyfin keeps the same items (collections, watch state);
- a rollback window protects the single-copy media while it's rewritten.

## Current state and evidence (2026-09-24, read-only inventory)

- **485 archive files over 2.5 GB, totalling 2,641.7 GB:**
  - 720p H.264: 257 movies (1,119 GB) and 53 TV episodes (167 GB);
  - 1080p: 44 movies H.264, 9 AV1, 3 HEVC, 1 DV5, 1 DV8; 45 TV episodes;
  - 2160p: 5 HDR10, 3 DV8, 2 DV7, 1 SDR;
  - SD: 57 H.264, 5 HEVC, 7 MPEG-2, 1 unprobeable.
- **Containers:** 267 `.m4v`, 143 `.mp4`, 68 `.mkv`, 5 `.m2ts`, 2 `.mpg`.
- **Pipeline available:** the Arc A380 via `docker exec jellyfin
  /usr/lib/jellyfin-ffmpeg` (`hevc_vaapi`, `scale_vaapi`, `tonemap_vaapi`,
  `ssim`; no VMAF).
- **Existing jobs:** archiver cron Mon–Sat 01:30, Jellyfin integrity check Wed
  03:00, Synology pull 04:30.
- **`Media/data`:** 1.35 TB available (88%) after the 2026-09-24 cleanup.

## Scope and exclusions

- **In scope:** re-encode archive files over 2.5 GB whose container can hold HEVC
  under the same name (`.mkv`, `.mp4`, `.m4v`: 477 files), in place at the
  identical path, one at a time, nightly.
- **Excluded, reported for manual handling:**
  - `.m2ts` (6) and `.mpg` (2): converting them would change the path;
  - Dolby Vision profile 5 (*Predators (2010)*): no HDR10 base layer;
  - the current libraries (Radarr/Sonarr-managed; the archiver owns those).
- **Not changed:** the archiver's own behaviour. Its per-axis `scale_vaapi min()`
  can distort scope 4K sources; that is logged as a follow-up.

## Authority model

| Fact | Authority |
|---|---|
| File content | The file at its path (Jellyfin re-reads it on the next scan) |
| Scope, decisions, evidence | This document |
| Per-file outcome | `work/compact-state.json` plus JSON-lines run logs |

## Design

- **Tool:** `scripts/video-archiver/video_archiver/compact.py`, deployed to
  `/mnt/Media/data/tools/video-archiver/`. It reuses the archiver's `Config`,
  lock, `RunLogger`, audio selection and Jellyfin scan client.
- **Resolution:** start at the smallest tier that contains the source (never
  upscale). The output box is computed with the aspect ratio preserved
  (3840×1600 → 1920×800).
- **Bitrate** (video kbps):

  | Tier | Box | Floor | Aim SDR/HDR | Ceiling SDR/HDR |
  |---|---|---|---|---|
  | 1080p | 1920×1080 | 1200 | 2000/2500 | 5000/6000 (raised from 3500/4500 after the pilot TV SSIM) |
  | 720p | 1280×720 | 700 | 1200/1500 | 2000/2500 |
  | SD | 1024×576 | 400 | 700 | 1200 |

  - The target is `max(budget at 1.5 GiB, aim)`, limited by the budget at the
    **2.3 GB cap** and by the tier ceiling.
  - The tier steps down only if the cap cannot fund its floor. Only one file
    (a very long 1080p title) steps down to 720p.
- **HDR:** PQ/HLG sources encode as 10-bit `main10` via `scale_vaapi` `p010`,
  with BT.2020 plus PQ/HLG tags. Dolby Vision 7/8 decode their HDR10 base layer.
- **Audio:** one track (default, else English, else first). Lossless or
  >640 kbps tracks become E-AC-3 384k (or AAC 192k stereo). Otherwise the track
  is copied (MP4-safe codecs only, else AAC).
- **Subtitles:** English only; MP4 keeps `mov_text`.
- **Chapters and metadata:** copied.
- **Verification before replacement:**
  - output ≤ cap and ≤ 80% of the source;
  - HEVC at the planned height;
  - duration within 2%;
  - an 8-second decode at 10%, 50% and 90% with zero errors;
  - source size and mtime unchanged since it was probed.
- **Replacement:** the output is encoded into `work/` on the same dataset, then
  `chown`/`chmod` to the original's and `os.replace` over the source (atomic).
- **Rollback window:** `zfs snapshot Media/data@archive-compact-<ts>` before
  the first replacement of each run. Snapshots older than 7 days are destroyed
  by the next run. Originals are recoverable from
  `/mnt/Media/data/.zfs/snapshot/<snap>/...` during that window, and space is
  freed as they expire.
- **Scheduling:** TrueNAS cron, root, 02:00 daily, running `run-compact.sh`.
  - It waits up to 90 minutes for the archiver's lock.
  - Largest files are processed first, and nothing new starts past 07:30 or
    when a file's estimated encode would overrun the deadline.
  - A Jellyfin library scan is requested after any replacements.

## Pre-start risk assessment

| # | Risk | Controls |
|---|---|---|
| R1 | Irreversible quality loss on single-copy media | Jason's instruction; conservative bitrates (1080p aims ≥2 Mbps); pilot with SSIM check; 7-day ZFS rollback |
| R2 | A bad encode replaces a good file | Multi-check verification; source-unchanged check; atomic replace; snapshot |
| R3 | Jellyfin loses collections or watch state | Same path and extension (item identity unchanged) |
| R4 | HDR/DV colour errors | DV5 skipped; HDR10 signalled; pilot includes a DV8 4K title |
| R5 | GPU contention with Jellyfin playback | 02:00–07:30 window, nice 15, one file at a time |
| R6 | Space not freed immediately | Snapshot retention: savings land about 7 days after each night's run |
| R7 | Archiver overlap | Shared lock with waiting |

## Milestones

- [x] **M0 — Inventory and design.** 485 files / 2.64 TB; dry run planned 477 files,
      2,413.8 GB → ~734 GB (**~1.68 TB saving**) with 8 skips.
- [x] **M1 — Supervised pilot (2026-09-24):** results in the evidence log.
      Jason's own playback check is recommended but not a gate.
- [x] **M2 — Unattended schedule:**
      - TrueNAS cron job #6, root, 02:00 daily, running `run-compact.sh`;
      - `compact` section in `config.json` (backup
        `config.json.bak-20260924-compact`);
      - `scripts/backup/video-archiver.sh` now also collects `run-compact.sh`
        and `work/compact-state.json`.
- [ ] **M3 — Monitoring:** Doctor warns on compaction failures or a stale run
      while candidates remain.
- [ ] **M4 — Completion:** all eligible files processed, skipped list handed to
      Jason, final space measured, cron removed or left as a guard for new
      oversized archive files.

## Evidence log

- **2026-09-24 — Inventory and dry run.** See M0. The dry run log is
  `logs/run-20260924T062941Z.jsonl` on TrueNAS.
- **2026-09-24 — Pilot.** Snapshot `Media/data@archive-compact-20260923-233906`
  was taken before the first replacement.

  | File | Before → after | Encode | SSIM vs original (30 s) | Notes |
  |---|---|---|---|---|
  | *Harry Potter and the Chamber of Secrets* (2160p DV8 HDR, MP4) | 20.27 → 2.22 GB | 404 s (~24×) | **0.9936** | 1920×800 `Main 10`, `yuv420p10le`, BT.2020/PQ; E-AC-3 5.1 |
  | *Jumanji (1995)* (720p H.264, `.m4v`) | 3.92 → 1.56 GB | 195 s (~32×) | **0.9900** | Same path, `hvc1` MP4 |
  | *Fear the Walking Dead* S02E12 (1080p H.264, `.mkv`) | 3.51 → 1.24 GB | ~2 min | **0.9757** | Grainy source at the old 3500k ceiling, so the ceiling was raised. English subs ×2 kept |

  - The first TV attempt was **correctly refused**. The decode spot-check
    treated the null muxer's "non monotonically increasing dts" notice after a
    seek as an error. The check was fixed to fail only on a non-zero exit or
    real decoder errors, and the retry passed.
  - The SSIM comparison copies the original out of `.zfs/snapshot`, because
    the Jellyfin container cannot see the snapshot directory.
  - **Throughput:** ~24–32× real time, so an estimated 40–50 GPU-hours for the
    477 files, about 8–10 nights in the 02:00–07:30 window.
- **Follow-ups:**
  - The archiver's own `scale_vaapi=w=min(iw,1920):h=min(ih,1080)` distorts
    non-16:9 sources above 1080p; its scaling should be fixed separately.
  - Manual handling is needed for the six `.m2ts`, two `.mpg` and one DV5
    (*Predators*) files.
  - M3 Doctor check.
