# Aster Unified Voice Service

> Status: Active — Stream A; M0 complete, M1 in progress
>
> Owner: Jason
>
> Proposed and started: 2026-10-10
>
> Authorization stream: **Stream A — Autonomous**, explicitly granted by
> Jason on 2026-10-10 when he directed creation, commit, publication and start
> of this project. The authority covers the exact systems, changes, risks,
> exclusions and gates below. Repository/platform controls, non-waivable stop
> conditions and later remote-write rules remain in force.

## Purpose and desired outcome

Make Aster sound like one assistant everywhere. Home Assistant, Aster
Companion on phone/Mac/web, the News Digest, notifications and any present or
future reasoning backend must send text to one private network-level Aster
Voice Service. That service alone owns speech normalization, pronunciation,
segmentation, synthesis and audio delivery.

The canonical identity is the already approved local Aster voice: Kokoro ONNX
`kokoro-v1.0.fp16.onnx`, British-English `bm_daniel`, `en-gb`, speed `0.95`.
Success means the same model, voice, quality controls and intonation policy are
used on every surface; legacy Piper synthesis and per-application TTS choices
are no longer production paths. Interactive speech must begin quickly enough
to be practical as an Alexa replacement, remain interruptible where the client
supports it and preserve the existing fully local privacy boundary.

This project produces Aster speech and therefore adopts the repository-wide
Aster voice standard without exception.

## Current state and evidence

- The authoritative source is the Forgejo HomeLab repository and this project.
  Live state remains authoritative for deployed versions and behavior.
- Aster Speech runs on unprivileged LXC 116 (`aster-speech`,
  `192.168.70.14:9130`, VLAN 70) with 6 vCPU, 4 GiB RAM, 512 MiB swap and a
  16 GiB disk. Read-only discovery on 2026-10-10 found the service active at
  about 275 MiB resident memory.
- The service has one Uvicorn worker. It loads `faster-whisper` `base.en` on
  CPU with `int8` compute, serializes transcription behind one lock and calls
  transcription with beam size 1.
- Interactive TTS is legacy Piper `en_US-lessac-high`, length scale `1.15`.
  It starts a subprocess for each request, generates a complete temporary WAV
  and returns audio only after synthesis finishes. It applies no canonical
  speech cleanup.
- Browser and native Companion clients split replies only near 1,800
  characters and wait for each complete WAV before requesting/playing the next
  chunk. Browser capture requests only generic `audio:true`; explicit capture
  constraints and measured turn telemetry are absent.
- Health, private/public speech routing, Authentik JWKS and Companion OIDC
  probes passed on 2026-10-10. No STT/TTS errors appeared in the queried recent
  journal window, but absence of use is not performance evidence.
- The production News Digest on LXC 114 already runs the approved Kokoro model
  and `bm_daniel` voice. It contains the accepted sentence/clause splitting and
  cleanup for Markdown, parentheses, currency and dotted United States
  abbreviations. Its batch renderer is application-local and CPU-heavy for a
  roughly fifteen-minute briefing; that does not establish interactive
  time-to-first-audio.
- Git commits `25bf4ef`, `cba252f`, `2170727`, `4c824b7` and `eaf427a` record
  the accepted voice identity, cross-project requirement, real listening
  selection, shorter-unit repair and pronunciation repair. The Companion
  project explicitly identifies deployed Piper as migration-only legacy state.
- Prior Companion repairs already fixed blocking STT, stale reverse-proxy
  connections, JWKS reachability, serialized turns, recording bounds,
  playback error visibility and temporary-audio retention. They remain
  regression requirements, not work to rediscover.
- Daily Proxmox backup and the TrueNAS guest-archive mirror cover LXC 116. A
  prior isolated file-level restore exercised Piper, cached Whisper and the
  service module. Kokoro assets and the future shared pronunciation policy are
  not yet part of that proof.

## Scope and exclusions

### In scope

- Evolve LXC 116 into the single canonical Aster Voice Service while retaining
  its existing identity, authentication boundary and recovery route.
