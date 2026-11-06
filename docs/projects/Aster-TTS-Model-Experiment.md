# Aster TTS model experiment

> **Status:** Active — Stream A; design and isolated staging approved, B60
> execution held at the revised GPU-risk gate
>
> **Owner:** Jason
>
> **Proposed:** 2026-11-04
>
> **Started:** 2026-11-04
>
> **Completed:** not applicable
>
> **Authorization:** Jason approved the bounded Stream A experiment on
> 2026-11-04. The approved envelope covers isolated, hash-pinned candidate
> staging, a registered Lab Hours workload, one reserved execution/recovery
> window, blind listening artifacts and restoration of the accepted inference
> service. It does not authorize production voice promotion, consumer routing
> changes, use of the Arc A380, driver changes, public exposure, persistent
> candidate services or remote Git writes. A same-day B60 Vulkan fault record
> discovered after approval adds a new material execution risk; B60 effects are
> held pending an explicit revised risk decision.

## Purpose and desired outcome

Determine whether a stronger local TTS model eliminates Aster's intermittent
mispronunciation of ordinary words while retaining natural cadence and useful
render speed. Produce short, blinded, directly comparable listening artifacts
and measurements for the current Kokoro voice and two Qwen3-TTS candidates.
Do not change the production voice until Jason listens and explicitly chooses a
candidate.

The experiment tests the reported defect rather than treating GPU use as the
goal. GPU acceleration is useful only if the candidate is correct, stable and
fast enough to operate locally.

## Current state and evidence

- Production speech is LXC 128 `aster-voice-prod` at `192.168.20.37`. Kokoro
  ONNX `kokoro-v1.0.fp16.onnx`, `bm_daniel`, British English and speed `0.95`
  run through ONNX Runtime CPU. The guest has no GPU mapping.
- News in LXC 114 uses the production batch TTS endpoint. Its current roughly
  690-second digest required about 473 seconds to synthesize, an approximately
  0.68 render factor. This is already fast enough for the digest workflow.
- The reported defect is a bizarre ordinary-word pronunciation every few
  sentences, not generally poor cadence. The current renderer independently
  phonemizes and renders short semantic units, which resets linguistic context.
- STT remains Whisper. Piper is a manually selected legacy rollback path, not
  an automatic or proposed replacement.
- LXC 110 owns the accepted B60-backed Qwen3.5 text-inference service. It is the
  only approved candidate GPU host for this experiment; the Arc A380 remains
  excluded because it carries production media and speech work.
- On 2026-11-04, current Kokopop Vulkan testing on the B60 produced implausibly
  stretched speech, four CCS compute-engine resets and about 1,900 `xe`
  `Fault response: Unsuccessful -EINVAL` messages. Aster remained HTTP-healthy,
  proving that endpoint health alone cannot detect GPU collateral effects.
- Primary upstream candidates are Qwen3-TTS through `qwentts.cpp`, which
  supports the 0.6B and 1.7B model families and advertises CPU and Vulkan
  backends. Chatterbox Nano CPU is retained only as a fallback candidate if
  Qwen cannot be made safe or reproducible.

## Scope and exclusions

### In scope

- Build an immutable six-passage pronunciation corpus from public/synthetic
  text, including common homographs, names, abbreviations, currencies, numbers
  and longer news-style sentences.
- Capture the current Kokoro control, normalized text and phoneme evidence.
- Stage exact, hash-recorded source and model artifacts in an isolated candidate
  path with no persistent listener or production consumer.
- Compare Qwen3-TTS 0.6B Base with a synthetic Kokoro-derived reference and
  Qwen3-TTS 1.7B with both the same reference and a fixed warm British male
  newsreader design prompt, subject to the execution gates below.
- Produce blind A/B/C audio, machine-readable timing/resource evidence and a
  listening score sheet.
- If GPU execution is explicitly accepted after the revised risk review,
  register a hash-pinned Lab Hours workload, reserve the full execution plus
  recovery interval, acquire the whole-host lease and shared operation lock,
  quiesce accepted inference, run once, then restore and verify it.

### Excluded

- No production Kokoro, Whisper, endpoint, route, credential or consumer
  changes.
