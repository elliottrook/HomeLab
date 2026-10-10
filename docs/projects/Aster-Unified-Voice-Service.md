# Aster Unified Voice Service

> Status: Active — Stream A; M0–M2 complete, M3 in progress; candidate staged,
> production selection withheld on uncached latency; B60 acceleration blocked
> by disabled Resizable BAR
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

Current resume point: M0 through M2 are complete and M3 is active. The approved
voice, normalization/pronunciation rules, acknowledgement, capacity topology,
API/network/dependency manifest and rollback plan are frozen. The next safe
action is to improve or explicitly accept the uncached first-audio result before
any production selector change. The candidate is installed but stopped and
disabled on LXC 116; production port 9130 remains authoritative and healthy.
The approved B60 experiment cannot proceed until the Proxmox host exposes a
Resizable BAR larger than 256 MiB; that requires a separate physical/firmware
maintenance decision rather than a live production-host PCI reconfiguration.

## Milestones

- [x] **M0 — Baseline, project and authorization.** Inspect source/history and
  live LXC 116; record consumers, legacy/canonical mismatch, scope, risks,
  exclusions, rollback and Stream A authorization. Gate: project/index/changelog
  committed and synchronized; no production mutation.
- [x] **M1 — Voice contract and measured design.** Verify Kokoro/voice licence
  and exact pinned assets; inventory live runtime and Home Assistant Assist/
  Wyoming support; define normalization, pronunciation, request/stream/cancel
  schemas, ports and caller identities; create offline fixtures and benchmark
  current Piper versus persistent Kokoro. Gate: warm/cold p50/p95, RTF, memory,
  concurrency and quality evidence; final deployment/rollback manifest.
- [x] **M2 — Canonical service candidate.** Implement persistent Kokoro,
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

### M1 working record — 2026-10-10

Read-only discovery and synthetic in-memory timing established the following
initial facts. These are design inputs, not completion evidence:

- Home Assistant VM 103 is healthy on HAOS 18.2, Core 2026.9.1 and Supervisor
  2026.09.3 with 2 vCPU and 4 GiB RAM at `192.168.20.11`. Its QEMU guest agent
  is available, so later pre/post-change evidence need not expose HA secrets.
- Home Assistant's supported external-service path is the Wyoming integration.
  Wyoming carries local STT/TTS over JSONL plus PCM, advertises models/voices,
  supports streamed synthesis text/audio, and requires no Home Assistant token
  in the speech service. The candidate therefore adds a dedicated Wyoming
  listener for VM 103 while retaining authenticated HTTP for Companion/News.
- The production News reference uses `kokoro-onnx` 0.6.1, ONNX Runtime 1.30.0,
  NumPy 2.5.3 and SoundFile 0.14.0. The deployed FP16 model is 163,527,961
  bytes with SHA-256
  `f3a290d384fbb27966d462905c71a46cef9e5fd00516b40df32a0b4afe77ac96`;
  `voices-v1.0.bin` is 28,214,398 bytes with SHA-256
  `bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d`.
- Upstream records `kokoro-onnx` code as MIT and Kokoro-82M model weights as
  Apache-2.0. The model card says v1.0 used permissive/non-copyrighted audio and
  lists its CC-BY attribution. Preserve those notices in the deployment
  manifest; verify the exact ONNX release provenance before closing M1.
- LXC 114 has 8 allocated cores/8 GiB; LXC 116 has 6 cores/4 GiB. Both run on
  the Xeon E5-2698 v4. The latest 11-story News job consumed 31m58.822s CPU and
  peaked at 864.9 MiB, so batch narration must never share an unprioritized
  interactive queue.
- One bounded persistent-FP16 sample on LXC 114 loaded in 1.966 seconds and
  rendered identical 4.833-second synthetic speech in 2.116, 2.191 and 2.213
  seconds (RTF 0.438–0.458), with 694,128 KiB maximum RSS. This is not a p95
  result and does not yet compare LXC 116. It proves a complete-WAV response
  cannot meet the provisional 750 ms first-audio target; clause-sized output
  must begin playback while later units render.
