# News Aggregator Phase 3 — Audio Digest

> Status: Graduated — all milestone completion gates passed. `/digest`
> now plays a local-Piper-narrated MP3 briefing of the latest digest run,
> confirmed working by Jason on both desktop and his own iPhone after two
> real-screenshot-driven mobile rendering fixes. HomeLab Doctor gained
> real coverage for a silent Piper/ffmpeg failure that previously had none.
> **Updated 2026-09-15/16** after Jason listened to a real full recording:
> added a spoken intro/outro and a silence gap between stories; evaluated
> two candidate male voices at his request and, on his direct feedback,
> kept the original `en_US-lessac-medium` voice unchanged — see Design
> decisions and the evidence log below.
>
> Project owner: Jason
>
> Proposed: 2026-09-15
>
> Started: 2026-09-15
>
> Completed: 2026-09-15
>
> Authorization stream: **Stream A — Autonomous**, granted by Jason
> 2026-09-15 in this project's own conversation ("Let's get it done now. I
> like all your suggestions"), per the per-project authorization mechanism
> in `CLAUDE.md` and the `Project-Creation-Standard`. This is a new,
> separate grant — Phase 2's Stream A authorization does not carry over,
> per `CLAUDE.md`'s own rule that each project needs its own explicit
> grant.
>
> No non-waivable checkpoint is named for this phase: it introduces no new
> guest, no new credential, no new firewall rule, and no new persistent
> egress target (the voice model is a one-time download over VLAN 70's
> already-approved broad egress). If a real safety/privacy trade-off
> surfaces unexpectedly, the general `CLAUDE.md` rule to stop and ask still
> applies regardless of Stream A.
>
> Predecessor: [News Aggregator Phase 2 — Digest, Sections and Source
> Requests](News-Aggregator-Digest-and-Sections.md), graduated 2026-09-15.

## Purpose and desired outcome

Jason asked for an audio read of the twice-daily digest — narrate the
latest digest run (headline plus abridged summary per story) as a single
downloadable/streamable briefing, playable from the `/digest` page. Chosen
specifically because Jason is separately planning to use Piper for a
future Home Assistant project, so this doubles as a real trial of that
same tool.

## Design decisions

- **Spoken intro/outro, added 2026-09-16 after listening to a real full
  recording.** Intro: "This is your morning/evening briefing for
  [Weekday, Month Day]." Outro: "That was your daily briefing for
  [date]." Morning/evening and the date are both computed from the
  generation timestamp using the same fixed `BC_OFFSET = timedelta(hours=
  -7)` convention `app.py`'s `get_audio_meta()` already established (BC no
  longer observes DST) — deliberately not a second, independent
  timezone-handling approach.