- No model promotion, automatic fallback change or new scheduled job.
- No Arc A380 work and no concurrent GPU experiment.
- No kernel, firmware, driver, compute-runtime or package-manager changes.
- No real-person voice sample or biometric voiceprint; use only a synthetic
  Aster-generated reference.
- No private news content in distributable fixtures. The real public digest may
  be tested privately, with only sanitized aggregate results retained.
- No public ingress, DNS, firewall, NetBox or authentication changes.
- No remote Git write without Jason's separate immediate confirmation.

## Authority model

| Fact | Authority |
|---|---|
| Live service, GPU and kernel state | Proxmox/LXC runtime |
| Lab Hours availability and booking | authoritative Proxmox Lab Hours ledger |
| Accepted production model and configuration | deployed units plus accepted local-AI platform records |
| Candidate identity | exact source revision, artifact hashes and experiment manifest |
| Pronunciation and preference | Jason's blinded listening assessment |
| Timing, load and faults | immutable experiment result plus host/guest telemetry |
| Inventory | NetBox, reconciled only if deployment later changes inventory |

## Architecture and data flows

Production remains unchanged:

`News/Aster consumer -> LXC 128 Kokoro ONNX CPU -> audio`

The isolated experiment writes only private artifacts:

`fixed corpus -> control/candidate renderer -> hashed WAV + result JSON -> blind package`

Any B60 phase must run through the existing fail-closed local-AI operating
model: authoritative reservation, whole-host lease, shared operation lock,
accepted-service checkpoint, bounded candidate process, host-kernel monitoring,
candidate termination, accepted-service restoration and health/kernel audit.
Partial output never becomes visible to production consumers.

## Privacy and security design

No credentials are required by the corpus or renderers. Candidate downloads are
pinned and hash-recorded before use. The corpus is public or synthetic; any
private current-digest comparison remains on the private lab and is excluded
from Git. Candidate services bind only to loopback, run transiently and are
removed from memory at the end of the window. Logs contain model/configuration
identity and aggregate resource data, not secret-bearing environment files.

## Pre-start risk assessment

| Risk | Likelihood / impact | Control | Residual risk |
|---|---|---|---|
| B60 Vulkan faults or resets disturb accepted inference | Material evidence / high | No GPU effects until revised approval; exclusive lease; pre/post kernel counters; immediate abort on any new `xe` fault/reset; recovery deadline and accepted-service restore | A GPU reset can affect the accepted process before the monitor reacts |
| Candidate hallucinates, omits or repeats speech | Medium / medium | Fixed transcript, blind listening, transcript-error scoring and no promotion | Human listening is required; automated checks cannot prove pronunciation |
| Synthetic reference produces an identity mismatch | Medium / low | Same reference for candidates; score identity separately; retain production unchanged | Qwen may not reproduce the current timbre exactly |
| Candidate artifacts consume storage or RAM | Low / medium | Bounded models/corpus, preflight headroom, isolated path and explicit retention decision | Model files remain sizable until removed |
| Lab work overlaps another local-AI owner | Low / high | Registered hash-pinned workload; authoritative full-window check and booking; immediate recheck; whole-host lease and shared lock | Ledger/lease unavailability fails closed and delays the test |
| Production is not restored by the deadline | Low / high | Capture exact accepted command/unit/hash and health before effects; guardian-enforced deadline; restore before analysis | Manual operator recovery may be required if the GPU or unit fails |
| Private or biometric material is retained | Low / medium | Public/synthetic corpus and synthetic voice reference only | A synthetic reference still represents Aster's designed identity but not a person |

There are no intended destructive operations. No backup, database or production
configuration is changed. The key abort conditions are a failed checkpoint,
missing booking/lease/lock, unexpected live topology, insufficient recovery
time, any new GPU fault/reset, candidate escape from loopback, accepted health
failure or an artifact/hash mismatch.

Jason accepted the original Stream A envelope on 2026-11-04. The newly
confirmed B60 reset evidence was not stated in that envelope, so GPU execution
requires a separate explicit risk decision. Documentation, corpus construction,
control rendering and CPU-only candidate evaluation may proceed meanwhile.

## Persistence plan

The experiment manifest records schema version, corpus hash, renderer/source
revision, model and reference hashes, exact arguments, start/end time, exit
status, timing, output hashes and resource/fault observations. Staging is
idempotent and candidate output is written under a run ID before an atomic
`complete` marker. Resume by reading this document, checking the tree and live
state, then continuing at the first incomplete milestone. Never infer success
from a missing process.