- Load the approved Kokoro model/voice persistently and expose bounded
  interactive synthesis with sentence/clause-aware incremental audio delivery.
- Create one shared speech-text normalization and pronunciation policy used by
  interactive replies and batch narration.
- Preserve and improve local STT: benchmark current `base.en`, add safe
  household/domain hints, evaluate VAD and capture preprocessing, and promote
  only a measured configuration that meets latency/accuracy gates.
- Add an internal stable API plus a Wyoming-compatible TTS/STT integration or
  equally native Home Assistant adapter selected after source/live validation.
- Migrate Companion web/Mac, News Digest and Home Assistant consumers one at a
  time; retain last-known-good rollback until each passes.
- Add cancellation/barge-in semantics where the client and protocol support
  them. A new utterance must stop stale playback and generation safely.
- Add non-content timing, queue, dependency and version telemetry; no raw audio
  or transcript logging.
- Reconcile Doctor, Beszel, backup/restore, NetBox service facts, runbooks,
  architecture, human wiki, derived Aster mirror and user handover.
- Commit completed milestones and synchronize them through Forgejo under the
  repository's remote-write rule.

### Allowed operational change classes

- Install pinned local model/runtime dependencies and voice assets on LXC 116.
- Change the Aster Speech source, unit/drop-ins and protected non-secret
  settings with pre-change checkpoints and service-only restarts.
- Change tracked Companion and News Digest clients, deploy them through their
  existing paths and restart only affected services.
- Configure Home Assistant's existing Assist/Wyoming facilities or one
  source-reviewed local adapter; snapshot VM 103 before material configuration.
- Add only the exact private DNS/service record or narrow inter-VLAN rules
  proven necessary for Home Assistant/News consumers to reach the service.
- Update existing monitoring, backup manifests and systems of record required
  by the integration checklist.

### Explicit exclusions

- No premium/cloud STT, TTS or speech-to-speech service; no household audio,
  transcript, voice sample or device state leaves the HomeLab.
- No alternate Aster voice, voice cloning, model-voice upload or weakening of
  the approved Kokoro `bm_daniel` identity without a new explicit decision.
- No new public ingress, port forward, tunnel or unauthenticated speech API.
  The existing authenticated Companion HTTPS path may carry the new protocol.
- No new reasoning model, change to `aster-llama`, general Home Assistant
  authority expansion, entity exposure change or new device-control ability.
- No retention of microphone audio or transcripts beyond request-lifetime
  processing; bounded synthetic fixtures may be retained when documented.
- No broad VLAN trust rule. Consumer access is source/destination/port-specific.
- No multi-room hardware purchase or physical installation in this project.
- No deletion of the Piper rollback or old News renderer until graduation and
  accepted restore/rollback evidence.

## Authority model

| Fact or control | Authority |
|---|---|
| Aster voice identity and policy | HomeLab Git voice standard and this project |
| Deployed service version/health | LXC 116 systemd, service health and measured probes |
| Home Assistant pipeline/entity authority | Home Assistant; this project changes speech components only |
| Consumer behavior | Each tracked client plus its deployed runtime |
| VM/LXC/IP/VLAN/service inventory | NetBox where adopted; live state verifies |
| Authentication | Existing Authentik Companion identity and service-local protected credentials |
| Pronunciation and normalization | Versioned Aster Voice Service policy in Git |
| Human operation and recovery | Aster Companion/voice runbook and human wiki |
| Derived Aster knowledge | Provenance-labelled mirror; never operational authority |

Reasoning systems return text. They do not select a voice, synthesize audio or
override speech policy. The Aster Voice Service is the only production speech
renderer regardless of whether text came from deterministic Home Assistant,
`aster-llama`, a later GPT-backed reasoner or a scheduled briefing.

## Architecture and data flows

```text
Home Assistant VM 103 ───────┐
Aster Companion LXC 104 ─────┤
News Digest LXC 114 ─────────┼─ authenticated/private text + request policy
future reasoning backend ────┘
                               │
                               v
                  Aster Voice Service, LXC 116
                  - normalization/pronunciation
                  - sentence/clause segmentation
                  - persistent Kokoro bm_daniel
                  - local STT and VAD
                  - streaming/cancellation
                               │
                               v
                    PCM/streamed audio to caller
```