- ONNX Runtime emitted CPU-affinity errors inside the constrained LXC cpuset.
  Explicit bounded intra/inter-op thread settings must be benchmarked in M1;
  leaving implicit host-wide affinity is not an acceptable production design.
- The existing Piper baseline remains the recorded 1.68-second TTS result from
  Companion close-out evidence. The frozen harness now supersedes it for
  comparative work: three iterations over eight identical fixtures produced
  median 2.321 seconds, p95 4.027 seconds, median RTF 0.451 and p95 RTF 0.633;
  the short HA confirmation took 1.017–1.068 seconds. Piper model SHA-256 is
  `4cabf7c3a638017137f34a1516522032d4fe3f38228a843cc9b764ddcbcd9e09`.
- The new `services/aster-speech/benchmark_tts.py` and versioned nine-case
  synthetic corpus produce content-free JSON with fixture/asset digests,
  load time, p50/p95 synthesis, RTF, RSS and thread settings. Six focused
  unit tests pass. The broader local speech suite remains unexecuted on the Mac
  because its system Python lacks PyJWT; existing service-environment testing
  remains required before M1 closes.
- Persistent FP16 Kokoro with package-default threading on LXC 114 produced
  median 1.816 seconds, p95 3.538 seconds, median RTF 0.384 and p95 RTF 0.422
  over the same 24 samples. The short HA case took 0.786–0.792 seconds, but
  ONNX Runtime attempted invalid host CPU affinities and peak RSS was 901,576
  KiB.
- An explicit ONNX Runtime session using six intra-op and one inter-op thread
  removed the affinity errors. A confirming 24-sample run improved median to
  1.507 seconds, p95 to 2.941 seconds, median RTF to 0.316 and p95 RTF to
  0.341; short HA synthesis was 0.641–0.663 seconds and peak RSS was 899,272
  KiB on LXC 114. This was a useful reference setting but did not transfer as
  the optimum on the speech guest.
- The identical pinned runtime/assets were copied only into an isolated
  `/tmp` candidate on LXC 116 while its accepted Piper API remained active.
  Digests matched before execution. Six/one threads produced median 2.329
  seconds, p95 4.435 seconds, median RTF 0.490 and short-HA latency
  1.013–1.029 seconds. Three/one was slower than four/one in a bounded pass.
- Four intra-op/one inter-op threads are the current LXC 116 candidate. The
  confirming 24-sample run produced median 1.849 seconds, p95 3.448 seconds,
  median RTF 0.384, p95 RTF 0.411 and 901,100 KiB peak RSS. The 27-character
  HA confirmation rendered in 0.748, 0.763 and 0.810 seconds. This nearly meets
  but does not pass the 750 ms p95 requirement; M2 must stream a smaller first
  acknowledgement clause and may not claim compliance from the median alone.
- The corpus initially included the exact minimal first unit `Done.` and the
  harness can select bounded cases by fixture ID. Ten warm four-thread samples
  on LXC 116 rendered in 0.390–0.446 seconds with median 0.398 and p95 0.446
  seconds. This passes the server-side first-unit target and leaves about 300 ms
  for transport and playback startup; end-to-end proof remains required.
- Two simultaneous four-thread engines oversubscribed the six-vCPU guest:
  median acknowledgement latency rose to 0.809/0.853 seconds and p95 to
  0.916/1.130 seconds. That topology is rejected despite safe memory use.
- Two simultaneous workers with two intra-op threads and one inter-op thread
  each produced median acknowledgement latency 0.655/0.648 seconds and p95
  0.663/0.652 seconds, at approximately 555 MiB maximum RSS per process. This
  is the M2 concurrency candidate: two persistent workers, interactive queue
  capacity two, a smaller immediate acknowledgement unit, and bounded later
  clause rendering. News remains separately queued at lower priority and may
  not occupy both interactive workers.

Primary protocol/licence references:

- `https://www.home-assistant.io/integrations/wyoming`
- `https://github.com/rhasspy/wyoming`
- `https://github.com/thewh1teagle/kokoro-onnx/blob/main/LICENSE`
- `https://huggingface.co/hexgrad/Kokoro-82M`

No service, firewall, model, Home Assistant integration or production file was
changed during this discovery. Benchmark audio was not retained. Four temporary
24 kHz/16-bit/mono listening WAVs were generated from the pinned production
reference renderer, checksum-verified after transfer and kept outside Git for
Jason's M1 listening decision.

