# Aster News video briefing

> **Status:** Active — Stream A for the booked B60 renderer session; visual design accepted
>
> **Owner:** Jason
>
> **Proposed:** 2026-11-06
>
> **Authorization stream:** Stream M generally; bounded Stream A authorization
> for booking `aster-news-video-xpu-20261106-1430-r1` through its recovery cutoff

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
- Jason authorized the owner to use the full booked B60 session autonomously
  for the fixed MuseTalk XPU smoke-render purpose. This covers diagnosis,
  hash-pinned implementation/registry/release revisions, explicit retries and
  early release on Proxmox/LXC 110 during the booking and recovery interval.
  It excludes a different workload purpose, runner kind, public exposure,
  destructive data operations, weakened restoration controls or work after the
  protected interval.

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
- [x] Record bounded autonomous authorization for the booked B60 session;
  retain ordinary authorization gates for later production integration.
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
- Staged a fixed MuseTalk/MLX one-frame resource probe against source revision
  `c6eb30ebd1ed4d043983209813370153de9346bf` and the pinned Q4 model snapshot.
  It permits exactly one frame at batch size one, verifies every source/model
  and input hash, refuses the real Lightroom editor and browser processes,
  holds Mac-local whole-host and shared-operation locks, and continuously
  aborts on swap, less than 20% free memory, more than 6 GiB process-tree RSS
  or a five-minute deadline. The suite passes 25 tests.
- Jason clarified that the authoritative Lab Hours ledger governs B60 work,
  not this Mac/MLX workload. No B60 registration or reservation was changed.
  The global Codex instruction was corrected with explicit owner approval so
  independent Mac workloads use their reviewed Mac host controls while any
  workflow that calls or competes with B60 remains governed by Lab Hours.
- Built an isolated Python 3.11 renderer environment after the first worker
  attempt proved macOS's Python 3.9 lacked OpenCV and MLX. All renderer imports
  then passed with MLX 0.32.4, OpenCV 5.0.0 and NumPy 2.4.6; the generated build
  directory was moved outside the pinned clean source checkout.
- The first real one-frame model load began from 61% free memory and zero swap.
  Tracked process RSS peaked at about 1.93 GiB, but system free memory fell to
  29% at 23.1 seconds and then 23% with 392.44 MiB of swap at 23.7 seconds.
  The supervisor terminated the process immediately on swap as designed. The
  Mac did not crash, no generated frame was produced, and Qwen/Whisper were
  restored healthy. The result proves Metal allocation is not captured fully
  by process-tree RSS and must remain governed by system memory/swap gates.
- A baseline-relative retry also aborted safely after swap grew from 392.44 to
  550.12 MiB. A structurally different staged loader then encoded/loaded
  Whisper before the VAE and quantized UNet; even this fell from 64% to 17%
  free memory in 3.82 seconds and grew swap from 585.19 to 715.62 MiB. No frame
  was generated and the Mac did not crash. Qwen and Whisper again restored
  healthy.
- MuseTalk 1.5 Q4/MLX is therefore rejected on this 16 GiB M4. The manifest is
  fail-closed as `rejected-on-16gib-m4`, the three-attempt capacity result is
  retained in `musetalk_probe_result_20261106.json`, and another attempt may
  not be made by weakening the memory or swap guards. Renderer evaluation must
  move to a materially lighter implementation or a host with more unified
  memory.
- Live B60 discovery found that its physical BAR has since reached the full
  32 GiB aperture, removing the earlier Level Zero enumeration blocker. Staged
  an isolated 30 GiB LXC 110 volume containing Python 3.12.12, PyTorch
  2.14.1 XPU, Intel compute runtime 26.31, MuseTalk PR 429 commit
  `3bd654938926af520ee30dfe945e4845ef476d94`, exact official model revisions
  and the pinned synthetic studio/audio inputs. No accepted Qwen files or unit
  configuration were changed.
- Registered the hash-pinned workload
  `aster-news-video-musetalk-xpu-smoke-v1` with the existing full-drain,
  whole-host lease, shared-lock and recovery-guardian path. The authoritative
  ledger accepted booking `aster-news-video-xpu-20261106-1430-r1` for
  14:30–16:00 Pacific, with recovery protected through 16:15. The dispatcher,
  workload pins, accepted Qwen service and empty output target passed preflight;
  GPU inference has not yet run.
- An independent sub-agent audited the live reservation-to-dispatch path and
  found that the isolated Intel compiler directory was missing from the
  transient unit's library path; the booking would have drained production but
  failed before rendering. Corrected and re-pinned the adapter to include
  `runtime/root/usr/local/lib`, then verified `libigc.so.2` and
  `libze_intel_gpu.so.1` load under the exact planned environment.
- The same audit identified three overstated controls. The transient renderer
  now runs in a private loopback-only network namespace with a continuously
  enforced 12 GiB memory ceiling and zero swap, and the post-run `xe`
  fault/reset/error scan is case-insensitive. An inert transient-unit test
  proved all three systemd controls, the registry and release-manifest pins
  revalidated, and the 14:30 booking remains scheduled.
- Activated Lab Hours Session Contract V2 for the booking. The 90-minute grant
  permits independently evidenced 20-minute attempts while enough booked time
  remains; it is not artificially limited to three tries. A
  later attempt is admitted only after a failed attempt proves production
  restored and enough booked time remains; an unrestored failure is terminal.
  The booking stays claimed between attempts and can be surrendered early only
  while idle and restored. Future bookings can opt into safe earlier promotion
  without losing their original duration or crossing a recovery boundary.
- V2 also requires a fresh independent read-only evaluation of the final live
  registration and exact reservation before the first attempt. The evaluator
  may not claim the booking, initialize XPU, or mutate B60; a deterministic
  blocker or `WILL NOT RUN` verdict prevents execution until correction and
  re-evaluation.