The initial design target keeps TCP 9130 and the current authenticated
Companion route. M1 must determine whether Wyoming should share the process on
a separate private port or be adapted behind the same service. Final ports,
call identities and firewall tuples are frozen before deployment. Batch news
requests may use the same service with longer timeouts but may not block the
interactive queue; scheduling, priority or a separate bounded worker must be
measured rather than assumed.

The first-audio path is: receive a speech-ready sentence, normalize it, render
the first bounded unit, begin playback, render later units concurrently within
a strict queue limit, and cancel unsent/stale units on interruption. Arbitrary
LLM token fragments are never committed as independent speech units.

## Privacy and security design

- All speech inference and voice assets remain local. No third-party speech
  account, API key or data-processing dependency is introduced.
- Reuse the existing Companion JWT/dedicated-key boundary where applicable.
  Home Assistant and News receive separate least-privilege caller identities
  if authentication cannot reuse an existing non-shared mechanism. Secrets
  remain outside Git and are never printed into evidence.
- Bind only to the required private address. Preserve NPM/Authenik for remote
  Companion access; internal integrations do not bypass authentication merely
  because they are on trusted network segments.
- Logs contain request IDs, durations, sizes, model/policy versions, queue
  depth and error classes—not input text, transcript text, raw audio, JWTs or
  voice samples.
- Normalize untrusted text as content, not instructions. Bound characters,
  synthesis units, duration, concurrency, memory, timeouts and cancellation.
- Validate voice/model files by pinned digest and retain provenance/licence
  evidence. Do not clone or export `bm_daniel` to another engine.
- Home Assistant continues to own device intent, entity exposure and service
  calls. The speech service receives no Home Assistant credential or device
  mutation capability.
- AI administration: not currently supported. The speech API is a media
  service, not an administrative API. Human SSH/Proxmox recovery remains the
  break-glass path; no AI-PAM management capability is added in this scope.

## Pre-start risk assessment

Jason accepted this risk envelope and Stream A start on 2026-10-10.

| Risk | Likelihood / impact | Control and residual risk |
|---|---|---|
| Canonical service becomes a speech single point of failure | Expected / medium | Keep Piper and application-local News rollback through graduation; fail visibly; typed/visual control remains. Host failure is still a shared lab limitation. |
| Kokoro misses interactive latency target on CPU | Plausible / high usability | Benchmark cold/warm first audio and p95 before cutover; persistent load, bounded units and queue isolation; reject or resize/re-place locally rather than hide latency. |
| News batch starves interactive speech | Plausible / medium | Separate priority/concurrency, measure simultaneous load, schedule-aware guard and abort threshold. Residual CPU contention requires evidence. |
| STT misrecognition triggers wrong HA intent | Plausible / high | This project does not broaden entity exposure; representative/far-field tests, safe hints/VAD, HA confirmations/allowlists remain authoritative. |
| Text cleanup changes meaning | Plausible / medium | Versioned rules, semantic fixtures, preserve displayed source text, targeted rather than broad substitutions. |
| Sentence streaming creates seams or cadence drift | Plausible / medium | Accepted chunk policy, bounded crossfade/silence only if listening tests support it, identical fixtures on every surface. |
| Authentication/proxy migration breaks phone voice | Plausible / medium | Preserve current path, regression-test JWT/JWKS and iPhone behavior, atomic source rollback. |
| Narrow new HA network path expands trust | Plausible / high | Exact VM-source to LXC 116 port only, logged and ordered before private blocks; no general Servers-to-Lab permit. |
| Model/licence or asset provenance is insufficient | Unknown / high longevity | Verify model, voice-pack and dataset distribution terms before central promotion; stop if rights are unclear. |
| Audio/transcript leakage through diagnostics | Plausible / high privacy | Synthetic fixtures, content-free logs, secret/content pattern review, request-lifetime temporary storage only. |
| Backup captures incomplete/unrecoverable voice state | Plausible / medium | Add model/policy/runtime to manifest, checksum local/off-host archive and perform isolated restore before graduation. |