Jason's first listening pass rejected the normalization sample: `CA
$1,234.50` was spoken as a malformed “one, two hundred and thirty-four CA
dollars,” and dotted `B.C.` had unnatural pronunciation. The fault was in the
reference text cleanup, not the approved voice. The candidate cleanup now
expands the amount to “one thousand two hundred and thirty-four Canadian
dollars and fifty cents” and `B.C.` to “British Columbia”; it also names
United States/Australian dollar prefixes and handles singular dollars/cents.
Nine cleanup regressions pass. A corrected listening WAV was rendered from
the pinned reference assets and remains pending Jason's acceptance; production
News code/audio was not changed.

Jason's next listening pass also rejected the bare `Done.` acknowledgement as
clipped and unnatural, and rejected the default readings of `Home Assistant`
and `Lutron Caseta`. Bare one-word acknowledgements are therefore removed from
the candidate policy. `There, that's done.` is the accepted acknowledgement.
The installed Kokoro path produced an invalid, abnormally long result from its
documented inline phoneme markup, so that approach was rejected; controlled
speech-only respellings for Home Assistant and Lutron Caséta are under
listening review instead. None of these choices is frozen until the comparison
audio is accepted.

Jason accepted pronunciation comparison option 5. The shared speech policy now
maps `Home Assistant` to the speech-only rendering “Home uh-sist-unt” and both
`Lutron Caseta` and `Lutron Caséta` to “Loo-tron kuh-set-uh”. Written UI text
retains the correctly branded names. This decision covered pronunciation only;
the acknowledgement was accepted separately in the following listening pass.

Jason subsequently accepted acknowledgement comparison option 3: `There,
that's done.` This wording supplies enough context for the approved voice to
render “done” naturally, avoids the rejected “ookay” onset, and is now the
canonical Home Assistant success acknowledgement fixture.

A bounded ten-sample warm reference check on LXC 114 rendered the accepted
acknowledgement in 0.648–0.657 seconds (median 0.653, p95 0.657). This is useful
evidence that the wording remains responsive, but it does not replace the M2
end-to-end measurement on the final two-worker LXC 116 service.

### M1 frozen candidate manifest

This is the candidate to implement in M2; it is not a statement of deployed
state.

| Item | Frozen candidate |
|---|---|
| Host/runtime | Existing unprivileged LXC 116; Python 3.13 candidate venv; `kokoro-onnx` 0.6.1; ONNX Runtime 1.30.0 |
| Voice | Exact FP16 model/voice hashes above; `bm_daniel`; `en-gb`; speed `0.95`; PCM mono 24 kHz/16-bit output |
| Interactive workers | Two persistent processes; two intra-op threads and one inter-op thread each; queue capacity two |
| Batch policy | Lower-priority queue, maximum one worker only when no interactive item waits; yield between bounded units; no second worker occupation |
| STT | Existing persistent faster-whisper `base.en`, CPU `int8`, serialized initially; independent timing/accuracy gate remains M7 |
| HTTP compatibility | Keep authenticated `POST /v1/stt` and complete-WAV `POST /v1/tts` during migration; same current limits and credentials |
| Streaming HTTP | Add authenticated `POST /v2/tts/stream`; request contains text and optional request ID only; server owns voice; response is ordered bounded PCM/WAV audio frames with request/unit metadata and an explicit end/error frame |
| Cancellation | `DELETE /v2/tts/{request_id}` and client disconnect mark queued/unsent units stale; workers check between units; client immediately stops local playback |
| Companion identity | Existing Authentik issuer/audience/JWKS or dedicated recovery key through current HTTPS `/voice/` route; no new public route |
| News identity | New dedicated service credential stored outside Git; HTTP batch class; longer timeout; never reuse Companion's recovery key |
| Home Assistant | Native Wyoming TCP listener on `192.168.70.14:10300`; advertise only canonical `aster-bm-daniel` TTS and current bounded STT |
| HA trust boundary | Exact OPNsense allow: source VM 103 `192.168.20.11` to destination `192.168.70.14`, TCP 10300, ordered before the Servers private-network block; listener also rejects non-HA peers where the socket API permits |
| Wyoming authentication exception | Wyoming has no bearer/mTLS field supported by the HA integration. Identity is therefore the exact stateful firewall source tuple plus dedicated listener, not general VLAN trust; TCP 9130 remains authenticated |
| Existing network paths | Preserve NPM `192.168.50.23` to TCP 9130 and exact speech-to-JWKS HTTPS egress; LXC 114 reaches authenticated TCP 9130 only after its dedicated credential exists |
| Normalization | One versioned policy derived from News `speech_text`; Markdown/link/code markers, parentheses, currency and approved abbreviations; segmentation follows normalization |
| First-unit policy | Never use the bare one-word `Done.` acknowledgement: listening found it clipped and unnatural. The accepted default is `There, that's done.`; never acknowledge before HA reports success. Other replies wait for the first complete semantic clause; no arbitrary token fragments |
| Limits | Existing 15 MiB STT and 2,000-character compatibility bounds; v2 adds bounded units, request duration, queue depth, connection count and per-caller rate limits before deployment |
| Telemetry | Request ID, caller class, policy/model versions, sizes, queue/worker timing, cancellation and error class only; never text, transcript, audio or credentials |