- The first V2 evaluation found two deterministic session-contract defects:
  the inner transaction/runtime still used the former 3,600-second deadline,
  and a rejected concurrent retry could finalize the booking while another
  retry remained active. Corrected every MuseTalk layer to the registered
  1,200-second deadline, gave retries a deterministic per-attempt unit, and
  made rejected duplicate admission state-neutral. The isolated live-controller
  regression now proves the losing retry cannot shorten the active booking;
  transaction and registry deadlines both report 1,200 seconds.
- The required independent re-evaluation returned `LIKELY RUN`. It confirmed
  both blockers are closed in the live release-pinned code, the booking remains
  scheduled for 14:30–16:00 with a 900-second recovery reserve, and dispatcher,
  lease, locks, attempt evidence, registry and release hashes are clean. The
  only remaining uncertainty is first-use B60 XPU enumeration/model execution,
  which was intentionally not initialized outside the booking.
- Jason clarified that this reservation is the authorization envelope for all
  bounded work needed to fulfil its fixed purpose. The owner may diagnose,
  repin, retry and surrender the lab without repeated approval while the
  booking remains active and restoration is proven. Updated the V2 contract
  and Codex skill from a three-attempt/per-retry-approval model to a
  remaining-time-and-restoration model.
- Attempt 1 crashed in PyTorch's Battlemage device-property path. The fixed
  guest removed `torch.xpu.get_device_name()`, verifies the B60 directly as
  PCI `8086:e211`, enables Python fault handling, and emits flushed stage
  markers. The adapter now converts a native crash into a bounded last-stage
  code instead of losing it as `UNCLASSIFIED`.
- The first failed attempt also exposed a restoration replay bug: recovery
  considered commands observed for an older lease and skipped the current
  unmask operations. Although the ledger said restored, LXC 110's accepted
  Qwen service remained runtime-masked and inactive. Replayed the exact fixed
  recovery inventory, verified Qwen, Aster Agent, Speech and both News timers
  active, and changed restore replay to consider only events bearing the
  current lease ID. Release pin `full_inference_lab_session.py` is now
  `210fa6811d488a0158347c7e40493833489836c73666f2146567145d2a2c3021`.
- Independent re-audit found and closed a final-minute admission gap: the
  retry ledger now includes the runner's 60-second setup lead in both admission
  and `retry_available`. Installed reservations pin is
  `7004bb8df68f4a9d6e30982d7163f21dc09453bff0b18b783e5e6938d8fb5dee`.
- Attempt 2 passed fixed PCI identity and crashed at
  `MOVE_MODELS_TO_XPU`, proving the failure occurs on the first real PyTorch
  XPU transfer. This matches upstream Battlemage reports in
  [PyTorch #179891](https://github.com/pytorch/pytorch/issues/179891) and
  [Intel LLVM #22834](https://github.com/intel/llvm/issues/22834): enumeration
  may succeed while Level Zero kernel execution segfaults. The reported
  OpenCL backend workaround requires an unsupported `LD_PRELOAD` shim and was
  not introduced into this fixed workload.
- Attempt 2 restored production successfully. With no supported correction for
  the registered PyTorch/Level Zero path, released the booking early as
  `EARLY_RELEASE_FAILED_RESTORED` after two evidenced attempts. Qwen, Aster
  Agent, Speech and News timers were active and drain/shared locks absent.
  The PyTorch XPU MuseTalk route is rejected on this current B60 stack; a later
  evaluation should use a separately registered supported runtime such as an
  OpenVINO/ONNX path rather than retrying the same Level Zero stack.
- Converted the fixed MuseTalk 1.5 positional encoder and UNet to a fixed-batch
  OpenVINO 2026.3.1 IR. The alternative keeps Whisper, VAE and latent/decode
  work on CPU and assigns only the converted UNet to OpenVINO `GPU`; the
  transient unit remains private-networked, capped at 12 GiB and zero swap.
  Exact OpenVINO Python, core, GPU-plugin, IR XML and IR BIN hashes are checked
  before GPU compilation.
- Booking `aster-news-video-ov-20261106-1525-r1` ran two short, safely restored
  attempts. The first exposed an overly terse runtime-error envelope; the
  second identified the concrete dependency failure: OpenVINO's GPU plugin
  could not resolve `libOpenCL.so.1`. The diagnostic envelope now preserves a
  bounded sanitized exception message.
- The V2 time gate correctly refused a third launch once the complete 60-second
  setup plus 900-second deadline no longer fit. The session was surrendered
  early as `EARLY_RELEASE_FAILED_RESTORED`, and replacement booking
  `aster-news-video-ov-20261106-1725-r2` was reserved for 17:25–17:50 with
  recovery protected through 18:05.
- Pinned the isolated OpenCL loader, Intel OpenCL ICD, GMM library, Level Zero
  loader and Intel Level Zero driver. The adapter now supplies the isolated
  runtime library paths and a direct `OCL_ICD_FILENAMES` reference to the
  pinned Intel driver. Exact-environment `ldd` checks resolve the OpenVINO GPU
  plugin, Intel OpenCL driver and Intel Level Zero driver without missing
  dependencies. The fresh independent read-only evaluation returned
  `LIKELY RUN`: every deterministic control and dependency is closed, with
  first-use OpenVINO GPU discovery/compile/inference as the only remaining
  experimental uncertainty.

## Close-out

Not ready. M2 is accepted and M3 renderer evaluation remains active, but the
current PyTorch XPU MuseTalk route is rejected on B60. A supported alternative
runtime, human viewing/listening of its first candidate, articulated-motion
evaluation and a production-capacity decision remain open; deployment requires
later gates outside the completed autonomous booking envelope.