No destructive or irreversible operation is planned. No credential rotation,
public exposure, broad trust change or removal of the last recovery copy is
authorized. Failure to verify a checkpoint, voice rights, exact network tuple,
rollback or materially adequate capacity is a stop condition for that mutation.

Likely interruptions are brief service-only restarts during staged deployment.
They are detected by current health probes plus new synthesis/version checks.
Companion retains typed interaction; Home Assistant retains dashboard/manual
control; the News Digest retains its accepted local renderer until migration.

## Persistence plan

This document is the durable project state. Each milestone records source/live
digests, accepted configuration, checkpoints, validation, blocker and next safe
action. Candidate deployments use a new file/root or service version and do not
replace the accepted path until tests pass. Keep model downloads and generated
audio out of Git.

On resume: read `AGENTS.md`, the Project Creation Standard and this document;
inspect Git status without overwriting unrelated work; verify the last recorded
source/live hashes and current service health; resume the first unchecked gate.
Never infer that an interrupted deploy, firewall write or Home Assistant change
succeeded. Reconcile before retry.

Current resume point: M0 is complete. Begin M1 with read-only licence/runtime,
Home Assistant protocol and network-path discovery, then build an offline
benchmark harness. No production component has been changed by project start.

## Milestones

- [x] **M0 — Baseline, project and authorization.** Inspect source/history and
  live LXC 116; record consumers, legacy/canonical mismatch, scope, risks,
  exclusions, rollback and Stream A authorization. Gate: project/index/changelog
  committed and synchronized; no production mutation.
- [ ] **M1 — Voice contract and measured design.** Verify Kokoro/voice licence
  and exact pinned assets; inventory live runtime and Home Assistant Assist/
  Wyoming support; define normalization, pronunciation, request/stream/cancel
  schemas, ports and caller identities; create offline fixtures and benchmark
  current Piper versus persistent Kokoro. Gate: warm/cold p50/p95, RTF, memory,
  concurrency and quality evidence; final deployment/rollback manifest.
- [ ] **M2 — Canonical service candidate.** Implement persistent Kokoro,
  sentence/clause policy, shared cleanup, bounded streaming, cancellation,
  content-free telemetry and compatibility endpoints. Gate: unit/integration,
  malformed/adversarial, cancellation, concurrency and secret/content tests;
  no deployment.
- [ ] **M3 — Staged LXC 116 deployment.** Verify backup/checkpoint; install
  pinned candidate beside the accepted service; run private canary and measured
  load; atomically select it only after gates pass. Gate: two independent
  authenticated synthesis passes, rollback rehearsal and current path health.
- [ ] **M4 — Companion migration.** Update web and native clients for
  sentence-streamed playback, explicit audio capture constraints, cancellation
  and useful failure states. Gate: automated regressions plus Jason's phone/Mac
  listening and responsiveness acceptance; typed interaction unaffected.
- [ ] **M5 — News migration.** Route the briefing through the canonical service
  without allowing batch work to starve interactive traffic; preserve chapters,
  pauses, schedule and rollback renderer. Gate: same approved voice/policy,
  valid artifact, simultaneous-interaction load test and schedule recovery.
- [ ] **M6 — Home Assistant integration.** Snapshot VM 103, add the selected
  native Wyoming/local adapter and exact private network/auth path, without
  changing entity exposure or device authority. Gate: normal/refused commands,
  interruption, dependency failure and rollback on one pilot surface.
- [ ] **M7 — STT and capture quality.** Compare current `base.en` against a
  bounded shortlist using real-consent listening tests and synthetic fixtures;
  add domain hints/VAD/capture controls only with measured benefit. Gate:
  accuracy and p95 response target, far-field/noise cases, no content retention.
- [ ] **M8 — Operations, recovery and graduation.** Close all integrations,
  restore the complete service in isolation, run failure/degradation tests,
  reconcile Beszel/NetBox/wiki/mirror/runbooks and complete user handover and
  efficiency review. Gate: two independent end-to-end production passes from
  each surface, accepted latency/voice identity and no unexplained legacy path.