## Milestones

### M0 — Record design and live constraints

- [x] Confirm the user-visible defect and current production architecture.
- [x] Research primary local candidates and acceleration support.
- [x] Obtain Stream A approval for the bounded experiment envelope.
- [x] Record the newly discovered B60 Vulkan reset evidence as a revised gate.
- [x] Commit the focused project record without unrelated user changes.

**Gate:** scope, exclusions, recovery and the new material risk are durable.

### M1 — Build corpus, harness and CPU control

- [x] Create six fixed public/synthetic passages and expected transcript.
- [x] Add deterministic manifests, result schema and blind package builder.
- [x] Capture at least two current Kokoro control renders and phoneme traces.
- [x] Unit-test missing/corrupt model, timeout, partial output and repeat runs.

**Gate:** the control reproduces the relevant workflow without touching a
production consumer.

### M2 — Stage and screen candidates without GPU effects

- [x] Pin exact `qwentts.cpp` source and initial 0.6B Q8 model artifacts and
  verify hashes.
- [x] Build the CPU screen in an isolated path without system package or driver
  changes.
- [ ] Run short CPU smoke tests for Qwen3-TTS 0.6B and 1.7B where feasible.
- [ ] Reject candidates that omit/repeat/hallucinate, cannot render the corpus,
  or are clearly too slow before any GPU risk is accepted.

**Gate:** at least one candidate is qualitatively credible and reproducible.

### M3 — Revised B60 risk decision and protected run

- [ ] Present the CPU evidence, exact candidate, kernel abort logic, duration
  and revised residual risk to Jason; obtain explicit acceptance or skip GPU.
- [ ] Register the exact hash-pinned experiment workload.
- [ ] Select an exact execution plus recovery window and obtain a clear
  authoritative ledger result before reservation.
- [ ] Reserve the workload; immediately before effects recheck the ledger,
  reservation, whole-host lease and shared operation lock.
- [ ] Capture accepted-service and kernel baselines, run the bounded candidate,
  abort on the first new GPU fault/reset, restore accepted inference and prove
  endpoint plus kernel health before releasing the window.

**Gate:** restoration passes and no unaccounted GPU/kernel collateral effect
exists. A reset or fault rejects the GPU path even if audio was produced.

### M4 — Blind listening and decision

- [ ] Randomize labels and present equal-loudness A/B/C samples.
- [ ] Score pronunciation errors per 1,000 words, omissions/repetitions,
  naturalness, identity preference and repeat determinism.
- [ ] Compare time to first audio, render factor, RAM/VRAM and GPU load.
- [ ] Record Jason's selection or retain current Kokoro.

**Gate:** a preferred configuration is identified by listening evidence; this
does not itself authorize production promotion.

### M5 — Close experiment

- [ ] Stop/disable every candidate and reconcile accepted production health.
- [ ] Decide which private model/audio artifacts to retain and document their
  storage/recovery status.
- [ ] Complete intent/efficiency and integration-impact reviews.
- [ ] Record any separately scoped promotion proposal.

## Validation and evaluation

The six passages cover: current public news style; record/read/lead/live/close/
minute/present/content/produce homographs in disambiguating sentences; names
and place names; currencies, dates and grouped numbers; dotted abbreviations;
and long sentences with clauses. Each configuration renders twice. Evaluation
records pronunciation failures per 1,000 words, textual omissions/additions or
repetitions, blind preference, time to first audio, total render factor,
resident memory, VRAM where applicable and new kernel faults/resets.

The experiment succeeds if it produces a fair blind comparison and a safe,
repeatable conclusion. A new model need not win. Promotion requires a separate
change plan with production regression, fallback and listening acceptance.

## Observability and maintenance

This is a transient experiment, not a service. No recurring automation or
alert is added. Existing Aster endpoint monitoring remains active. A B60 phase
adds temporary high-sensitivity host-kernel observation because normal endpoint
health failed to expose prior resets. Beszel requires no inventory change; its
resource history may corroborate but does not own pass/fail.

## Backup, restore and rollback

