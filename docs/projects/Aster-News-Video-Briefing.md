# Aster News video briefing

> **Status:** Proposed — Stream M; visual design accepted, renderer evaluation started
>
> **Owner:** Jason
>
> **Proposed:** 2026-11-06
>
> **Authorization stream:** Stream M

## Purpose and desired outcome

Add an optional video edition of the private News Digest in which Aster presents
the existing briefing with a stable fictional identity, contemporary British
broadcast bearing, the canonical Aster voice and a coherent studio. The result
must remain private, recoverable and subordinate to the existing audio/text
briefing rather than becoming its only delivery path.

## Current state and evidence

News Digest already owns briefing text and canonical spoken delivery. Aster's
accepted visual baseline is a fictional Black British male presenter with an
apparent age of 42 in 2026. Ten identity-preserving 2026 wardrobe assets are
pinned by SHA-256, and the exact rectangular-monitor studio is accepted. Local
code calculates annual age, prepares candidate-only age/wardrobe briefs and
selects one wardrobe image per date. The current 1.68-second Mac/Qwen plus
SadTalker synthetic candidate is hash-pinned for evaluation; its facial timing
is accepted and its replacement voice awaits review. No deployed video
renderer, schedule or production integration exists.

## Scope and exclusions

In scope: presenter identity contract, annual one-year ageing candidates,
annual evidence-based wardrobe refresh, daily outfit rotation, studio design,
later lip-sync/video-render evaluation, News Digest integration, private
delivery, monitoring and recovery design.

Excluded unless separately approved: impersonating a real presenter, cloning a
real voice, public publishing, changing briefing editorial logic, replacing the
canonical Aster voice, activating generated identity changes without review,
or creating a local-AI schedule without verified Lab Hours admission.

## Authority model

- News Digest remains authoritative for story selection and briefing text.
- The HomeLab UI style guide and production News Digest implementation own the
  canonical Aster voice contract.
- `presenter_profile.json` owns the accepted appearance and ageing policy.
- `wardrobe.json` owns the accepted wardrobe, research evidence and rotation.
- Project evidence records candidate acceptance; generated assets do not
  become authoritative merely because they exist.

## Architecture and data flows

The proposed flow is News Digest text → shared speech cleanup → canonical
Mac/Qwen Aster speech → bounded presenter/lip-sync renderer → private video
artifact → authenticated News Digest delivery. Daily wardrobe selection is a
pure date-to-asset mapping and makes no AI or network call. Annual ageing and
wardrobe work produces candidates only.

## Privacy and security design

The presenter is fictional. Real-presenter images may inform broad era and
broadcast-language research but must never be used as a face target. Briefing
content should remain on the private/local path. Future renderer credentials,
if any, must remain outside Git and behind a least-privilege service identity.
No public ingress is proposed.

## Pre-start risk assessment

| Risk | Control | Residual risk |
|---|---|---|
| Identity drift or accidental resemblance to a real person | Immutable identity anchor, pinned accepted images, candidate-only annual update and human acceptance | Generative outputs still need visual review |
| Presenter becomes stale or gimmicky | Annual current-broadcaster/tailoring evidence gate; restrained broadcast brief | Fashion judgement remains subjective |
| Video path competes for local AI capacity | No schedule now; future full-window Lab Hours check, reservation, host lease and shared lock are mandatory | Rendering may need a separate capacity decision |
| Video failure disrupts the briefing | Keep text/audio path independently usable; publish video only after complete render | Video may be unavailable while audio remains healthy |
| External generation exposes private briefing content | Use only synthetic visual references during design; evaluate a local renderer before any real-content trial | Some candidate artwork was generated externally |

Recovery is currently deletion/reversion of unaccepted local candidates; no
production state was changed. Abort on identity drift, unverified source rights,
private-content egress, Lab Hours conflict or loss of the existing audio path.

## Persistence plan

Accepted and candidate states are explicit, assets are hash-pinned, and daily
selection is deterministic. Resume by reading this project, the two manifests,
the README and test output. Partial future renders must remain invisible to the
briefing UI until atomically accepted.

## Milestones

### M0 — Presenter identity and ageing contract

- [x] Prepare a fictional modern British presenter baseline and immutable anchor.
- [x] Implement candidate-only annual apparent ageing with manual acceptance.

### M1 — Wardrobe system

