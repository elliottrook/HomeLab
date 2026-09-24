# Archive Library Duplicate Cleanup — 2026-09-24

> Requested by Jason: "delete all confirmed lower resolution and one copy of
> the same resolution files. Correct any mismatches you identified." Scope:
> Jellyfin **Archive Movies** (`/mnt/Media/data/archive-movies`) and
> **Archive TV** (`/mnt/Media/data/archive-tv`) on TrueNAS. The media has a
> single copy (the accepted boundary), so every deletion was verified first.
> The full action log and plan are kept privately at
> `~/lab/private-backups/media-cleanup/archive-dedupe-2026-09-24-*`.

## Method

1. **Read-only discovery:** an online SQLite backup of Jellyfin's
   `jellyfin.db`, taken to `/tmp` on TrueNAS and deleted afterwards. Copies
   were grouped by TMDB/IMDB (films) or series TVDB/TMDB plus season/episode
   (TV), falling back to title and year.
2. **Compared:** video width and height from `MediaStreamInfos`, runtime and
   size. Pairs whose runtimes disagreed were treated as identification
   errors, not duplicates.
3. **Before deletion:**
   - the file to keep had to exist, be non-empty and be a different file;
   - "identical" pairs had to match exact byte size and a SHA-256 of the
     first and last 8 MB;
   - same-resolution non-identical pairs were deleted only if runtimes
     agreed within 2 minutes and neither file had multi-part (CD/part)
     naming. This kept both halves of *Hogfather* and both cuts of *Narnia*
     and *Night at the Museum*;
   - within the same resolution, the larger (higher-bitrate) file was kept.
4. **Tags:** embedded tags (`ffprobe`) were used to identify mislabeled
   files.

## Result

| Category | Files | Size |
|---|---|---|
| Archive lower-res copies (Carry On Abroad, Harry Potter CoS 720p, Licence to Kill, Stan & Ollie SD, Transformers) | 5 | 11.1 GB |
| Archive lower-res copies of current Movies/Shows titles (Rick and Morty S03/S05/S06, Snowpiercer S1, The Crown S5–6, Shrek Forever After, Spider-Man Homecoming/Far From Home, The Boy and the Heron, plus re-identified Avengers: Endgame SD and Cannonball Run II 720p) | 66 | ~69 GB |
| Archive same-res copy of a current title (Avengers: Age of Ultron) | 1 | 14.4 GB |
| Identical duplicates, one copy kept (3rd Rock from the Sun, American Gods, 1923, ALF, A Perfect Planet, Bad Boys ×3, Austin Powers ×3, 12 Monkeys, Carry On Nurse/Sergeant, Miss Congeniality 2, The Terminator, and more) | 215 | 148.5 GB |
| Same-res smaller encodes (The Predator, Iron Man 3, Carry On Again Doctor, Doctor Who S00E10) | 4 | 11.8 GB |
| **Total deleted** (videos 291; 295 entries including their own sidecars) | | **255.2 GB of file data** |

- **Space returned: ~254.8 GB**, essentially all of the deleted file data.
  `Media/data` available went from 829.7 GB before the cleanup to 1,084.4 GB
  once ZFS finished freeing blocks in the background.
  - *Correction:* an immediate post-run reading showed only +177.9 GB and
    was wrongly attributed to shared storage (hard links or block clones).
    The shortfall was ZFS's asynchronous freeing still in progress.

## Snapshot removal (Jason: "No just delete please")

`Media/data@pre-plex-migration-20260830-205932` was destroyed on
2026-09-24.
- **What it was:** the rollback checkpoint for the Plex→Jellyfin migration,
  which closed on 2026-09-01. The Plex source media had lived on the
  Synology and was already deleted, so it was not part of this snapshot.
- **What it held:** files removed from the current libraries since
  2026-08-30:
  - download leftovers (~9 GB);
  - a *Rango* UHD `.iso` (64.6 GB);
  - music consolidation leftovers (6 GB);
  - full-quality originals of titles the video archiver later downconverted
    (~118 GB: *The Shawshank Redemption*, *Ready or Not: Here I Come*,
    *72 Hours*, *Furious* S1, and a *Doctor Who* "Season 4" mix);
  - titles with no other copy (~64 GB: *Departure* S2–S3, *Gone* (2026)
    S1, *Adults* (2025) 2 episodes, and the films *No Limit* (2022),
    *Fall for Me* (2025) and *Don't Say Good Luck* (2026)).
- Jason was shown this breakdown and chose deletion without restoring
  anything.
- **No holds or clones** existed. `zfs destroy` reported "will reclaim
  243G". Measured available space rose by **260.9 GB**, from 1,084.4 GB to
  1,345.4 GB. `usedbysnapshots` is now 0.
- The small `Media/ix-apps@pre-plex-migration-20260830-210033` snapshot
  (Jellyfin application data, 0 B used) was kept.

**Combined result for 2026-09-24:** `Media/data` available went from
829.7 GB to **1,345.4 GB (+515.7 GB)**. Usage dropped from 93% to **88%**
(`df`). `zpool list` capacity lags while freeing completes.

## Mismatch corrections (renames and moves; no overwrites)

- `Marvel/Marvel (1969).CD1–CD4.m4v`, identified by their tags, became:
  - `Ant-Man and the Wasp Quantumania (2023)/`
  - `Doctor Strange in the Multiverse of Madness (2022)/`
  - `Guardians of the Galaxy Vol. 3 (2023)/`
  - `Shang-Chi and the Legend of the Ten Rings (2021)/`
- `Marvel/Marvel (1969).mp4` was really *Avengers: Endgame* SD. It was
  deleted, since the 1080p copy is in Movies.
- The 720p `The Cannonball Run (1981).m4v` was really *Cannonball Run II*.
  It was deleted, since the 1080p copy is in Movies. The genuine 1981 SD
  file was renamed to `The Cannonball Run (1981).m4v`.
- `Home/Home.m4v` (94 min) became `Home (2015)/Home (2015).m4v`. It had been
  mis-matched to *Spider-Man: No Way Home*. This identification is by
  runtime; there were no tags.
- The 720p *Stan & Ollie* was moved out of `Herbie/` into
  `Stan & Ollie (2018)/`, after its SD copy was deleted.
- The Mr Bates vs The Post Office "S01E02/E03" 3-minute disc extras were
  moved to `extras/` and renamed "Disc 1 Title 3" and "Disc 2 Title 1".
- 16 folders left empty were removed.

## Left for Jason (not determinable automatically)

- `archive-movies/Pride/Pride.m4v` (109 min SD, no tags). Not *Pride &
  Prejudice (2005)*; the actual title is unknown.
- Doc Martin:
  - S06E08 `.m4v` (68 min, tagged "Doc Martin S10 D3"), probably a
    Series 10 item in the wrong slot;
  - S07E02 `.m4v` (92 min), likely two episodes in one file.
- Doctor Who S01E09 `.m4v` (69 min).
- All the Rivers Run S01E01 (51 min in the archive, 184 min in Shows).
- *Hogfather* CD1/CD2 (two parts, kept); *Narnia* and *Night at the Museum*
  (copies differ by ~3–4 min, both kept).

## Follow-up

Jellyfin needs a library scan to drop the deleted items and pick up the
renamed ones: Dashboard → Libraries → **Scan All Libraries**. The Archive
libraries' `EnableRealtimeMonitor` is not explicitly set.