Rollback is process-level: terminate and collect the isolated candidate,
restore the exact accepted `aster-llama.service`, validate its model/build,
health, PID/restart count and a bounded inference, then inspect the host kernel
for collateral faults. Production speech never moves, so Kokoro and Whisper do
not require rollback. Candidate artifacts contain no unique user data and may
be recreated from their pinned manifest.

## Integration impact checklist

- [ ] **HomeLab Doctor:** no change unless a later promotion occurs; run the
  existing relevant health checks after restoration.
- [ ] **Monitoring/alerting and Beszel:** no inventory change; use existing
  monitoring plus temporary kernel observation.
- [ ] **Backup and recovery:** candidate artifacts are reproducible and not
  production state; record retention choice at close-out.
- [ ] **NetBox:** not applicable; no device, guest, address or service change.
- [ ] **Human wiki:** not applicable unless a candidate is later promoted.
- [ ] **Aster mirror/snapshot:** record only the accepted conclusion if useful;
  never treat experimental evidence as deployed fact.
- [ ] **Operational reference/runbooks:** update only if the operating model or
  accepted backend changes; neither is authorized here.
- [ ] **Repository documentation:** this project and portfolio are authoritative
  for experiment status.
- [ ] **Diagrams/rack records:** not applicable; topology is unchanged.
- [ ] **Homepage/service discovery:** not applicable; no service is exposed.
- [ ] **Authentication/authorization:** not applicable; no API identity added.
- [ ] **DNS/certificates/firewall:** not applicable; loopback-only transient run.
- [ ] **Automation/schedules:** no recurring schedule; one Lab Hours booking is
  execution admission, not an automation.
- [ ] **Security inventory:** hashes, modes and temporary artifact cleanup are
  checked; no credentials are used.
- [ ] **AI administration integration:** not applicable to a transient
  candidate; human operation uses the existing Proxmox control path.

## Graduation criteria

- Fixed corpus, manifests and blind samples are reproducible.
- Current Kokoro and at least one credible candidate are compared twice.
- No transcript error, resource measurement or GPU/kernel event is hidden by a
  healthy HTTP endpoint.
- Accepted production services are restored and independently validated.
- Jason records a listening decision, including retaining Kokoro if no candidate
  is clearly better.
- Any promotion remains a separate explicit decision.

## Evidence log