- [x] Prepare ten identity-preserving 2026 broadcast outfits.
- [x] Implement deterministic ten-day shuffle with no adjacent repetition.
- [x] Require current UK broadcaster and tailoring research in annual refreshes.
- [x] Pin source assets and pass local regression tests.

### M2 — Studio design

- [x] Reconcile the studio direction to the current AsterTV design authority.
- [x] Produce the first 16:9 studio candidate at television viewing distance.
- [x] Record presenter and story-graphics safe regions and prohibit baked text.
- [x] Obtain owner acceptance of the exact rendered candidate.

### M3 — Renderer evaluation

- [x] Compare bounded local presenter/lip-sync options on synthetic text.
- [ ] Measure identity stability, lip-sync, render time, resource use and failure behavior.
- [ ] Select or reject an implementation without changing production.

### M4 — Private pilot and graduation

- [ ] Design the private integration, recovery checkpoint and operator workflow.
- [ ] Obtain authorization immediately before any remote/production mutation.
- [ ] Validate audio/text independence, monitoring, backup/restore and user acceptance.

## Validation and evaluation

Current tests verify pinned hashes, age/date boundaries, candidate-only output,
all-ten coverage per cycle, stable same-day selection and 365 days without an
adjacent outfit repeat. Later gates must cover malformed manifests, missing
assets, renderer timeout/interruption, stale video, identity similarity,
lip-sync, mobile/TV playback, capacity and two production-shaped passes.

## Observability and maintenance

No service or schedule exists yet, so Doctor, Beszel and alerting are not
applicable at this design stage. A pilot must expose last successful render,
duration, source digest identity, output age and actionable failure state.
Annual work may not be scheduled until its complete execution and recovery
window has a verified Aster Lab Hours reservation for a registered hash-pinned
workload.

## Backup, restore and rollback

Git-tracked manifests/code and hash-pinned source assets are the current
recovery set. Rollback is the last accepted presenter and wardrobe collection.
A future deployed renderer must document configuration backup, artifact
retention, isolated restore and an immediate audio-only fallback.

## Documentation and systems-of-record updates

- HomeLab Doctor/monitoring/Beszel: not applicable until a service is selected.
- Backup, wiki, Aster mirror and operational reference: required before pilot graduation.
- NetBox, diagrams, Homepage, DNS, certificates and firewall: no change at design stage.
- Authentication/AI administration: not yet supported; must be designed before deployment.
- Automation/schedules: deliberately disabled; Lab Hours controls apply before activation.
- Repository: this project, presenter/wardrobe contracts and visual assets are the design record.

## Graduation criteria

Jason accepts the identity, wardrobe and studio; a renderer passes quality,
privacy, capacity and failure tests; the canonical Aster voice remains the
accepted Mac/Qwen 1.7B Aster voice; text/audio remain independently
available; private delivery, monitoring, recovery and operator handover pass;
and all production changes have their required authorization.

## Evidence log

### 2026-11-06 — Identity and wardrobe design

- Accepted Aster's modern 2026 appearance as the visual baseline.
- Generated ten clothing-only variants and two numbered review boards.
- Recorded 2026 broadcaster/tailoring research and a 90-day annual evidence gate.
- Implemented deterministic daily selection and annual candidate briefs.
- Passed 10/10 local tests and Python syntax compilation.
- No service, schedule, credential, network, remote repository or production state changed.

### 2026-11-06 — Studio candidate and annual brand binding

- Rendered a photorealistic 16:9 studio candidate with a left/centre-left
  presenter region and a large right-hand graphics-safe wall.
- Rejected the first blue/cyan app-icon-derived frame after Jason identified it
  as obsolete design language; it is preserved only as negative evidence.
- Reviewed the current reconciled AsterTV r7 skin package and generated v2 from
  its canonical ivory, stone, paper, ink, charcoal, deep green, sage and
  champagne-gold language, plus its limestone and jade surface assets.
- Added a fail-closed annual studio review: resolve the then-current accepted
  AsterTV design release, research current broadcast-set design, create candidates and
  require owner acceptance. It does not schedule or render automatically.
- Revised only the story display from the original curved architectural wall
  into a conventional horizontal rectangular monitor with a thin gold frame.
  The curved-monitor v2 is preserved as superseded evidence; the rectangular
  geometry is an annual-review invariant unless Jason explicitly revisits it.
- Jason accepted the exact v3 rectangular-monitor frame as the studio.