## Validation and evaluation

Freeze an evaluation script before tuning. It must include short HA
confirmations, conversational replies, dates/times, money/measurements,
Markdown, URLs, acronyms, dotted initials, household/device names, questions,
long sentences and multi-sentence news. Use identical text across renderers.

Record:

- STT exact/semantic command accuracy and entity-name accuracy;
- capture duration, endpoint delay, STT completion, LLM first text, TTS first
  playable audio, completion and client playback start;
- p50/p95 and cold/warm results, audio real-time factor, queue time, CPU/RSS,
  timeouts and cancellation latency;
- pronunciation defects, seams, distortion, cadence, voice identity and
  subjective listening acceptance;
- one and two simultaneous interactive users plus concurrent News rendering;
- malformed/empty/oversized text/audio, unsupported codec, stale/revoked auth,
  dependency loss, restart, interrupted request and replay behavior;
- denied unauthenticated/cross-scope calls and absence of content in logs;
- rollback to Piper/local News with existing typed/manual controls intact.

Provisional interactive targets, frozen or revised with evidence in M1:
warm p95 STT after end-of-speech <= 1.5 seconds; first playable speech after the
first complete response sentence <= 750 ms; cancellation audible stop <= 250
ms; no queued News work may push warm interactive first audio above 1.5 seconds.
Targets are requirements, not claims of current performance.

Before graduation, review whether every integration actually uses the single
service, whether the network hop improves rather than degrades operation, and
whether CPU, queueing, dependency count, updates and household friction justify
the architecture. A working but slow or inconsistently voiced system does not
graduate.

## Observability and maintenance

- Extend HomeLab Doctor from liveness/JWKS to model/policy version, bounded
  synthesis canary, dependency and backup freshness without routine content.
- Add low-cardinality request, error, p50/p95 latency, queue depth, cancellation
  and worker saturation metrics to existing monitoring where actionable.
- Reconcile LXC 116 in Beszel after resource/runtime changes; do not duplicate
  host alerts already owned there.
- Pin model/runtime dependency versions and digests. Test candidates offline,
  then rerun conformance/listening fixtures before promotion.
- Jason owns actionable alerts and listening acceptance. Avoid alerts for a
  single recoverable client cancellation or expected idle periods.
- The News schedule remains owned by its existing timer. The speech service is
  continuously available through systemd with bounded restart behavior.

## Backup, restore and rollback

Protect source, service unit, non-secret configuration, normalization and
pronunciation policy, pinned dependency manifest, Kokoro model/voice assets or
their verified reproducible source, and caller configuration. Credentials stay
in protected live configuration and existing encrypted guest backups, never Git.

Before deployment, verify the latest LXC 116 Proxmox archive and TrueNAS mirror
and retain a source/unit/runtime checkpoint. Before Home Assistant changes,
create and verify its normal recovery point. Restore into an isolated directory
or non-conflicting guest first; validate checksums, model load, synthetic TTS,
STT and health before any cutover.

Rollback order: stop new consumer routing; select the retained Piper service or
application-local News renderer; restore only the changed client/config; remove
only the exact new firewall/service rule if it is no longer used; verify typed,
manual and pre-project speech paths. Do not restore a whole firewall or VM over
later unrelated changes.

## Documentation and systems-of-record integration

- [ ] **HomeLab Doctor** — model/policy-aware health, synthesis canary,
  dependency and backup-age behavior with tested failures.
- [ ] **Monitoring/alerting** — latency/queue/error/resource signals and final
  Beszel reconciliation for LXC 116 and any deliberately excluded component.
- [ ] **Backup and recovery** — full voice assets/policy/runtime coverage,
  checksum verification and isolated restore.
- [ ] **NetBox** — reconcile LXC 116 service/port and any Home Assistant
  service relationship; no new guest/IP currently proposed.
- [ ] **Human wiki** — one Aster Voice Service page with operation, consumer,
  privacy, recovery and troubleshooting guidance.