| Date | Evidence | Result |
|---|---|---|
| 2026-11-04 | Read-only live discovery found production Kokoro ONNX on LXC 128 using CPU, with News LXC 114 consuming its batch endpoint. Current digest render factor was approximately 0.68. | The complaint is not explained by insufficient speed; pronunciation/context is the primary experiment target. |
| 2026-11-04 | Primary-source review identified Qwen3-TTS 0.6B/1.7B through `qwentts.cpp` as the best local candidate family, with Chatterbox Nano CPU as fallback. | Three-way control/candidate design selected. |
| 2026-11-04 | Jason approved the proposed bounded Stream A experiment. | Documentation and isolated staging may proceed within the recorded envelope. |
| 2026-11-04 | Existing EPUB narration evidence showed four B60 CCS resets and about 1,900 `xe` faults during a current Vulkan TTS comparison while Aster's endpoint remained healthy. | GPU execution paused at a new explicit risk gate; CPU screening and stronger kernel abort instrumentation are required first. |
| 2026-11-04 | Created a six-passage public/synthetic corpus, exact-production normalization/unit plan, synthetic Kokoro reference, hash-checked render evidence and blind-package tooling. Nine focused tests cover corpus privacy/shape, malformed WAVs, missing/corrupt pins, failed/partial render cleanup, timeout cleanup and replay refusal. | M1 passed locally. No listener, route, timer, credential or production configuration was added. |
| 2026-11-04 | Rendered two production-shaped Kokoro controls in LXC 128. The twelve clips totalled 322.238 audio seconds and 189.226 render seconds, aggregate RTF 0.5872 and median 155.02 WPM. The production service PID remained unchanged. Identical normalized text and phonemes produced a different WAV hash on all six repeated passages; duration differences were zero to 53 ms. | CPU speed is already adequate. Post-phonemization inference is not bit-deterministic, which is consistent with a random-output symptom but requires listening/ASR to determine whether the differences include pronunciation changes. |
| 2026-11-04 | Pinned `qwentts.cpp` `5916bf7…`, GGML `cc5df49…`, Hugging Face revision `b7ee2e8…`, the 0.6B Base Q8 talker `d54dbaf1…` and Q8 tokenizer `1883beee…`. Built a CPU-only candidate `aea3907b…` in LXC 110 without package, driver, service or route changes; its ABI probe passed. Current source contains an unadvertised SYCL build path in addition to the documented CPU/Vulkan paths. | Initial candidate staging is reproducible. SYCL may avoid the known Vulkan fault path but remains experimental and is not authorized for execution yet. |
| 2026-11-04 | A low-priority CPU-only homograph smoke began without requesting exclusivity. During it, the accepted service was gracefully stopped at 18:31 and restored at 18:32 by claimed Lab Hours booking `aster-stream-a-sa3-candidate-i-20261104-1830-r2` (18:30–19:30 local). The candidate was terminated immediately; it produced no WAV or surviving partial file. Memory retained 12 GiB available, the restored endpoint returned `{"status":"ok"}`, and the host kernel showed no new GPU/OOM event. | The restart was reservation-driven, not resource pressure, but the smoke would have competed with a protected owner. All local-AI execution is held until an authoritative clear-window check. The CPU quality gate remains incomplete. |
| 2026-11-05 | Registered hash-pinned Lab Hours workload `aster-tts-dual-cpu-screen-v1` for the 0.6B and 1.7B Qwen3-TTS Base Q8 CPU candidates. The fixed runner uses the same homograph passage, Kokoro synthetic reference and seed for both, permits no network/GPU/route change, retains private WAV evidence, and restores accepted production through the full-drain controller. Installed workload, adapter and guest pins passed manifest, custody and inactive-target validation. | Initial readiness claim, subsequently disproven: its 4,500-second execution deadline fit the ledger's 90-minute bound but exceeded the separate 2,700-second full-drain bound. |
| 2026-11-05 | The authoritative ledger reported the complete 08:30–10:00 Pacific window clear, then accepted booking `aster-tts-dual-cpu-20261105-0830` for owner `aster-tts-experiment` and the registered dual-CPU workload. The minute dispatcher and Lab Hours doctor were enabled and active. | Historical booking record only; the workload was invalid for the full-drain controller and did not execute either test. GPU/SYCL remained outside the booking. |
| 2026-11-05 | Booking `aster-tts-dual-cpu-20261105-0830` was claimed at 08:30 and failed closed at 08:31 before either candidate started. The transaction requested 4,500 seconds but the full-drain controller has a separate 2,700-second maximum. Its pre-plan cleanup also masked the primary error with `workload plan was not captured`. No WAV or partial output was created; production restoration, Doctor, Kokoro and Aster health all passed. | The earlier readiness claim was incorrect. The combined workload is removed from registration and must not be retried. |
| 2026-11-05 | Two independent Codex reviews re-read the ledger, dispatcher, full-drain and project requirements. The corrected design uses separately registered 0.6B and 1.7B workloads, each with one exact candidate, a 2,100-second render timeout, 2,400-second transaction deadline, 3,600-second booking and 900-second recovery reserve. The dispatcher lead plus execution and recovery leave approximately 240 seconds of booking margin. Exact binary, codec, reference, model and input hashes are enforced; pre-plan cleanup no longer runs; wrong profile, GPU use, pin drift, bad lease and Boolean-generation cases are tested. | Split design accepted for readiness validation. The two one-hour bookings require at least a 15-minute gap and may be created only after live source/plan proof and exact ledger checks pass. |
| 2026-11-05 | The first available interval was initially blocked by B60 reservation `b60-exclusive-20261105-day-r1`, whose owner and guardian failed during restoration. The authoritative session retained `production_restored=false`, the shared operation lock and inactive News timers. The owning “Aster Adaptive Computing — Stream A” agent was contacted and completed the registered assisted recovery. The ledger now records `FAILED_RESTORED`; exclusive/shared/drain locks are absent and accepted Aster, LLM, Speech and News services/timers are active. | TTS did not bypass or mutate another owner's lock. Cross-agent recovery and independent hand-back verification restored an admissible baseline. |
| 2026-11-05 | Post-install readiness passed 71 platform tests, five focused TTS tests, release-manifest load, both inactive-target validations, exact root custody and guest/model/binary/tokenizer/plan/reference hashes. A live no-effect `LocalProxmoxFullDrainSourceProducer.collect(..., lab_seconds=2400)` plus `plan(..., lab_seconds=2400)` verified current-cycle backup, accepted hashes, consumers, rollback/GPU baseline and 900-second recovery. Static dispatcher construction proved 60-second lead + 2,400-second execution + 900-second recovery leaves 240 seconds inside each one-hour booking. | Both exact single-candidate workloads are ready. No inference was run outside Lab Hours. |
| 2026-11-05 | After authoritative exact-window checks, booked `aster-tts-qwen-0p6b-20261105-1330` for 13:30–14:30 and `aster-tts-qwen-1p7b-20261105-1600` for 16:00–17:00 Pacific. Both records name owner `aster-tts-experiment`, their exact registered workloads and state `scheduled`. The later slot avoids B60 retry `b60-exclusive-20261105-day-r2` at 15:00–15:45 plus both 15-minute buffers. | Both tests have separate valid reservations with complete execution and recovery time. Dispatcher/runtime will recheck ledger, lease, locks, backup, accepted hashes and consumers immediately before effects and fail closed on drift. |
| 2026-11-05 | Jason explicitly requested an attended Mac-only acceleration comparison while the separately booked Proxmox tests remained unchanged. On the M4 Mac mini, the same pinned `qwentts.cpp` `5916bf7…`, GGML `cc5df49…`, Q8 talkers/tokenizer, synthetic reference, homograph input and seed were compiled for native Metal and run without a listener or production route change. The 0.6B render produced 20.72 seconds of audio in 14.894 seconds (wall RTF 0.719, engine RTF 0.689, TTFA 474 ms, maximum resident set about 3.84 GB); the 1.7B render produced 22.48 seconds in 19.353 seconds (wall RTF 0.861, engine RTF 0.825, TTFA 560 ms, maximum resident set about 5.57 GB). Both runs reported zero swaps and their WAVs contained no clipped samples. | Both Qwen candidates are faster than real time on the 10-GPU-core M4. The 0.6B Metal result is about 8.5 times faster than its completed CPU screen by RTF. Pronunciation preference still requires listening; the scheduled 1.7B CPU run remains useful as the same-runtime CPU baseline. |
| 2026-11-05 | Pulled the exact currently published morning News briefing and its 15 narration stories without changing production, verified the source MP3 and extracted-script hashes, then rendered the 17 intro/story/outro segments with the same pinned Qwen 1.7B Metal candidate and synthetic reference. The resumable attended run produced 741.6 seconds of audio in 641.804 seconds (aggregate RTF 0.865), with 16 one-second story gaps, peak -4.758 dBFS and zero clipped samples. The source Kokoro MP3 is 787.704 seconds; both private comparison files and a hash manifest remain under the Mac experiment directory. | Full production-shaped batch narration is faster than real time on the M4 and 46.1 seconds shorter than the current Kokoro briefing. This proves capacity and pacing, but listening remains the decision gate for pronunciation and voice preference. |
| 2026-11-05 | Booking `aster-tts-qwen-1p7b-20261105-1600` was claimed at 16:00 and finished `COMPLETE` at 16:06 Pacific. The pinned 1.7B Base Q8 CPU candidate produced 20.88 seconds of audio in 149.080 seconds (RTF 7.140, 212.64 WPM); its WAV hash is `eee2d90d…`. The result records no GPU or network use and no route change. The ledger closed the reservation, runtime locks are absent, and accepted Aster, voice and inference services are active with inference health returning OK. | The final CPU baseline passed safely but is unsuitable for interactive production. The same 1.7B candidate on the M4 Metal path is approximately 8.3 times faster by RTF and remains the practical deployment candidate, subject to Jason's listening decision and a separate promotion plan. |

## Close-out

Open. The fixed corpus, Kokoro control, both exact Qwen CPU screens and both
attended Mac Metal screens are complete. The invalid combined workload is
retired, both valid bookings closed with production restored, and the Mac
comparison did not touch the central stack. Listening and the deployment-risk
decision remain; no production promotion has occurred. No B60 or A380
GPU/SYCL effect may occur until M3's revised risk decision.