### 2026-11-06 — First local lip-sync and motion candidate

- Compared the local roles of SadTalker, MuseTalk, Wav2Lip and LivePortrait.
  SadTalker was selected for the first single-image, audio-driven test because
  it can generate facial expression and head pose without first making a source
  performance video.
- Rendered the synthetic line “Good evening. This is Aster.” with canonical
  Kokoro `bm_daniel`, `en-gb`, speed `0.95`, then produced a 52-frame,
  2.08-second H.264/AAC candidate from the accepted studio.
- Sampled early, middle and late frames. Aster's identity, wardrobe, hands,
  desk and studio remained visually stable; full-file decode also passed.
- The 256-pixel CPU face pass took 318 seconds (6.12 seconds/frame), with about
  18 additional seconds for final compositing. This is not real-time capacity.
- The result animates lips, eyes and restrained head/upper-body micro-motion.
  Its hands and arms remain static, so independent random gestures are still an
  open renderer requirement rather than a claimed capability.
- The candidate, canonical WAV and complete hash/model/parameter manifest are
  stored under `docs/assets/news-video/pilot/` and `services/news-video/pilot/`.
  No service, schedule, local-AI reservation, remote system or production route
  was created or changed; the attended render ran on the Mac.
- Jason judged the facial lip synchronization perfect but rejected the v1
  voice quality. Audit found that the pilot had used the former Kokoro contract
  even though Aster's accepted authority had moved to Mac/Qwen 1.7B. The mux
  introduced no clipping or material level change.
- Re-rendered the identical text and motion recipe with the accepted Aster
  speech authority. The v2 result is 1.68 seconds and 42 frames; it decodes
  cleanly and retains the visually stable presenter/studio composition. The
  rejected v1 files remain hash-pinned as superseded evidence.
- Jason accepted the v2 voice identity and lip synchronization but reported two
  defects: “Aster” sounded like “aRster”, and the moving head appeared detached
  from the static torso. Added a bounded model-facing whole-word pronunciation
  rule (`Aster` → `Asster`) while preserving written text, and rendered v3 with
  SadTalker's documented full-image `--still` mode to lock the original pose.
- The measured v3 CPU path took 300 seconds for 46 face frames plus about 16
  seconds to composite. Extrapolation gives 42.93 hours for 15 minutes or 57.25
  hours for 20 minutes of video; accepted Qwen speech adds about 12.97–17.30
  minutes. Twice daily would require roughly 86–115 Mac CPU-hours per day, so
  SadTalker is rejected for long-form production capacity.
- Current feasibility direction is reusable full-presenter motion loops plus a
  mouth-only renderer such as MuseTalk 1.5. Its official implementation reports
  30+ fps on an NVIDIA V100 after avatar preparation, but the HomeLab has no
  supported NVIDIA/CUDA path. A bounded M4/MLX or alternative-hardware benchmark
  is required before any twice-daily schedule can be proposed.
- Jason accepted the v3 “Asster” model-facing pronunciation and directed that
  the work be pushed and feasibility continue. The written identity remains
  “Aster”; production deployment of the speech-gateway rule remains a separate
  remote change from this repository push.
- The first community MuseTalk/MLX feasibility probe used 64 frames at batch
  size 8 on the 16 GiB M4 while Adobe Lightroom Classic was also open. Jetsam
  evidence recorded Lightroom as the largest individual process and two Python
  processes at roughly 11–12 GiB each; compressor exhaustion culminated in a
  watchdog panic. The probe produced no accepted result and will not be
  repeated in that form.
- Future renderer probes must fail closed if Lightroom is open, continuously
  monitor system memory and workload RSS, use a small batch-1 resource ladder,
  and stop before swap/compressor pressure. No further inference may run until
  its exact command and artifacts are a registered hash-pinned Lab Hours
  workload with a clear reservation, host lease and shared operation lock.
- After the reboot, the Mac speech authority exposed a pre-existing temporary
  library-path deployment defect. Its exact accepted Qwen and Whisper builds
  were repackaged with separate durable library directories and relative
  runtime paths; authenticated production validation passed. A real OS-reboot
  recovery test remains deliberately deferred.

## Close-out

Not ready. M2 is accepted and M3 renderer evaluation is active. Human viewing
and listening of the first candidate, articulated-motion evaluation and a
production-capacity decision remain open; deployment requires later gates and
the Stream M change boundary.