- [ ] **Aster mirror/snapshot** — publish a provenance-labelled derived summary
  only after the operational record is current.
- [ ] **Operational reference and runbooks** — replace Piper/current-client
  facts and document canary, rollback, model update and caller diagnosis.
- [ ] **Repository documentation** — architecture, project portfolio,
  changelog and voice standard/implementation links.
- [ ] **Diagrams/rack records** — logical voice flow update; no physical rack
  change expected.
- [ ] **Homepage/service discovery** — not applicable unless an operator UI is
  added; Companion already links the user-facing service.
- [ ] **Authentication/authorization** — separate least-privilege caller paths,
  existing Companion OIDC/JWT and human recovery; no shared admin credential.
- [ ] **DNS, certificates and firewall** — prefer no new DNS/certificate; record
  and test only exact private tuples needed by HA/News.
- [ ] **Automation and schedules** — preserve News ownership; bound service
  concurrency/restarts and missed/failed generation behavior.
- [ ] **Security inventory** — asset provenance/licence, secrets outside Git,
  file ownership/modes, patch owner and temporary-access removal.
- [ ] **AI administration integration** — not currently supported; no safe or
  useful management API is in scope, human SSH/Proxmox is break-glass.

## User-facing handover requirement

Before graduation, provide one plain-language guide covering:

- what Aster sounds like and which surfaces now share it;
- phone/Mac/web launch and existing passkey authentication;
- Home Assistant normal voice workflow and unchanged entity/control limits;
- listening/thinking/speaking/interrupted/error states and Stop speech;
- what remains available when voice, the network or LXC 116 is unavailable;
- privacy boundaries and confirmation that routine audio is not retained;
- operator health/rollback paths and any manual acceptance action.

Jason must complete a real walkthrough on Companion and the Home Assistant
pilot and listen to a regenerated News briefing before graduation.

## Graduation criteria

- Every production Aster speech surface uses the exact canonical service,
  model, voice and policy; no unrecorded application-local TTS remains.
- Voice identity, pronunciation and cadence pass Jason's real listening test on
  phone, Mac/web, Home Assistant and News.
- Provisional or M1-frozen latency/cancellation/concurrency thresholds pass at
  p95 under normal and News-overlap load.
- STT meets the frozen household/entity accuracy cases without retaining
  content or broadening Home Assistant authority.
- Authentication, denied access, malformed input, dependency failure, restart,
  reboot, interruption and rollback tests pass.
- Doctor, monitoring/Beszel, backups, isolated restore, NetBox, wiki, Aster
  mirror, runbooks, architecture and handover agree with live state.
- Two independent end-to-end passes succeed for every critical production
  surface; residual limitations are explicit and accepted.
- Post-deployment intent/efficiency review finds the single service genuinely
  improves identity and operation at acceptable resource/maintenance cost.

## Evidence log

| Date | Milestone/action | Evidence | Result / next safe action |
|---|---|---|---|
| 2026-10-10 | M0 source discovery | Authoritative checkout, relevant voice history, service/client code, project standard, operations and Companion runbook inspected. Existing unrelated brand-design edits left untouched. | Canonical-vs-legacy mismatch and known client/service constraints recorded. |
| 2026-10-10 | M0 live discovery | Read-only Proxmox/LXC 116 inspection: unprivileged guest, 6 cores/4 GiB, one active Uvicorn worker, `base.en`, `lessac-high`; health/JWKS/OIDC/HTTPS probes pass. Secret value redacted and not retained. | Current service is healthy legacy state and the rollback baseline. |
| 2026-10-10 | Stream A decision | Jason rejected premium services and directed a network-level single solution using the approved voice, with project creation, commit, push and immediate Stream A start. | Risk envelope accepted; M0 complete, M1 starts with read-only design/licence/protocol discovery and offline benchmarks. |

## Close-out

Open. Final close-out will record the selected protocol/ports, release hashes,
consumer inventory, measured performance, restore/rollback evidence, accepted
limitations, maintenance owner and any deliberately deferred satellite work.