Deployment is a side-by-side candidate under a versioned root with a separate
unit/socket first. M3 must verify current LXC backup age and file-level recovery,
asset/source/unit digests, two authenticated candidate passes, Wyoming source
denial/allow behavior and rollback before selecting it. The accepted Piper unit,
environment and model remain unchanged until selection.

Rollback is consumer-first: stop new v2/Wyoming routing; restore Companion to
complete-WAV v1, News to its application-local renderer and HA to its prior
pipeline; then stop/disable only the candidate unit and remove only its exact
firewall rule if unused. Verify Piper v1, STT, typed Companion, HA manual control
and News schedule. Do not restore the whole guest, firewall or HA VM over later
unrelated state.

### M2 working record — 2026-10-10

- Added the repository-only canonical core in
  `services/aster-speech/voice_candidate.py`; no production service imports it.
- The core implements the approved normalization and pronunciations, bounded
  semantic units, two interactive workers, a batch queue restricted to worker
  zero, ordered results, backpressure and request cancellation state.
- Five focused candidate tests and the six benchmark tests pass. Ten News text
  tests pass after the candidate tests exposed and repaired a sentence-final
  dotted-abbreviation punctuation loss in both normalization paths.
- The broader legacy speech discovery remains blocked on this Mac because its
  system Python does not include PyJWT; that known environment limitation does
  not affect the dependency-free M2 core tests and must be rerun in the service
  venv before the M2 gate closes.
- Added the dependency-free bounded `AVS1` audio-frame protocol and a separate
  FastAPI router candidate for authenticated streaming and cancellation. Caller
  class is server-owned, request IDs are generated or strictly validated, and
  error frames disclose only an exception class—not submitted text or details.
- Twelve M2 core/protocol tests and six benchmark tests now pass, along with ten
  News normalization tests. Shutdown testing exposed and repaired orphaned
  internal queue-wait tasks; the clean run emits no pending-task warnings.
- This remains repository-only. FastAPI adapter tests and integration with the
  actual authentication dependency must run in the pinned service environment;
  no route, listener, package or production service has changed.
- Added a pinned two-engine Kokoro renderer pool. Startup fails closed on either
  model/voice digest mismatch; each scheduler worker owns a distinct ONNX
  session with the accepted two-intra/one-inter thread limits. Compatibility
  WAV output wraps the same normalized PCM used by streaming.
- Added a separate candidate application, environment template and hardened
  systemd unit for port 9131. The accepted production unit does not import or
  reference any candidate module, and the candidate unit has not been installed
  or enabled.
- A temporary runtime check on LXC 114 verified both exact asset digests, loaded
  two persistent sessions in 4.287 seconds and completed simultaneous renders
  from both engines at 24 kHz. The outputs were even-length PCM buffers of
  78,880 and 142,368 bytes. Temporary scripts were removed; no audio was kept.
