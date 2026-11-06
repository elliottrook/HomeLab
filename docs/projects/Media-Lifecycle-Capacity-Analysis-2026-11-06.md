# Media lifecycle bitrate and capacity analysis — 2026-11-06

> Read-only analysis and policy candidate. No archive ceiling, ARR profile, media file or schedule was changed by this analysis.

> **Later decision:** Jason chose 1080p with the 45 MB/min soft reference for
> both movies and TV, a three-month Current period, and requested a 60–62%
> retention plan. The earlier four-month delay and 720p/stereo TV scenario in
> this document are historical alternatives. See the
> [retention and recall plan](Media-Lifecycle-Retention-and-Recall-Plan-2026-11-06.md).

## Scope and provenance

This uses the live TrueNAS `Media` pool, administrator-scoped Jellyfin media metadata, physical Archive file sizes, and Radarr/Sonarr import histories as of 2026-11-06. Repository context is [Media-Lifecycle-Redesign.md](Media-Lifecycle-Redesign.md), [Archive-Large-File-Compaction.md](Archive-Large-File-Compaction.md), the [old compactor](../../scripts/video-archiver/video_archiver/compact.py), and the [completed RAIDZ widening record](completed%20projects/Media-RAIDZ-Widening.md). The old archiver and compactor schedules remain disabled.

Decimal units: 1 MB = 1,000,000 bytes; 1 TB = 1,000,000,000,000 bytes. `MB/min = total encoded file bytes / 1,000,000 / runtime minutes`, including one audio track, all English subtitles and container overhead. `MB/min / 7.5` gives total Mb/s.

## Measured inventory

| Physical Archive | Files | Runtime coverage | Total measured runtime | Apparent file size | Mean runtime | Median indexed runtime |
|---|---:|---:|---:|---:|---:|---:|
| Movies | 990 | 989 | 113,229 min | 2.099 TB | 114.49 min | 111.61 min |
| TV episodes | 5,014 | 5,013 | 193,647 min | 3.164 TB | 38.63 min | 42.99 min |
| Combined | 6,004 | 6,002 | 306,876 min | 5.263 TB | — | — |

Seven physical files lacked Jellyfin items, but direct Jellyfin-container `ffprobe` supplied their durations. One indexed 2.318 GB movie MKV and one indexed 0.296 GB TV M4V lacked a Jellyfin runtime and failed that probe. They need separate health checks; they are excluded from modeled runtime. The nine-file exception set has negligible effect on aggregate sizing but is a real integrity hold. Source file extensions were inventoried; no other video extension appeared in these Archive roots.

Indexed resolution is mostly below the requested standard: movies have 526 SD, 367 720p, 84 1080p, nine 2160p+ and two unknown; TV has 3,179 SD, 1,161 720p, 667 1080p, one 2160p+ and one unknown. Jellyfin reported a 5.1-or-higher track on 379 movies and 1,738 episodes; English subtitle tracks on 94 movies and 597 episodes. The subtitle counts do not prove whether separate sidecars are available. Upscaling or upmixing these sources would not meet the genuine-quality requirement. Full 1080p/5.1 normalization therefore assumes genuine replacement sources for much of the library.

## Candidate quality budget

**Candidate: 45 MB/minute as a soft planning reference**, not a forced target or hard quality ceiling, for a 1080p HEVC/Main10 video plus one English 5.1 E-AC-3 track at approximately 640 kb/s and all English subtitles. This is 6.0 Mb/s total and leaves approximately 5.36 Mb/s for video. Preserve HDR signaling when the source is genuinely HDR; do not manufacture HDR, 5.1 or resolution from a lesser source. If one existing Atmos track must remain Atmos, verify the codec and playback separately rather than silently flattening it to ordinary 5.1.