- **Per-story silence gap, added 2026-09-16 for the same reason.** The
  original v1 script synthesized the entire script (intro + every story)
  in one Piper call, relying on Piper's own sentence/newline pausing alone
  — real listening showed stories ran into each other. Rebuilt as: intro,
  each story, and the outro are now separate Piper calls, concatenated via
  ffmpeg's `concat` demuxer with a fixed 1-second silence clip (`ffmpeg -f
  lavfi -i anullsrc=r=22050:cl=mono`, matching Piper's own probed output
  format exactly — `pcm_s16le`, 22050 Hz, mono — so `-c copy` concatenation
  is lossless and fast) inserted between each. A plain timed silence gap
  was chosen over a spoken "next story"-style bridge phrase to avoid
  repetition fatigue across a 13+ story briefing, and to avoid a new
  non-text audio asset dependency.
- **Voice change requested, evaluated, and declined — 2026-09-16.** Jason
  asked for an English male voice. Rather than picking one unilaterally,
  generated real samples of two candidates (`en_US-ryan-medium` and
  `en_GB-alan-medium`, both downloaded from the same Hugging Face
  `rhasspy/piper-voices` source as the original voice) narrating the same
  real 13-story digest with the new intro/pause/outro structure, and sent
  both to Jason to listen to before changing anything live — matching this
  project's own established Milestone-1 precedent of never committing to
  a voice without a real confirmed sample. Jason didn't like either and
  asked to keep the original `en_US-lessac-medium` voice. Both candidate
  models and their test-output directories were deleted afterward; nothing
  in production was ever pointed at either candidate.
- **Piper, not a cloud TTS API.** Local, offline, no new credential or
  egress target beyond the one-time voice-model download. Matches this
  project's own established preference for local `aster-llama` synthesis
  over any cloud alternative.
- **Prebuilt Piper binary, not the `piper-tts` PyPI package.** Avoids
  pulling `onnxruntime` and its native dependencies into the venv; the
  standalone release is a single self-contained executable.
- **`en_US-lessac-medium` voice**, sent to Jason as a real generated
  sample before building anything further around it; confirmed acceptable
  ("it will be fine").
- **`length_scale 1.15`** (Piper default 1.0, higher = slower) — Jason
  asked for the pace slowed down after hearing the first real sample.
- **One combined narration per digest run, not per-story clips** — a
  "morning/evening briefing," not a jukebox. Simpler to build and matches
  how the digest itself is already framed as one twice-daily event.
- **Only the latest `digest_run`'s entries are narrated**, not the full
  rolling `/digest` page history (which can show up to 40). Narrating
  everything currently on the page would make the briefing longer with
  every passing digest cycle instead of staying a bounded "what's new."
- **Deviation notes are not narrated** — they read fine on a page but
  don't flow naturally when spoken aloud; only headline + abridged summary
  make up the script.
- **MP3, not raw WAV** — `ffmpeg`/`libmp3lame` transcodes Piper's WAV
  output. A real 13-story briefing was measured at 4.2MB in MP3 vs. what
  would have been several times that in WAV — meaningful for anyone
  listening over cellular via the Tailscale route rather than at home.
- **One fixed file, overwritten each run**, matching `digest_entries`'
  own replace-not-accumulate design — no unbounded audio history to prune
  or grow the backup footprint.

## Milestone 1 — Piper install and voice validation — **complete 2026-09-15**

- [x] Installed the prebuilt Piper binary release (`2023.11.14-2`,
      `piper_linux_x86_64.tar.gz`) to `/opt/piper/piper/` on LXC 114 — no
      new guest, reuses existing compute. Confirmed real resource
      headroom first rather than assuming (1.9GB RAM free, 14GB disk free
      before starting).
- [x] Downloaded the `en_US-lessac-medium` voice model (63MB .onnx +
      config) from Hugging Face over VLAN 70's already-approved broad
      egress — no firewall change needed.
- [x] Real end-to-end test: synthesized a genuine test sentence, confirmed
      valid WAV output (`file` command: RIFF/WAVE PCM, 22050 Hz mono),
      measured a 0.165 real-time factor (~6x faster than real-time on this
      LXC's 2 allocated cores, no GPU needed).
- [x] Sent the real generated audio to Jason directly (not just described
      it) before building the rest of the pipeline around this voice
      choice, since voice quality is inherently subjective.

## Milestone 2 — Audio synthesis pipeline — **complete 2026-09-15**

- [x] `audio_digest.py`: queries the most recent `digest_run`'s entries,
      builds a plain-text script (intro line, then headline + abridged
      summary per story, deviation notes excluded), pipes it to Piper,
      transcodes the WAV output to MP3 via `ffmpeg`, writes
      `static/digest-audio/latest.{mp3,json}`, deletes the intermediate
      WAV.
- [x] Chained into the existing digest schedule via a new
      `run_digest.sh` wrapper (`digest.py` then `audio_digest.py`, each
      independent — matching `run_pipeline.sh`'s own established
      "one stage failing doesn't block the others" convention) and
      updated `news-aggregator-digest.service`'s `ExecStart` accordingly.
      The 05:15/17:15 schedule itself is untouched.
- [x] Verified against real data twice: an initial 6-story briefing
      (1.9MB MP3) and, after the Phase-2-adjacent source expansion
      surfaced more cross-outlet stories, a 13-story briefing (4.2MB MP3)
      — both sent to Jason directly.
- [x] Installed `ffmpeg` via `apt` (a standard Debian package, not an
      unusual dependency) specifically for MP3 transcoding.

## Milestone 3 — UI integration — **complete 2026-09-15**

- [x] Added an audio player card to the top of `/digest`, reading
      `latest.json` for story count and generation time (`get_audio_meta()`
      in `app.py`); renders nothing if no digest has run yet, rather than
      a broken player pointing at a missing file.
- [x] Real mobile-rendering bug found and fixed through two live
      iterations, not assumed correct from desktop-only testing: Jason's
      real iPhone screenshot showed the native `<audio controls>` element
      rendering taller than its container, so half the control visually
      spilled past the card's own background/border onto the plain page
      background beneath. First attempt (`min-height: 54px` plus more
      padding) was insufficient per a second screenshot; fixed properly
      with an explicit `height: 84px` on the audio element and more
      generous container padding, based on the real proportions visible
      in that second screenshot rather than another blind guess.
- [x] Alongside the audio player, applied cosmetic changes Jason asked
      for at the same time: doubled the brand title and nav-button sizing,
      bumped the site-wide base font size a few points via `:root`
      (cascades correctly since the whole stylesheet is `rem`-based).

## Required integration impact checklist

- [x] **HomeLab Doctor** — extended `check_news_aggregator()` with an
      audio-freshness check: `run_digest.sh` swallows a failing stage
      (`|| echo ... continuing`), so a broken Piper or `ffmpeg` would
      leave the systemd service reporting success while the audio
      silently went stale — a real, confirmed gap, not a hypothetical
      one. Checks `latest.mp3`'s mtime against a 14-hour threshold
      (generous margin over the 12h cadence); warns if no audio has ever
      been generated, fails if it's gone stale. Verified both branches
      with synthetic state strings before trusting the live (currently
      fresh, correctly silent) result.
- [x] **Backup and recovery** — real, quantified answer given to Jason
      rather than assumed: LXC 114's whole-guest backup (unchanged since
      Phase 1) does capture `news.db` and the audio file, not just
      config/app code, since it has no path exclusions. Measured real
      numbers: `news.db` steady-state growth ~0.5MB/day (~180MB/year
      unbounded, no pruning exists); the single overwritten audio file
      contributes a bounded ~30-60MB total across all retained backup
      generations combined, since it never accumulates on live disk.
      Confirmed `/mnt/backups` is plain ext4 (no ZFS dedup), so every
      retained generation really is an independent full copy. Jason
      decided to leave the whole-guest backup as-is given the volume is
      negligible either way.
      **Revisited 2026-09-16**: despite the measured footprint being
      negligible, Jason asked to stop retaining old audio in backups at
      all. Added `exclude-path` to the shared all-guests backup job
      (`backup-49999802-1365`) via `pvesh set /cluster/backup/...`,
      anchored to `/opt/news-aggregator/static/digest-audio/latest.mp3`
      specifically — the leading `/` anchors it to each container's own
      root, so it can only ever match inside LXC 114 (no other guest has
      that path), not a collision risk against the other 13 guests this
      same job also backs up. `latest.json` (121 bytes) is deliberately
      not excluded — it's negligible and useful metadata. `news.db`
      remains fully backed up; it is a real system of record, unlike the
      regeneratable audio file.
- [x] **NetBox** — not applicable; no new guest, VM, or interface.
- [x] **Diagrams/rack records** — not applicable; no new guest.
- [x] **Homepage/service discovery** — not applicable; no new tile needed,
      the audio player lives inside the existing `/digest` page.
- [x] **Authentication/authorization** — unchanged from Phase 1/2's
      decision (network ACL only); the audio file is served by the same
      Flask app behind the same access boundary, no separate exposure.
- [x] **DNS, certificates and firewall** — not applicable; no new
      exposure, same host/port.
- [x] **Automation and schedules** — audio generation rides the existing
      digest timer; no new schedule introduced.
- [x] **Security inventory** — no new credentials; Piper and `ffmpeg` are
      local, unauthenticated tools with no external API key.
- [x] **Repository documentation** — this document, plus general cleanup
      of accumulated `.bak-*` development-safety-copy files from
      `/opt/news-aggregator/` (Jason's own dev-session copies, not this
      repo's established Homepage `services.yaml.before-*` convention,
      which was deliberately left untouched as out of scope).

## Graduation criteria

The project graduates when Piper generates real, Jason-approved audio on
the existing digest schedule, the player renders correctly on both
desktop and mobile (confirmed by Jason directly, not assumed), and
HomeLab Doctor has real coverage for a silent Piper/ffmpeg failure.

## Evidence log

| Date | Milestone | Evidence | Result | Operator |
|---|---|---|---|---|
| 2026-09-15 | Authorization | Jason asked for an audio digest, confirming all of Claude's design suggestions (local Piper TTS, one combined narration, deviation notes excluded) and noting the Piper choice doubles as a trial for a planned Home Assistant project | This document created; Milestone 1 begins | claude |
| 2026-09-15 | 1 Piper installed and voice validated | Confirmed real headroom before installing (1.9GB RAM, 14GB disk free). Installed the prebuilt Piper binary release and the `en_US-lessac-medium` voice model. Real synthesis test: valid WAV confirmed via `file`, 0.165 real-time factor. Sent the actual generated audio to Jason rather than assuming the voice choice was acceptable — confirmed ("it will be fine") | **Milestone 1 complete** |
| 2026-09-15 | 2 audio pipeline built | `audio_digest.py` built and chained into the digest timer via a new `run_digest.sh` wrapper. Verified against two real digest runs (6 stories/1.9MB, then 13 stories/4.2MB after the source expansion), both sent to Jason directly for real listening, not just described | **Milestone 2 complete** |
| 2026-09-15 | Voice pace adjusted | Jason asked to slow the voice down after hearing the real sample. Added Piper's `--length_scale` at 1.15 (default 1.0) | Regenerated and reverified live |
| 2026-09-15 | 3 UI integration and real mobile bug found/fixed | Added the audio player to `/digest`. Jason's own real iPhone screenshot showed the native audio control rendering taller than its container and visually spilling past the card background. First fix (`min-height: 54px`) was confirmed insufficient by a second real screenshot; fixed properly with an explicit `height: 84px` sized off the actual proportions visible in that screenshot, since Claude has no way to render or inspect mobile Safari's native audio control directly. Jason confirmed afterward on his own device: "Audio is great!" | **Milestone 3 complete, confirmed working** |
| 2026-09-15 | Digest hero-image cropping fixed, in two passes | Jason's own screenshot showed some hero images (particularly wire-service composite/side-by-side thumbnails) cropped too tightly at `height: 220px` with `object-fit: cover`, cutting off faces. Increased to `340px`, then a second real screenshot showed it was "almost perfect" but still wanted a bit more, so increased again to `400px` | Verified deployed live after each pass |
| 2026-09-15 | Backup scope investigated and reported honestly | Jason asked to confirm recordings/news items aren't being backed up, assuming only config/app was. Checked the real config rather than confirming the assumption: the whole-guest backup has no path exclusions, so it does capture `news.db` and the audio file. Measured real growth numbers (~0.5MB/day DB growth, ~30-60MB total audio footprint across all retained generations) and confirmed `/mnt/backups` has no dedup (plain ext4). Jason decided to leave the backup as-is once he saw the real numbers were negligible | Accurate answer given rather than confirming an incorrect assumption |
| 2026-09-15 | Doctor extended for a real gap | `run_digest.sh` swallows a failing stage, so a broken Piper/ffmpeg would report success while leaving the audio stale with no alert. Added an audio-freshness check to `check_news_aggregator()`; verified both the "never generated" and "stale" branches with synthetic state before trusting the live (correctly silent, audio is fresh) result | Real monitoring gap closed |
| 2026-09-15 | Audio timestamp shown in local time | The "generated" timestamp on the audio player was displaying raw UTC; Jason asked for local time. Converted in `get_audio_meta()` using the same fixed UTC-7 offset already established for the digest timer (BC no longer observes DST), rather than adding a second timezone convention | Verified live: 23:16 UTC correctly renders as 16:16 |
| 2026-09-15 | Cleanup | Removed `.bak-*` development-safety-copy files from `/opt/news-aggregator/` at Jason's request. Investigated the actual disk usage first rather than assuming the `.bak` files were the bulk of it — they weren't (a few hundred KB); the Python `venv/` (41MB) was the real majority, which is normal and not bloat. Corrected that to Jason directly rather than letting the earlier imprecise framing stand | Directory tidied; inaccurate earlier framing corrected |
| 2026-09-15 | Graduation | All three graduation criteria met with real confirmation, not assumption: Jason confirmed the audio itself ("Audio is great!") and the mobile player rendering, both on his own device rather than taken on faith from Claude's own testing; HomeLab Doctor's audio-freshness check is live and verified against both real and synthetic state. Moved this document to `docs/projects/completed projects/` via `git mv`, fixed its now-relative cross-references, and updated the portfolio README | Project closed out |
| 2026-09-16 | Post-graduation refinement | Jason listened to a real full recording and asked for: an intro naming the briefing/date, a pause or bridge between stories, a short outro, and an English male voice. Rebuilt `audio_digest.py` to synthesize intro/each story/outro as separate Piper calls joined by a fixed 1-second silence clip (`ffmpeg anullsrc`, format-matched to Piper's probed `pcm_s16le`/22050 Hz/mono output for lossless `-c copy` concatenation) instead of one continuous Piper call | New logic verified via `py_compile` before running against real data |
| 2026-09-16 | Voice candidates generated and rejected | Downloaded `en_US-ryan-medium` and `en_GB-alan-medium` from the same Hugging Face source as the original voice; generated real samples of both narrating the actual latest 13-story digest with the new intro/pause/outro structure, to a non-production test directory (`--voice-model`/`--out-dir` overrides added to the script for exactly this); sent both to Jason before changing anything live. Jason: "Don't like either voice. Let's just go with the original. Don't change the voice." | Both candidate `.onnx`/`.onnx.json` files and their `/tmp` test-output directories deleted; production voice (`en_US-lessac-medium`) never changed |
| 2026-09-16 | Production redeployed and verified | Backed up the pre-change script to `audio_digest.py.bak-pre-intro-pause-outro` (rollback point, kept — not deleted), promoted the new version to `audio_digest.py`, ran it for real against the live `news.db` (13 stories, digest_run `2026-09-16T12:15:57Z`). Verified live rather than assumed: `latest.json` matches the real digest_run and story count; `curl` against the actual gunicorn bind (`192.168.70.13:8080`, found by reading the real systemd unit rather than guessing a port) confirmed `/digest` returns HTTP 200 and `/static/digest-audio/latest.mp3` serves the new 4,639,976-byte file | Live and confirmed serving correctly; `run_digest.sh`/the existing 05:15/17:15 timer needed no changes since the entry point filename didn't change |
| 2026-09-16 | Backup exclusion revisited | Confirmed on the live host first, not assumed: the audio file already only ever exists as one overwritten `latest.mp3`, no history accumulates on disk. Jason's actual concern was backup-generation bloat, previously investigated and accepted as negligible (~30-60MB total) — he asked to exclude it anyway. Read `man vzdump`'s `--exclude-path` documentation and the live `/cluster/backup` job list via `pvesh` before changing anything, rather than guessing at Proxmox's exclusion mechanism. Added `/opt/news-aggregator/static/digest-audio/latest.mp3` as an anchored `exclude-path` on the shared all-guests job via `pvesh set /cluster/backup/backup-49999802-1365` | Verified with a real manual `vzdump 114` test run (not assumed from the config alone): `tar -tvf` on the resulting archive confirmed `latest.mp3` genuinely absent while `news.db`, `app.py`, and the small `latest.json` were all still present. Test archive deleted afterward via `pvesm free`; the pre-existing 02:44 automatic backup from earlier that same morning still contains the (pre-change) audio file, as expected — tomorrow's 02:30 run is the first to benefit |

## References

- [News Aggregator Phase 2 — Digest, Sections and Source Requests](News-Aggregator-Digest-and-Sections.md)
- [News Aggregator (MuckScraper) — Phase 1](News-Aggregator-MuckScraper.md)
- [Project Creation Standard](../../Project-Creation-Standard.md)