- Fifteen M2 core/protocol/renderer tests and six benchmark tests pass locally,
  plus ten News normalization tests. The FastAPI/Auth/JWT integration gate
  remains assigned to the isolated LXC 116 candidate environment.
- The first isolated LXC 116 application pass found and repaired a candidate
  lifecycle defect: the separate FastAPI app must explicitly initialize the
  reused Whisper model and lock. No production code or process was changed.
- With a synthetic temporary bearer key and no listening socket, the corrected
  candidate passed health, 401 refusal for TTS/STT, authenticated compatibility
  WAV, strict extra-field rejection, cancellation, two ordered PCM frames plus
  explicit end, and two simultaneous authenticated requests. Submitted text
  and audio were not logged or retained.
- Live synthesis of the accepted acknowledgement took 1.165 seconds on LXC
  116, so it did not meet the first-audio goal. The exact listening-approved
  phrase is now rendered once at startup and cached. A repeat integration pass
  returned its compatibility WAV in 0.002 seconds and returned the same cached
  response during a concurrent test in 0.004 seconds, while the other uncached
  request completed in 1.163 seconds. Caching does not authorize speaking
  before Home Assistant reports success.
- The two-sentence streaming fixture completed in 1.770 seconds with audio
  payloads of 142,368 and 78,880 bytes followed by an end frame. This buffered
  TestClient measurement is not a network first-audio measurement; M3 must
  measure the first received PCM frame through the real side-by-side listener.
- The isolated source, packages, model copies and synthetic key environment
  were deleted after both passes. The accepted production service remained
  active and healthy before and after testing.
- A second isolated pass used a real Uvicorn listener bound only to LXC 116
  loopback. Time to first response body was 0.055 seconds for a fresh client
  and 0.012 seconds warm for the cached acknowledgement; an uncached short
  response took 1.772 seconds. The cache therefore meets the acknowledgement
  path goal, while uncached reasoning speech remains a known M3 latency risk
  and must not be hidden by the compatibility result.
- Closing a client stream during synthesis cancelled its work and an immediate
  cached recovery request completed in 0.012 seconds. The first explicit
  DELETE probe exposed an incomplete chunked response: scheduler cancellation
  was being surfaced as transport cancellation. The protocol now distinguishes
  explicit API cancellation from disconnects, completes the former with a
  content-free `cancelled` frame, and continues to propagate genuine client
  disconnects.
- The corrected real-listener probe returned DELETE 204, HTTP 200 with exactly
  one `cancelled` frame, then HTTP 200 for the immediate recovery request. The
  service-environment suite passed 42 tests before that repair, including real
  FastAPI integration and mocked Authentik JWT rejection/acceptance; 19 focused
  local candidate/protocol/benchmark tests pass with the added cancellation
  regression. The Mac's broader discovery still lacks PyJWT, so its one import
  failure is an environment limitation rather than a candidate failure.
- The temporary listener, source, dependency and model staging were removed.
  Production `aster-speech` remained active and its health endpoint passed.
  These results close the M2 functional gate without authorizing deployment;
  the uncached first-audio target remains an explicit M3 acceptance item.

### M3 working record — 2026-10-10

- Verified the successful 2026-10-10 02:46 LXC 116 snapshot backup and its
  completion log. Seven daily guest backups were present and backup storage had
  about 2.61 TiB free. A protected in-guest checkpoint was also created under
  `/var/lib/aster-speech/checkpoints/20261010-m3-pre`; it contains the accepted
  source, production unit, protected environment and dependency freeze. All
  four recorded hashes verified and checkpoint files are mode 0600.
- Installed the candidate side by side under `/opt/aster-voice-candidate`, with
  approved assets under `/opt/aster-voice/models`, a separate protected
  environment and a separate disabled systemd unit on TCP 9131. The model,
  voice and source archive hashes matched the frozen values before startup.
  Production source, environment, unit and TCP 9130 were not replaced.
- Direct-pin installation exposed transitive dependency drift before service
  activation. That never-selected venv was quarantined and deleted. The active
  candidate venv was rebuilt from the captured production freeze plus the exact
  M2 Kokoro lock; `pip check` passed and the complete resulting freeze is now
  `requirements-candidate.lock`.