The 640 kb/s audio allowance is a quality-oriented planning choice within [Dolby Digital Plus's supported rate range](https://professional.dolby.com/technologies/dolby-digital-plus), not a claim that every source or player needs precisely that rate.

[Apple's HLS authoring specification](https://developer.apple.com/documentation/http-live-streaming/hls-authoring-specification-for-apple-devices/) gives illustrative 1080p HEVC video variants at 4.5–5.8 Mb/s for SDR and 5.4–7.0 Mb/s for HDR at 30 fps, and says these are starting points to evaluate against actual content. The candidate sits near the middle of its SDR range and the lower end of its HDR range after audio. [HandBrake's quality guidance](https://handbrake.fr/docs/en/latest/technical/video-cq-vs-abr.html) explains why constant-quality encoding should decide final size rather than forcing every title to a bitrate. Grain, motion, codec, frame rate, HDR and subtitle format may require more or less. Flag outputs materially above 45 MB/min for review; accept a larger exception when the verified picture/audio/subtitle gate needs it. Avoid re-encoding a good file solely to meet the reference.

At 45 MB/min, a mean Archive movie would be 5.15 GB, a mean episode 1.74 GB, and a 180-minute feature 8.10 GB. A 5 GB movie cap instead allows 43.7 MB/min at the mean movie runtime but only 27.8 MB/min for a three-hour feature; the same cap allows 129.4 MB/min for the mean TV episode. The fixed cap is inconsistent across runtimes.

## Two distinct Archive scenarios

| Soft reference | Equivalent total Mb/s | Uniform-size **all-1080p/5.1** model | Change from current 5.263 TB | Mean movie / episode |
|---:|---:|---:|---:|---:|
| 35 MB/min | 4.67 | 10.741 TB | +5.478 TB | 4.01 / 1.35 GB |
| **45 MB/min** | **6.00** | **13.809 TB** | **+8.547 TB** | **5.15 / 1.74 GB** |
| 55 MB/min | 7.33 | 16.878 TB | +11.615 TB | 6.30 / 2.12 GB |

This is `306,876 measured minutes × reference`, split at 45 MB/min into 5.095 TB movies and 8.714 TB TV. It is a planning **scenario**, not a promised encoder output: constant-quality files vary. It assumes every title has a genuine source meeting the requested 1080p/5.1 standard, which is false today. It also excludes the two unmeasurable runtimes and future files.

A different question is how much a rate rule could save from **today's** Archive while keeping all below-reference files unchanged. Of 987 indexed movies with runtimes, only 22 exceed 45 MB/min; of 5,008 indexed episodes, only 118 exceed it. Trimming those files exactly to 45 MB/min would mathematically save at most about **0.661 TB of movies plus 0.041 TB of TV** before quality, subtitle, container and rollback checks. That is an optimistic upper bound, not an authorized rewrite or achievable guarantee. A lower 25 MB/min threshold would catch 814 episodes, but leaves only 2.69 Mb/s video after a 640 kb/s audio track and is a poor universal 1080p HDR quality rule. Most existing episodes are already compact because their sources are lower resolution.

## Acquisition and pool runway

`Media` is ONLINE, with 39.978 TB raw pool size, 16.766 TB raw allocated (41%), and **15.322 TB ZFS available** to datasets. The `Media/data` referenced size rose from 9.039 TB in its 2026-10-17 snapshot to 10.389 TB now: **1.350 TB in 20.52 days, about 1.97 TB per 30 days**. The 2026-10-20 snapshot yields about 2.10 TB per 30 days. These observed net growth rates include all `Media/data` content, not just video.

The current physical media root occupies about **5.388 TB** by apparent file size in addition to the **5.263 TB** Archive. These apparent sizes are not identical to ZFS referenced bytes because of filesystem compression, metadata and allocation accounting.

Last 30 days of ARR history contain 63 Radarr movie-file imports (1.266 TB) and 701 distinct Sonarr episode-file imports (1.253 TB), or **2.519 TB gross**. ARR file-deletion events sum to approximately 0.314 TB, leaving **2.205 TB event-level net**; this is not exact pool accounting because other writes, snapshots and application data are outside ARR. The same imports correspond to approximately 7,053 movie minutes and 29,351 episode minutes with known ARR runtimes (six Sonarr runtimes missing). At 45 MB/min, those known 36,404 minutes would occupy about **1.638 TB**, if all were accepted at the reference. This assumes the mix and import count persist, and it ignores the four-month Current residence before Archive eligibility. Recent seven- and fourteen-day volumes are lower than the thirty-day average, so forecasts use the observed 2.0 TB/month dataset trend as a central case, not a precise prediction.

[TrueNAS's ZFS primer](https://www.truenas.com/docs/references/zfsprimer/) recommends adding capacity before a pool reaches 80% for write performance and replacement headroom. Converting the current raw-to-available ratio (0.660) to a planning estimate leaves about **10.04 TB usable growth before 80% raw allocation**, versus 15.32 TB until nominal full. This ratio is approximate and can change with recordsize, compression and pool layout.

| Scenario, as if immediate | Archive size | Usable growth before ~80% raw | Usable space until nominal full | At 2.0 TB/month: ~80% / nominal full |
|---|---:|---:|---:|---:|
| Keep present Archive | 5.263 TB | 10.04 TB | 15.32 TB | ~5.0 / ~7.7 months |
| Replace all at 35 MB/min | 10.741 TB | 4.57 TB | 9.84 TB | ~2.3 / ~4.9 months |
| **Replace all at 45 MB/min** | **13.809 TB** | **1.50 TB** | **6.78 TB** | **~0.75 / ~3.4 months** |
| Replace all at 55 MB/min | 16.878 TB | already past 80% | 3.71 TB | already past 80% / ~1.9 months |

At the central trend, an immediate 45 MB/min rebuild would reach the 80% planning point around late November 2026 and nominal full around mid-February 2027; both dates have substantial uncertainty. Without the rebuild, the corresponding rough points are early April and late June 2027. A range of about 1.7–2.2 TB/month shifts the 45 MB/min case to roughly 0.7–0.9 months until 80% and 3.1–4.0 months until nominal full.

**Do not perform a bulk rebuild at present capacity.** If all new normalized copies were staged while all originals remained, the transient extra 13.809 TB would leave only about 1.51 TB of current ZFS available capacity before accounting for snapshots and downloads. The four-month Current delay also means recent large acquisitions keep consuming space before any Archive optimization can reclaim it. Use bounded replacements with verified checkpoints, and revisit capacity expansion or acquisition pace before promising a full genuine 1080p/5.1 library.

## Decision status

The 45 MB/min reference is proposed for Jason's review. The current exact 5,000,000,000-byte Archive ceiling remains active in the project plan until a new rule is adopted. The numbers show that a per-minute **budget is more coherent** than a fixed per-file ceiling, but neither rule by itself preserves quality or shrinks an already compact SD/720p library. The implementation should use quality-led encoding, compare the verified output to its source, and report exceptions rather than chase a file-size target.

## Alternative: 1080p/5.1 movies, 720p/stereo TV

Jason requested a second, read-only model with the same 45 MB/min movie reference but a 720p stereo TV standard. **Candidate TV reference: 24 MB/min**, including one English AAC stereo track at approximately 192 kb/s and English subtitles. That is 3.20 Mb/s total and leaves about 3.01 Mb/s for video. [Apple's illustrative HLS table](https://developer.apple.com/documentation/http-live-streaming/hls-authoring-specification-for-apple-devices/) gives 720p HEVC SDR video variants at 2.4 and 3.4 Mb/s and stereo AAC up to 160 kb/s. The 192 kb/s audio allowance is a modest quality choice beyond that delivery table, not a compatibility requirement. HDR/high-motion TV may require an exception above 24 MB/min; encode to verified quality rather than force the rate.

| Scenario | Movies | TV | Combined Archive | Change from present Archive | Usable growth before ~80% raw / nominal full |
|---|---:|---:|---:|---:|---:|
| Present physical Archive | 2.099 TB | 3.164 TB | 5.263 TB | — | 10.04 / 15.32 TB |
| All 1080p/5.1 at 45 MB/min | 5.095 TB | 8.714 TB | 13.809 TB | +8.547 TB | 1.50 / 6.78 TB |
| **Movies 45; TV 720p/stereo at 24 MB/min** | **5.095 TB** | **4.648 TB** | **9.743 TB** | **+4.480 TB** | **5.56 / 10.84 TB** |

The tiered model uses the same 113,229 measured movie minutes and 193,647 episode minutes. The average Archive episode would be about 0.93 GB; an hour of TV about 1.44 GB. The uniform-tier model is 4.067 TB smaller than the all-1080p/5.1 model, but still larger than today's Archive because thousands of current files are SD/720p and small.

If 24 MB/min were applied only as a rate trigger to existing TV, **845 of 5,008** indexed episodes with usable runtimes exceed it. Reducing exactly those files to the reference could save at most **0.416 TB** before quality checks. Together with the 45 MB/min movie trigger's idealized 0.661 TB, the mathematical maximum current-library saving is 1.077 TB. This is not an expected real saving: existing 1080p and 5.1 TV may require video downsampling or audio downmixing, and a verified quality gate could reject many candidates.

The present TV Archive includes **668 indexed files above 720p** and **1,738 with a 5.1-or-higher track**. A strict 720p/stereo policy would deliberately reduce those properties. Another **3,179 indexed TV episodes are SD**, so they cannot become genuine 720p by encoding alone; source upgrades would be needed. Only 597 indexed TV episodes report an English subtitle track. These cohorts overlap and should not be added together. The policy decision must distinguish a standard for **future acquisitions** from permission to downgrade playable existing files.

At the observed 2.0 TB/month dataset growth, an immediate tiered rebuild leaves about **2.8 months until the 80% planning point** and **5.4 months until nominal full**, roughly late January and April 2027 from 2026-11-06. Without the rebuild the corresponding central estimates remain 5.0 and 7.7 months. In the last 30 days ARR imported about 7,053 movie minutes and 29,351 episode minutes with known runtimes; the tiered references would represent approximately **0.317 + 0.704 = 1.022 TB** of eventual Archive files for that volume, versus about 2.519 TB gross imports. This is an optimistic stabilized-flow illustration, not an immediate pool saving: files spend four months in Current, six Sonarr runtimes were missing, and the historical imports include upgrades/backfill. The first months after a rebuild could still grow near the observed 2.0 TB/month rate.

This alternative is **not adopted**. No media, ARR profile, scheduler or Archive size rule was changed by the analysis.

## Corrected incoming-media runway — 2026-11-06

The earlier runway table intentionally extended the **observed 2.0 TB/month unoptimized pool growth** indefinitely. It did not credit smaller retained files from the proposed tiered optimizer. Jason asked for a corrected estimate. Read-only ARR history and current title/episode runtimes now allow a direct 30-day cohort model:

| Last 30 days | Import events / unique files | Imported size | Known runtime | Modeled retained size at movie 45 / TV 24 MB/min |
|---|---:|---:|---:|---:|
| Movies | 63 | 1.266 TB | 7,053 min | 0.296 TB |
| TV episodes | 701 distinct files | 1.253 TB | 29,351 min in 695 files | 0.597 TB |
| **Total** | **764** | **2.519 TB** | **36,404 min** | **0.893 TB**, plus 0.017 TB of episodes without ARR runtimes |

For each known-runtime imported file, the model uses `min(imported bytes, runtime minutes × tier MB/min)` so an already small source is never enlarged to meet a budget. Nine movie and 298 episode imports were already below their respective budgets. This is a theoretical size result, not proof that every file can pass the quality/HDR/audio/subtitle/playback gates. In the last 60 days, the same method gives 1.956 TB for that two-month cohort, or about 0.978 TB/month. The seven- and fourteen-day cohorts imply lower rates, so 0.9–1.2 TB/month is a **planning range for stabilized retained media growth**, with approximately 1.0 TB/month as a central illustration. Non-media writes, retained snapshots, true quality exceptions and a change in acquisition volume could push above it. ARR replacement events mean retained bytes are not identical to net pool growth.

The Current/Archive four-calendar-month rule governs **view classification**. Whether optimization happens on intake or only when a file becomes Archive is still an implementation choice. Do not assume the age rule itself requires waiting four months to encode. The tiered all-Archive scenario leaves approximately 5.56 TB of estimated usable headroom before 80% raw pool allocation and 10.84 TB until nominal full:

| Hypothetical path after immediate tiered Archive rebuild | Growth assumption | ~80% raw planning point | Nominal full |
|---|---|---:|---:|
| Optimize new imports promptly and remove original after verified replacement | 0.9–1.2 TB/month retained media planning range | ~4.6–6.2 months | ~9.0–12.0 months |
| Keep large new files through four months of Current, then optimize at eligibility | ~2.0 TB/month for four months, then ~1.0 TB/month | ~2.8 months | ~6.8 months |

The second row is a simplifying delay model: the 80% point arrives before the first four-month cohort can be compressed. In practice older Current backlog may become eligible sooner, and quality failures or ARC/snapshot occupancy may change both rows. The **immediate rebuild** itself is only a mathematical scenario; much of the existing SD/stereo Archive lacks genuine replacement sources, and staging the entire new library at once would be unsafe. If the Archive is *not* rebuilt, keeping its current 5.263 TB size and optimizing future imports promptly would instead leave roughly 10.04 TB before the 80% planning point: about 8.4–11.2 months at the 0.9–1.2 TB/month range, before other pool growth.

This correction supersedes use of the earlier 2.0 TB/month rate as a long-term forecast **after** optimization is actually deployed and measured. Until then, observed pool growth remains the operational rate to monitor.