- The pinned candidate passed all 46 service-environment tests as the
  `aster-speech` account. Both candidate and production then reported healthy,
  with no warning-or-higher candidate journal entries. Candidate resident
  memory was approximately 1.22 GiB and its unit remained disabled.
- The real port-9131 canary refused missing credentials with 401, returned two
  valid authenticated mono 24 kHz WAV responses, emitted ordered
  `audio`, `audio`, `end` stream frames, completed two simultaneous synthetic
  requests successfully, returned DELETE 204 plus a content-free `cancelled`
  frame, and recovered immediately with HTTP 200.
- Measured candidate latency was 0.011 seconds for the cached acknowledgement,
  2.825 seconds for the uncached compatibility WAV, 1.521 seconds to the first
  streamed body, and 1.852/1.865 seconds for two concurrent short requests.
  Functionality and isolation pass, but uncached first audio still misses the
  frozen 0.750-second target. Production selection is therefore withheld.
- Rollback rehearsal stopped only `aster-voice-candidate`: TCP 9131 closed and
  production TCP 9130 remained healthy. The candidate remains installed,
  stopped and disabled for tuning; all temporary scripts, archives, copied
  assets and the never-selected drifted venv were removed.
- Jason approved exclusive use of the Proxmox Intel Arc Pro B60 for an
  acceleration experiment. A protected copy of LXC 116's configuration was
  captured, then only `/dev/dri/renderD128` was mapped to the existing
  `aster-speech` UID/GID. A separate OpenVINO 1.24.1 venv and Intel's official,
  hash-verified compute runtime 26.35.39758.10/IGC 2.41.5 were extracted under
  an isolated test root; no system package or production runtime was replaced.
- The provider correctly rejected GPU initialization instead of producing a
  valid B60 benchmark: Intel's runtime reported `Resizable BAR not detected`
  and OpenVINO reported `Device GPU is not available`. ONNX Runtime then fell
  back to CPU, which the probe detected and rejected. Live PCI evidence shows
  the physical B60 path is healthy at PCIe Gen3 x8, but physical BAR2 is only
  256 MiB although the card supports up to 32 GiB. This is a host firmware/
  PCI allocation prerequisite, not a Kokoro compatibility or capacity result.
- No risky live BAR resize or GPU driver unbind was attempted on the production
  Proxmox host. The render device was withdrawn live, the isolated runtime,
  cache, packages and probes were deleted, and production speech remained
  healthy. Proxmox has queued deletion of the temporary `dev0` config entry;
  it will disappear from the persistent LXC configuration on the next normal
  guest restart. The device is not currently visible inside LXC 116.

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
| 2026-10-10 | M2 real-listener close-out | Loopback-only Uvicorn canary on LXC 116: cached first body 55 ms fresh/12 ms warm; uncached 1.772 s; disconnect recovery 12 ms; explicit DELETE 204 followed by one content-free `cancelled` frame and successful recovery. Temporary listener/staging removed; production remained active and healthy. | M2 functional/security/cancellation gates complete. M3 remains pending; uncached first-audio latency is a tracked acceptance risk. |
| 2026-10-10 | M3 staged canary and rollback | Fresh guest backup plus protected file checkpoint verified; pinned candidate installed separately on 9131; 46 tests, authentication refusal, two WAV passes, streaming, concurrency, cancellation and rollback passed. Cached acknowledgement 11 ms; uncached first body 1.521 s. | Candidate left stopped/disabled and production 9130 healthy. Do not select it until uncached latency meets 750 ms or Jason explicitly accepts a revised threshold. |
| 2026-10-10 | M3 Arc Pro B60 acceleration probe | Least-privilege render-node mapping; isolated OpenVINO 1.24.1 and hash-verified Intel compute runtime; provider-fallback detection; live PCI BAR/link inspection; complete test-root cleanup and live device withdrawal. | No GPU benchmark claimed: B60 compute rejected because physical Resizable BAR is only 256 MiB. Production stayed healthy. Next step requires a planned BIOS/physical maintenance decision, or a different accelerator host. |

## Close-out

Open. Final close-out will record the selected protocol/ports, release hashes,
consumer inventory, measured performance, restore/rollback evidence, accepted
limitations, maintenance owner and any deliberately deferred satellite work.
