# Aster Unified Voice Service

> Status: Active — Stream A; M0–M3 and M5–M7 complete; M4 Companion migration
> and M8 close-out remain; M9 production graduation is approved but may not
> provision or cut over production until the M4/M8 and release-preflight gates pass
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
- Freeze the accepted service as Aster Voice V1, deploy it independently on the
  Servers VLAN, migrate consumers one at a time, and retain LXC 116 as a
  sanitized V1 lab baseline from which a separate V2 candidate may later start.
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
- Create one new unprivileged production guest on the Servers VLAN from the
  immutable V1 release manifest; assign separate production identities and
  protected configuration; add only the exact DNS, firewall, monitoring,
  backup and systems-of-record changes required for its consumers.
- After production acceptance, retain LXC 116 as the V1 lab baseline and create
  any future V2 work in a separate lab guest or replaceable clone.

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
- No in-place VLAN retag or identity conversion of LXC 116, no bidirectional
  production/Lab synchronization, no shared writable model/configuration path,
  and no production credentials or mutable household data copied into Lab.
- No V2 implementation in this project. M9 establishes the isolated lane and
  reproducible baseline only; a V2 project needs its own scope and acceptance.

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
| V1 source release | Forgejo commit and version manifest; optional release tag after explicit authorization |
| Production runtime and secrets | New production guest and protected production configuration |
| V1 lab baseline | Sanitized LXC 116 deployment derived from the accepted V1 release |

Reasoning systems return text. They do not select a voice, synthesize audio or
override speech policy. The Aster Voice Service is the only production speech
renderer regardless of whether text came from deterministic Home Assistant,
`aster-llama`, a later GPT-backed reasoner or a scheduled briefing.

The repository's GitHub copy remains the **protection mirror**. The retained
VLAN 70 deployment is the **V1 lab baseline**, not a live service mirror:
production owns live availability and credentials, while the baseline owns no
production traffic or mutable production state.

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
| New production guest differs from accepted V1 | Plausible / high | Install only from the immutable release manifest; compare source, dependency, model, voice and policy digests before consumer traffic. |
| Production and Lab identities or secrets cross-contaminate | Plausible / high | Separate credentials, DNS names, monitoring labels and protected configuration; sanitize the retained baseline and test cross-environment denial. |
| Consumer cutover causes household voice outage | Plausible / medium | Keep `.70.14` healthy, move one consumer at a time, verify two passes and reverse the consumer selector first on failure. |
| V2 experimentation mutates the only V1 recovery copy | Plausible / medium | Keep the V1 baseline immutable except controlled recovery tests; create V2 in a distinct clone/guest. |

No destructive or irreversible operation is planned. No public exposure, broad
trust change or removal of the last recovery copy is authorized. M9 permits new
least-privilege production identities but not disclosure or reuse of existing
secrets. Failure to verify the release manifest, production and LXC 116
checkpoints, exact network tuples, isolated restore, rollback or materially
adequate capacity is a stop condition for provisioning or cutover.

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

Current resume point: M0 through M3 and M5 through M7 are complete; M4 and M8
are active. The canonical service, News route, Home Assistant pilot, monitoring,
backup/isolated recovery, NetBox services, human wiki and derived mirror are
live and verified. Companion still uses the retained 9130 path, so M4 and final two-pass
cross-surface graduation remain before the legacy renderer can be retired.
A pinned Kokoro GGML/Vulkan renderer and authenticated network bridge are staged
but stopped in GPU LXC 110. The end-to-end short response was about 0.71–0.90
seconds without active generation and 2.94 seconds during a bounded Llama
request. M3 now requires GPU workload isolation or an explicit target change;
production must not select this shared, uncoordinated renderer.
The otherwise-idle TrueNAS Arc A380 is now the preferred isolated renderer
candidate: its loopback canary met the short-response target and remained stable
during concurrent Jellyfin VAAPI encoding. An authenticated network and
rollback gate still precede any production selection.

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
- [x] **M3 — Staged LXC 116 deployment.** Verify backup/checkpoint; install
  pinned candidate beside the accepted service; run private canary and measured
  load; atomically select it only after gates pass. Gate: two independent
  authenticated synthesis passes, rollback rehearsal and current path health.
- [ ] **M4 — Companion migration.** Update web and native clients for
  sentence-streamed playback, explicit audio capture constraints, cancellation
  and useful failure states. Gate: automated regressions plus Jason's phone/Mac
  listening and responsiveness acceptance; typed interaction unaffected.
- [x] **M5 — News migration.** Route the briefing through the canonical service
  without allowing batch work to starve interactive traffic; preserve chapters,
  pauses, schedule and rollback renderer. Gate: same approved voice/policy,
  valid artifact, simultaneous-interaction load test and schedule recovery.
- [x] **M6 — Home Assistant integration.** Snapshot VM 103, add the selected
  native Wyoming/local adapter and exact private network/auth path, without
  changing entity exposure or device authority. Gate: normal/refused commands,
  interruption, dependency failure and rollback on one pilot surface.
- [x] **M7 — STT and capture quality.** Compare current `base.en` against a
  bounded shortlist using real-consent listening tests and synthetic fixtures;
  add domain hints/VAD/capture controls only with measured benefit. Gate:
  accuracy and p95 response target, far-field/noise cases, no content retention.
- [ ] **M8 — Operations, recovery and graduation.** Close all integrations,
  restore the complete service in isolation, run failure/degradation tests,
  reconcile Beszel/NetBox/wiki/mirror/runbooks and complete user handover and
  efficiency review. Gate: two independent end-to-end production passes from
  each surface, accepted latency/voice identity and no unexplained legacy path.
- [ ] **M9 — V1 production graduation and V2 lab baseline.** Prerequisite:
  complete M4 and M8, reconcile all source/live state, and freeze a reproducible
  V1 manifest. Provision a new unprivileged production guest on the Servers
  VLAN from that release, with a stable private DNS name and separate
  credentials, monitoring, backups and systems-of-record records. Migrate Home
  Assistant, Companion, News and other production consumers one at a time while
  `.70.14` remains healthy. Gate: matching code/dependency/model/voice/policy
  digests, cross-environment access denial, isolated restore, exercised
  consumer-first rollback, two passes per surface and seven days of healthy
  production soak. After acceptance, sanitize and retain LXC 116 as the
  immutable V1 lab baseline; reserve a distinct lab guest/clone for later V2
  work. A Git tag such as `aster-voice-v1.0.0` requires an immediate explicit
  remote-write approval when the manifest is ready.

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

Jason accepted pronunciation comparison option 5 on the original ONNX path,
which temporarily mapped `Home Assistant` to “Home uh-sist-unt” and both
`Lutron Caseta` and `Lutron Caséta` to “Loo-tron kuh-set-uh”. The later pinned
Kokopop CPU-path comparison showed both ordinary spellings sound correct; the
phonetic forms were what made them sound wrong inside the longer briefing.
Jason selected plain `Home Assistant` and plain `Lutron Caseta`. The current
policy therefore leaves `Home Assistant` unchanged and only canonicalizes the
accented spelling `Lutron Caséta` to `Lutron Caseta`. Written UI text is still
untouched. This supersedes the earlier engine-specific respellings.

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
- Follow-up investigation corrected the scope of that blocker. The live
  llama.cpp service proves that Mesa Vulkan can use this B60 with the small BAR;
  only Intel's `xe` Level Zero/OpenCL compute-runtime path rejects it. Kokopop
  commit `2c6989ac800f624ea984210215e1b76be42eea81`, with its pinned patched GGML
  commit `36da57138425487184aa1da2eee2cde155909c6f`, was built in the isolated
  `/opt/aster-voice-vulkan-test` root in LXC 110 with Vulkan explicitly enabled.
  All 617 upstream tests passed.
- The immutable Kokoro F16 GGUF came from model revision
  `b7958cdedd0efa56e8756895e739fbe2852f635d`; its 176,165,568-byte file matched
  the published SHA-256
  `e8242a1321e580599c26981692adf088ebfdc4c7b7555959b13f4d6667d0d206` and
  contains the approved `bm_daniel` voice. Explicit synthesis identified the
  Intel Arc Pro B60/BMG G21 through the Intel open-source Mesa driver and
  produced valid mono 24 kHz/16-bit WAV output. No automatic CPU fallback was
  used for this pass.
- The persistent localhost-only canary delivered warm first audio for the short
  acknowledgement in 0.588 seconds, meeting the 0.750-second target. A
  representative longer first sentence delivered its first audio in 1.608
  seconds; an identical CPU-runtime comparison required about eight seconds
  for that first chunk. Vulkan is therefore useful but does not remove the need
  for Aster-owned bounded sentence/clause segmentation, acknowledgement caching
  and a contention/listening gate. The transient listeners were stopped and
  generated remote audio/traces were removed; the pinned build/model remain
  staged, stopped and isolated for the next pass. Production llama.cpp and
  speech services remained active and healthy.
- Staged a least-privilege network renderer without changing production. The
  Kokopop listener remains loopback-only on LXC 110; a separate stdlib bridge
  binds only `192.168.70.12:9132`, requires a dedicated file-backed bearer key,
  fixes `bm_daniel`, speed 0.95 and WAV output, and accepts at most 240 UTF-8
  characters with two concurrent requests. LXC 116's candidate is the only
  configured client. It validates mono 24 kHz/16-bit WAV before scheduling and
  caches only the exact approved acknowledgement. Both new units and the LXC
  116 candidate remain disabled.
- The authenticated LXC 116 to LXC 110 compatibility path returned a valid
  373,964-byte WAV in 2.460 seconds for the normalization fixture containing
  Home Assistant, Lutron Caseta, CA$1,234 and B.C. Authless candidate and bridge
  calls returned 401. Focused renderer/scheduler tests passed, including fixed
  voice/options, malformed WAV and oversized/refused input.
- Dependency health was made fail-closed. With the renderer bridge running,
  candidate health returned HTTP 200; stopping only that candidate bridge made
  health return HTTP 503 with `status=unavailable`; restarting it restored 200.
  Production speech stayed healthy throughout.
- Warm uncached short-response measurements through the full candidate path
  were 0.714, 0.810 and 0.896 seconds, close to but not a p95 pass against the
  0.750-second target. During a simultaneous bounded 128-token Llama request,
  the same speech path took 2.940 seconds and Llama completed in 44.741 seconds.
  Shared B60 Vulkan execution without coordination therefore fails the
  interactive latency gate. Production selection remains withheld; the next
  safe design action is workload isolation (prefer the otherwise-idle second
  GPU if compatible) or a measured GPU-aware preemption/priority mechanism,
  followed by the frozen load suite. All candidate services were returned to
  stopped/disabled; production Llama and speech remained active and healthy.
- The second-GPU follow-up found TrueNAS's Intel Arc A380 on `i915`, with an
  8 GiB mapped BAR and `/dev/dri/renderD128`. Its physical link currently
  negotiates only PCIe Gen1 x1, but the persistent 168 MiB model avoids a large
  per-request transfer. Vulkan initialization passed in the existing Jellyfin
  container, and a short idle sample showed no active GPU clients.
- A loopback-only, resource-bounded container reused the exact pinned Kokopop
  binary/model hashes and explicitly selected the A380 through Mesa Vulkan.
  The first cold render took 3.290 seconds; subsequent short renders took
  0.494–0.511 seconds and the longer Home Assistant/Lutron/British Columbia
  sentence took 1.431 seconds. With a sustained real-time Jellyfin HEVC VAAPI
  encode active, three short renders took 0.587, 0.491 and 0.493 seconds.
  This passes the provisional 0.750-second short-response target and indicates
  video encode and TTS can coexist on separate A380 engines, subject to the
  full scheduled-archiver and interactive-load gates.
- The requested non-Vulkan check was performed rather than assumed. Intel's
  pinned OpenVINO 2026.4 runtime enumerated both CPU and the A380 GPU once the
  container received the host render-group GID. ONNX Runtime OpenVINO 1.24.1,
  configured GPU-only with fallback disabled, then rejected the approved
  hash-pinned Kokoro FP16 graph at compile time because a subgraph rank is not
  static. No OpenVINO performance claim or CPU fallback is recorded. Changing
  or re-exporting the approved model would require a fresh identity/listening
  gate; the measured Vulkan path remains the selected A380 candidate.
- Added a TrueNAS custom-app definition with a source-pinned Vulkan build,
  read-only external model/key mounts, non-root containers, an internal-only
  renderer network, fixed voice/speed/backend, resource limits and only the
  authenticated bridge published on `192.168.20.40:9132`. Compose interpolation
  and syntax validate. A clean build produced renderer image
  `sha256:9bd62132580321de372827d83360150d62ad60ae6e862a1fd168a9d9075b46a3`.
  An isolated loopback run as UID/GID 10001 with only render GID 107 explicitly
  selected the A380 and produced valid mono 24 kHz/16-bit WAV. The first
  request took 4.648 seconds while the model and shader pipeline warmed; the
  next three identical acknowledgements took 0.631, 0.651 and 0.657 seconds.
  The renderer must therefore stay resident and pass a warm-up request before
  admission. No listener, firewall rule or production route has yet been
  enabled.
- Jason approved the narrow authenticated canary. OPNsense now permits only
  LXC 116 `192.168.70.14` to TrueNAS `192.168.20.40:9132/TCP` on Lab VLAN 70,
  sequence 2684, UUID `92fb4b0a-750f-4d10-b655-fdad43b6994b`, before the
  RFC1918 isolation block. The live `pf` rule was verified; LXC 110 remained
  blocked. The bridge rejected an unauthenticated LXC 116 request with 401 and
  returned a valid 119,084-byte WAV in 0.661 seconds with the protected key.
- The first deployed Compose canary exposed and corrected two definition bugs:
  a bridge attached only to an internal Docker network was not host-published,
  and its health command omitted `import urllib.request`. Kokopop remains only
  on the internal network; the authenticated bridge alone also joins a normal
  edge network and binds `192.168.20.40:9132`. Both containers are healthy.
  The disabled-by-default LXC 116 candidate was pointed at that bridge and
  returned healthy plus a valid 24 kHz WAV for the Home Assistant, Lutron
  Caseta, Canadian-currency and B.C. fixture in 2.496 seconds. Production port
  9130 and routing were not changed; listening acceptance remains required.
- The first bounded A380 contention gate intentionally used unique short
  acknowledgements so the exact-response cache could not hide renderer delay.
  Without Jellyfin load, twelve idle requests had 0.778-second median and
  1.040-second p95 complete-WAV latency. During four briefing-sized renders,
  twelve interactive requests rose to 1.597-second median and 3.239-second
  p95, then recovered to 0.857/0.875 seconds. Because this already failed, no
  additional Jellyfin load was imposed.
- A second probe used the candidate's actual two-worker scheduler with the
  briefing classified as `batch`. Priority reduced interactive median to
  0.896 seconds, but p95/max remained 2.658 seconds because an in-flight batch
  render cannot be pre-empted inside Kokopop. The six batch units completed at
  0.558, 1.837, 3.797, 6.019, 6.830 and 8.367 seconds. M3 remains unselected.
  The next implementation step is bounded batch-specific clause segmentation
  plus admission that stops submitting News work while interactive work is
  pending; repeat this gate before adding Jellyfin overlap. This is a software
  scheduling issue, not evidence for changing the provisional A380 choice.
- A 20-character batch cap plus one-at-a-time admission and 250 ms grace did
  meet the numeric contention target: 1.383-second p95 without Jellyfin and
  1.388 seconds during a real 35-second HEVC Main10 VAAPI transcode. Jason
  rejected the resulting News sample as too slow. Measurement confirmed a
  33.045-second artifact contained 10.859 seconds of silence, with 18 pauses of
  at least 300 ms. The experimental policy was rolled out of the boot-disabled
  candidate and will not be promoted or published as the solution.
- The revised architecture isolates workload rather than degrading speech.
  LXC 114 now has a separately staged CPU-only build of the same Kokopop commit
  `2c6989ac800f624ea984210215e1b76be42eea81` and pinned GGML revision; all 617
  upstream tests pass. Its GGUF matches the A380 asset SHA-256
  `e8242a1321e580599c26981692adf088ebfdc4c7b7555959b13f4d6667d0d206`.
  A whole natural briefing produced 20.25 seconds of valid mono 24 kHz audio in
  about 18.1 seconds, split internally into only two semantic chunks. During a
  separate extended CPU News render, twelve uncached A380 acknowledgements
  measured 0.878-second median and 0.928-second p95/max. Production News and
  speech services were unchanged. Jason accepted the corrected natural CPU
  sample with plain device names as the target News voice.
- Context comparison confirmed the new renderer pronounces plain `Home
  Assistant` and `Lutron Caseta` correctly. The old phonetic substitutions made
  both names sound wrong in the longer briefing even though short comparison
  clips had previously favoured them on the old path. Jason selected the plain
  forms; 18 focused tests pass and the boot-disabled LXC 116 candidate now uses
  that policy. A corrected full natural CPU briefing was generated for the
  final context listening gate; production remains unchanged.
- The accepted CPU path is now staged behind the one candidate API. LXC 114
  runs boot-disabled `aster-kokopop-news` and an authenticated fixed-policy
  bridge; LXC 116 has a distinct News caller identity and a dedicated third
  scheduler worker. The two A380 workers never consume the batch queue. The
  bridge returned 401 without its renderer credential and valid mono 24 kHz
  WAV with it. During a 26.467-second batch request, twelve uncached A380
  interactive replies completed in 0.802–0.851 seconds (0.851-second p95/max),
  and the batch stream completed successfully with 911,105 framed bytes.
  Production port 9130, the production News UI and both News timers remained
  unchanged; all new services remain boot-disabled.
- The default-off News client now validates and consumes the canonical framed
  batch stream using a dedicated file credential. Its `local` mode preserves
  the existing in-process Kokoro renderer as immediate rollback. Thirteen
  focused News normalization/client tests pass on LXC 114. A real 20-story
  canary completed without publishing to the production directory: valid MP3
  (1,404.288 seconds, 8,961,932 bytes), 20 strictly increasing chapter offsets,
  valid WebVTT and matching metadata. The current production artifact remained
  unchanged at 1,239.240 seconds/8,312,540 bytes. The client and service
  environment are installed with explicit `local` mode; scheduled cutover is
  withheld pending Jason's listening acceptance of the retrieved full canary.
- Listening found one defect in the full canary: possessive `B.C.'s` escaped
  the dotted-abbreviation rule and Kokopop spoke the dots as URL tokens. The
  shared and News normalizers now recognize possessive suffixes, producing
  `British Columbia's`; 22 focused tests pass. A complete opening/first-story
  replay through the authenticated batch route was accepted by Jason. Plain
  `Eby` remains unchanged—no unnecessary phonetic substitution was added.
- M5 is promoted. The LXC 114 CPU renderer and authenticated bridge plus the
  LXC 116 candidate API are boot-enabled; the News environment selects
  `ASTER_NEWS_TTS_MODE=aster`. A deliberate bridge outage produced the expected
  client failure without content leakage, followed by valid 24 kHz recovery.
  The timer-owned service then digested 18 live clusters and published a real
  15-story canonical briefing in 25m16s end to end (23m21s audio phase): valid
  974.712-second MP3, 6,269,780 bytes, 15 chapter starts, valid JSON/WebVTT and
  HTTP 200 with matching size. Production speech 9130, candidate health, News
  UI, timer and all three boot dependencies are healthy. The retained `local`
  mode and protected pre-change files remain the immediate News rollback.

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

For a full-guest rehearsal, remove the restored NIC and disable on-boot before
first start. Use a protected restore-only environment to bind HTTP/Wyoming to
loopback, select the local ONNX renderer and clear the external batch renderer.
Never start a restored guest with its original static IP. Validate the approved
health identity, a fixed non-retained WAV/STT round trip and critical file
hashes, then destroy only the explicitly temporary VMID.

Rollback order: stop new consumer routing; select the retained Piper service or
application-local News renderer; restore only the changed client/config; remove
only the exact new firewall/service rule if it is no longer used; verify typed,
manual and pre-project speech paths. Do not restore a whole firewall or VM over
later unrelated changes.

## Documentation and systems-of-record integration

- [x] **HomeLab Doctor** — model/policy-aware health, dependency behavior,
  bounded content-free synthesis and LXC 116 backup/mirror age behavior are
  deployed or exercised with explicit success and failure tests.
- [x] **Monitoring/alerting** — latency/queue/error/resource signals are live,
  Beszel owns guest resources, and a label-preserving Grafana bridge to the
  established email policy passed a synthetic firing/resolution test.
- [x] **Backup and recovery** — the corrected runtime, voice assets, policy and
  protected configuration are covered by byte-identical Proxmox/TrueNAS
  archives; a network-isolated restore passed health, local TTS and STT.
- [x] **NetBox** — LXC 116 retains VM/interface/IP IDs 16/16/30 and now records
  canonical, legacy and Wyoming TCP services plus the exact HA consumer boundary.
- [x] **Human wiki** — the reviewed Aster Voice Service page covers operation,
  consumers, privacy, recovery and troubleshooting.
- [x] **Aster mirror/snapshot** — accepted source `aster-voice-service` produced a
  provenance-labelled pipeline-1.5.0 mirror with 1,810 verified entries and
  content hash `7bd9e61fd4d522f38d80f7e82157cfd8dae8189a31c066c1fe70f793767e3a24`.
  The twice-identical 1,839-source snapshot hashes to
  `94f87e3879a4bf749e299e8676de758191e2e04743cefdb2bfae4b6f34e5ea37`
  and is active with the prior directory retained.
- [x] **Operational reference and runbooks** — canonical/legacy roles, canary,
  rollback, recovery and caller diagnosis match the deployed service.
- [x] **Repository documentation** — architecture, project portfolio,
  changelog and implementation README link the canonical voice standard.
- [x] **Diagrams/rack records** — the logical architecture now records the
  canonical, Wyoming and isolated renderer flow; no physical rack change.
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
| 2026-10-12 | M9 V1 release-manifest preflight | Created `Aster-Voice-V1-Release-Manifest.json` from Forgejo `a064dfe` and content-only live LXC 116 inspection. It binds the accepted voice/model assets and twelve deployed runtime/dependency/unit hashes without containing credentials. The audit found that several accepted deployed candidate files are not yet present on this Stream A branch, and the repaired native Mac app has not been independently observed using v2 streaming. | Manifest is deliberately `draft-blocked`; no production guest, address, credential, consumer cutover or tag is authorized. Next reconcile the hashed runtime into Forgejo, verify native endpoint use, then complete M8 two-pass evidence before producing the immutable manifest. |
| 2026-10-12 | M4 browser streaming recovery and listening acceptance | Jason reported the old voice despite cache-busted URLs. Proxy evidence proved three `/voice/v1/tts` calls; public source inspection then showed that a later LXC 104 source deployment had overwritten both the streaming hunk and canonical root after their earlier verified deployment. Preserved current live drift, restored only the reviewed streaming delta, checkpointed it as `aster_agent.py.pre-stream-restore-20261012T1830`, then reran the idempotent root retirement with backup `aster_agent.py.pre-root-20261013T012603Z`. Compile, restart and public source checks passed. Jason reported the restored voice “worked and sounds great”; proxy evidence proves `/voice/v2/tts/stream` returned 1,116,174 bytes and the cancellation route independently returned 204. | Browser M4 listening, canonical endpoint and cancellation gates pass. Treat a return to the old voice as live-source drift first, not merely browser cache: inspect the rendered page and NPM endpoint log. The missing local `/Applications/AsterCompanion.app` is separate and remains blocked on matched Swift tooling/rebuild. |
| 2026-10-12 | M4 native Swift streaming candidate | Replaced complete-WAV `/voice/v1/tts` retrieval with authenticated `/voice/v2/tts/stream`, a bounded incremental AVS1 decoder, immediate semantic-unit WAV playback, unique request IDs and cancellation DELETE. Added split-frame, WAV construction and incomplete/invalid-stream tests. All changed Swift sources pass the compiler parse gate and repository whitespace checks. | Repository-only candidate. This Mac's Swift 6.3.3 compiler and 6.3.2 SDK are mismatched, so SwiftPM cannot build even the package manifest; do not install the app until the full Swift test suite passes on a matched toolchain. |
| 2026-10-12 | Aster canonical web name and inventory reconciliation | Removed the obsolete bearer-key root page and mounted the current passkey-authenticated Aster client at both `/` and the compatibility `/companion` path. LXC 104 has rollback copy `aster_agent.py.pre-root-20261012T205523Z`; compile, restart, public byte-equivalence and production in-process assertions passed, and the apex response contains no legacy API-key control. NetBox independently read back service ID 6, `Aster web and agent API`, TCP 9120 on the existing `hermesagent` VM/IP object with the canonical public URL recorded. | `https://aster.elliottrook.com/` is now the canonical Aster interface. `/companion` remains deliberately compatible so Authentik callbacks and installed shortcuts do not break. The network inventory change was applied in the repository-defined authoritative NetBox system. |
| 2026-10-12 | M4 browser streaming deployment | Dry-run helpers matched NPM host 18's exact legacy location and the single OPNsense NPM-to-9130 reference. OPNsense backup `config-aster-voice-stream-before-20261012-202425.xml` precedes exact rule `c69d946a-f769-4cdf-8bb8-29aa34ae4529` (`.50.23 -> .70.14:9131/TCP`); reload and live ruleset verification passed. NPM backup `aster-voice-stream-before-20261012-202440.sqlite` precedes the longer `/voice/v2/ -> 9131/v2/` location with buffering disabled; NPM's renderer, reload and `nginx -t` passed while `/voice/ -> 9130` remained unchanged. The focused source hunk dry-ran against live-only LXC 104 drift, then deployed behind `/opt/aster-agent/rollback-m4-browser-stream-20261012-2027`; compile, restart and health passed. All seven tests passed against the actually rendered live page. Public v2 denied unauthenticated input with 401, legacy health returned 200, and one source-local authenticated HTTPS canary returned AVS1 `audio,end`, 106,320 audio bytes in 0.595 seconds. | Machine gates pass for browser streaming without overwriting unrelated live 27B/runtime/UI state. Jason's real browser listening, stop/cancellation and responsiveness acceptance remains mandatory. Native Swift still uses complete-WAV v1 and is the next implementation slice. |
| 2026-10-12 | M4 browser streaming candidate | Live read-only reconciliation found `aster-agent.service` active on LXC 104 and the deployed browser still calling `/voice/v1/tts`; the live source SHA-256 differs from the current repository and was not overwritten. The repository candidate now incrementally validates bounded AVS1 frames, converts each mono 24 kHz PCM unit to a WAV for immediate browser playback, preserves autoplay/manual-play behavior, aborts later units and sends explicit request cancellation. Python syntax and seven focused browser voice tests pass. | Repository-only pass. No NPM route, LXC 104 source or production speech consumer changed. Next reconcile the source drift, add the exact authenticated `/voice/v2/` proxy to 9131, test denial/rollback, then deploy only the reviewed browser delta. Native Swift streaming remains separate M4 work. |
| 2026-10-12 | M9 scope and lifecycle approval | Jason directed implementation of the proposed production graduation and V2 lab-baseline design. The repository standard now defines one-way Lab-to-release-to-production promotion and reserves “mirror” for Forgejo/GitHub protection. | Stream A scope extended only for the recorded M9 systems and change classes. M4 and M8 remain hard prerequisites; next safe work is Companion/cross-surface reconciliation and release-manifest preparation, not production provisioning. |
| 2026-10-10 | M0 source discovery | Authoritative checkout, relevant voice history, service/client code, project standard, operations and Companion runbook inspected. Existing unrelated brand-design edits left untouched. | Canonical-vs-legacy mismatch and known client/service constraints recorded. |
| 2026-10-10 | M0 live discovery | Read-only Proxmox/LXC 116 inspection: unprivileged guest, 6 cores/4 GiB, one active Uvicorn worker, `base.en`, `lessac-high`; health/JWKS/OIDC/HTTPS probes pass. Secret value redacted and not retained. | Current service is healthy legacy state and the rollback baseline. |
| 2026-10-10 | Stream A decision | Jason rejected premium services and directed a network-level single solution using the approved voice, with project creation, commit, push and immediate Stream A start. | Risk envelope accepted; M0 complete, M1 starts with read-only design/licence/protocol discovery and offline benchmarks. |
| 2026-10-10 | M2 real-listener close-out | Loopback-only Uvicorn canary on LXC 116: cached first body 55 ms fresh/12 ms warm; uncached 1.772 s; disconnect recovery 12 ms; explicit DELETE 204 followed by one content-free `cancelled` frame and successful recovery. Temporary listener/staging removed; production remained active and healthy. | M2 functional/security/cancellation gates complete. M3 remains pending; uncached first-audio latency is a tracked acceptance risk. |
| 2026-10-10 | M3 staged canary and rollback | Fresh guest backup plus protected file checkpoint verified; pinned candidate installed separately on 9131; 46 tests, authentication refusal, two WAV passes, streaming, concurrency, cancellation and rollback passed. Cached acknowledgement 11 ms; uncached first body 1.521 s. | Candidate left stopped/disabled and production 9130 healthy. Do not select it until uncached latency meets 750 ms or Jason explicitly accepts a revised threshold. |
| 2026-10-10 | M3 Arc Pro B60 acceleration probe | Least-privilege render-node mapping; isolated OpenVINO 1.24.1 and hash-verified Intel compute runtime; provider-fallback detection; live PCI BAR/link inspection; complete test-root cleanup and live device withdrawal. | No OpenVINO GPU benchmark claimed: Intel's `xe` compute runtime rejected the 256 MiB physical BAR. Production stayed healthy. This result blocks Level Zero/OpenCL, not Mesa Vulkan. |
| 2026-10-10 | M3 B60 Vulkan Kokoro canary | Internet/upstream review plus live llama.cpp evidence identified Mesa Vulkan as the small-BAR path. Pinned Kokopop/GGML build; 617 tests; immutable verified F16 GGUF with `bm_daniel`; explicit B60 synthesis; persistent first-audio traces; CPU comparison; generated remote evidence cleanup. | Vulkan is viable without ReBAR. Warm short first audio was 0.588 s; a longer first sentence was 1.608 s. Keep the canary stopped and production unchanged pending Jason's listening parity, bounded segmentation and shared-GPU contention gates. |
| 2026-10-10 | M3 private Vulkan renderer bridge and contention gate | File-backed dedicated bearer key; fixed voice/speed/format; bounded input/concurrency; WAV validation; full authenticated LXC 116 path; 401 refusal; dependency 503/recovery; production isolation; simultaneous live Llama generation. | Functional/security gates pass, but latency does not: warm short end-to-end 0.714–0.896 s and 2.940 s under active Llama generation. Candidate units returned to stopped/disabled; production remained healthy. Do not select until GPU workload isolation or proven scheduling meets the frozen target. |
| 2026-10-10 | M3 TrueNAS A380 backend comparison and private canary | Live i915/device/BAR inspection; explicit Mesa Vulkan device selection; cold/warm and longer-sentence timings; sustained Jellyfin VAAPI overlap; Intel OpenVINO 2026.4 and ORT OpenVINO 1.24.1 with CPU fallback disabled; pinned non-root deployment-image build; loopback validation; exact OPNsense rule; authentication refusal/success; full LXC 116 candidate fixture. | A380 Vulkan passes: warm short 0.494–0.511 s and 0.491–0.587 s during VAAPI overlap; the clean deployment image warmed to 0.631–0.657 s after a 4.648 s cold request; authenticated network render was 0.661 s. OpenVINO rejects the approved dynamic-rank ONNX graph. Production remains unchanged; warm-up admission, full load and listening gates remain. |
| 2026-10-10 | M3 A380 interactive/News contention gate | Twelve unique idle acknowledgements; four briefing-sized renders with twelve interactive requests; recovery series; repeat through the deployed scheduler's real `batch` queue. Jellyfin overlap withheld after the earlier gate failed. | Direct overlap failed at 1.597 s median / 3.239 s p95. Scheduler priority improved median to 0.896 s but p95 remained 2.658 s because in-flight Kokopop work is not pre-emptible. Add batch-specific bounded clauses and interactive-aware admission, then repeat before selection. |
| 2026-10-10 | M3 rejected bounded-batch correction and isolated CPU News canary | Iterated 60/30/20-character GPU News caps; measured generated-sample silence; rolled rejected policy out of the candidate. Built identical pinned Kokopop/GGML CPU-only on LXC 114; 617 tests; identical GGUF hash; natural whole-briefing render; simultaneous isolated A380 probe. | The numeric 1.388 s contention pass was rejected because the sample contained 10.859 s silence and sounded slow. CPU News produced 20.25 s natural audio in ~18.1 s while A380 interaction held 0.878 s median / 0.928 s p95. Keep workloads isolated behind one fixed Aster identity, pending listening parity and batch-backend integration. |
| 2026-10-10 | M3 accepted voice and isolated batch-backend integration | Jason accepted the corrected full CPU News sample. Added a dedicated authenticated batch route and scheduler worker, boot-disabled LXC 114 CPU renderer/bridge, 401/200 boundary checks, and a real concurrent candidate request. | Batch completed in 26.467 s while twelve uncached A380 replies stayed between 0.802 and 0.851 s. One Aster identity is preserved without GPU contention. Production speech, News UI and timers remain unchanged; next gate is artifact equivalence and News-client rollback integration. |
| 2026-10-10 | M5 default-off News client and full artifact gate | Strict framed-stream client; distinct file credential; local rollback mode; 13 live tests; isolated real 20-story render; MP3/metadata/VTT/chapter validation; production artifact timestamp and services checked. | Full 23:24 canary and 20 chapters are valid; production stayed unchanged. Client is installed in explicit local mode with rollback copies. Await full-artifact listening acceptance before enabling the candidate dependencies or switching the schedule. |
| 2026-10-10 | M5 full-artifact listening correction | Isolated exact-context variants showed plain `Eby` was correct. Root cause was `B.C.'s` bypassing abbreviation expansion and being spoken as URL tokens. Added possessive abbreviation tests and regenerated the complete opening/first story through the canonical route. | Jason accepted the corrected opening. Promote the reversible News path, then run dependency and real-service gates. |
| 2026-10-10 | M5 canonical News promotion | Boot-enabled only the CPU renderer, authenticated bridge and candidate API; atomically selected `aster`; rehearsed bridge failure/recovery; ran the actual timer-owned digest service; validated published MP3, JSON, VTT, chapters, HTTP size, health and enablement. | Pass. Real run completed successfully in 25m16s and published 15 stories/16:14.712 audio. Local rendering remains a one-line rollback. M5 complete; proceed to the next consumer only after publishing this checkpoint. |
| 2026-10-10 | M6 Wyoming adapter and private path | Added Wyoming 1.10.2 adapter advertising only `aster-bm-daniel` TTS; six exact-runtime tests passed. Enabled candidate listener `192.168.70.14:10300`, restricted it to HA VM `192.168.20.11`, and confirmed non-HA peers receive `unauthorized`. OPNsense rule `5468fe48-c98c-4ce6-ac1f-eeb118583fcb` permits only `.20.11` to `.70.14:10300/TCP` at sequence 1975 before the Servers private-network block; protected backup `config-aster-wyoming-before-20261011-033501.xml` precedes it. Fresh snapshot-mode VM103 archive `vzdump-qemu-103-2026_10_10-20_35_35.vma.zst` completed successfully at 2.42 GiB. | Candidate 9131 and production 9130 remain healthy. Home Assistant configuration is unchanged; add the Wyoming integration and pilot pipeline only through the authenticated HA UI, then run normal/refused, interruption, dependency-failure and rollback gates before completing M6. |
| 2026-10-10 | M6 Home Assistant pilot and failure gates | Added the supported Wyoming integration as `aster-voice` and a separate, non-preferred `Aster Pilot` pipeline with Home Assistant conversation, no STT, British English and only the advertised approved household voice. HA's preview played the accepted pronunciation fixture; typed pilot conversation returned the time and refused the unexposed `front door` command. With no News digest active, stopping only the candidate produced HA's explicit `Error playing audio`; production 9130 stayed healthy, then candidate 9131/Wyoming 10300 recovered and the identical preview played. Long preview audio was stopped with the client audio control; closing the preview editor alone does not cancel already-buffered browser playback. The unchanged preferred `Home Assistant` pipeline answered after the test. | Pass for the isolated TTS pilot. No entity exposure, device authority, preferred pipeline or STT path changed. Rollback is immediate selection of the still-preferred original pipeline; removing the pilot/integration and exact firewall rule is the full cleanup. M6 complete; proceed to measured STT/capture work in M7 before assigning the pilot to a real voice satellite. |
| 2026-10-10 | M7 synthetic STT shortlist | Ran 24 samples per arm from eight versioned, locally generated Aster-voice fixtures; reports contain only fixture IDs/counts/timing. Untuned `base.en`: 50% exact, 22.4% WER, 0.783 s p95. VAD gave no benefit: 50%, 22.4%, 0.840 s. `small.en`: 62.5%, 20.7%, 2.325 s and failed the 1.5 s target. `distil-medium.en`: 50%, 19.0%, 5.769 s and failed. Correctly spaced household vocabulary on `base.en`: 75%, 15.5%, 0.814 s p95; six of eight fixture classes were exact on all iterations, with currency and `Jason's room` still unresolved. | Keep `base.en`; reject VAD and larger CPU models for the responsive path. Add reversible English/no-history/vocabulary candidate settings. Production and the HA pilot remain unchanged. M7 stays open for currency/room corrections plus consented near/far-field/noise capture tests. |
| 2026-10-10 | M7 tuned candidate deployment | Preserved exact pre-M7 candidate source/unit under `/opt/aster-voice-candidate/backups/m7-pre-stt-20261010`; installed Git-matching source and credential-free systemd policy; restarted only the idle candidate. Production 9130, candidate 9131, Wyoming 10300 and all News dependencies remained healthy. An authenticated synthetic Home Assistant fixture returned HTTP 200 with the expected non-empty schema in 0.87 s; response content was not printed and the temporary result was deleted. | Candidate-only pass. Rollback is the two preserved files plus candidate restart. No preferred HA pipeline or production STT changed; next add bounded Wyoming STT and run the isolated HA pilot before any real satellite assignment. |
| 2026-10-10 | M7 bounded Wyoming STT candidate | Added one advertised `aster-base-en` ASR model and the pinned Wyoming `Transcribe`/PCM/final-`Transcript` sequence. External VAD is required; input is mono 16-bit PCM at 8–48 kHz, capped at 15 MiB, with fixed model/language, strict event order, format consistency, serialized inference and content-free failures. Thirty-two focused speech/Wyoming tests pass against Wyoming 1.10.2 in LXC116, including unauthorized source, invalid sequence, format change, oversize and inference failure. | Repository candidate pass; not yet deployed. Preserve the current TTS-only listener, then stage the four files, run direct Wyoming synthetic transcription and only afterward add STT to the non-preferred HA pilot. |
| 2026-10-10 | M7 Wyoming STT deployment and HA discovery | Preserved the three prior runtime files under `/opt/aster-voice-candidate/backups/m7-pre-wyoming-stt-20261010`, installed Git-matching runtime files and restarted only the idle candidate. Production/candidate health and ports 9130/9131/10300 remained healthy. Reloading only HA's `aster-voice` integration caused the authorized `.20.11` client to discover `aster-stt`; it was saved on the still-non-preferred `Aster Pilot` with English STT and the existing British-English Aster TTS. | Discovery/configuration pass. Preferred `Home Assistant` remains unchanged. HAOS guest execution is available for an authorized-source synthetic Wyoming replay; complete that, failure/rollback and consented microphone tests before M7 graduation. |
| 2026-10-10 | M7 authorized Wyoming replay | Temporarily transferred the existing synthetic `ha-name` WAV and a content-free replay client into VM103/HA Core, then sent the pinned `Transcribe`, PCM and `AudioStop` sequence from the only authorized source. The candidate returned one final English `transcript` event with non-empty 53-character output in 0.824 s. Transcript content was never printed; all temporary HA Core, VM103 and Proxmox files were removed. Production and candidate health remained green. | End-to-end protocol and p95-target pass on synthetic audio. M7 remains open for a rollback/failure rehearsal and Jason's consented near/far-field/noise microphone cases, especially currency and `Jason's room`. |
| 2026-10-10 | M7 Wyoming STT rollback rehearsal | With News idle, preserved the current three-file runtime, restored the exact pre-STT files, restarted the candidate through its normal 10-second model warm-up and reloaded only HA's Wyoming integration. Restored the exact current runtime, restarted/reloaded again, and confirmed the integration returned to two entities. Candidate and production health passed throughout; the preferred assistant was not changed. | Rollback/recovery pass. Machine gates are complete. M7 now waits only for Jason's consented near-field, far-field and household-noise microphone acceptance, including the two unresolved synthetic classes. |
| 2026-10-11 | M7 browser-capture HTTPS repair | Repeated Safari capture attempts produced `[object Object]` before any Wyoming request reached Aster. Safari marked the existing HTTP page insecure and exposed no microphone permission. Added a checkpointed private NPM host with wildcard TLS/WebSockets, exact logged OPNsense permit `192.168.50.23 -> 192.168.20.11:80/TCP`, split DNS on OPNsense and both Pi-holes, and Home Assistant 2026.9's supported single-IP trusted-proxy setting. `https://homeassistant.elliottrook.com` returns 200 with certificate verification, direct HTTP recovery remains 200, and Safari now exposes Microphone permission as `Ask`. | Transport/browser gate passed. The new HTTPS origin requires one normal Home Assistant login before the consented currency/room microphone fixtures can be repeated. No microphone content was retained. Checkpoints exist on OPNsense, NPM and both Pi-holes. |
| 2026-10-11 | M7 first live HTTPS microphone and playback gate | The consented near-field Safari test reached Wyoming three times at 0.70--2.23 seconds. The successful household utterance was transcribed as `Turn on the kitchen lights and tell me the price is $1,234 Canadian dollars.`: currency formatting and `Canadian dollars` passed, while the final `in B.C.` was clipped or omitted. Home Assistant produced the expected unknown-entity response. Automatic reply audio initially failed even though the same Aster Wyoming voice played through HA's manual preview; Safari's site policy was `Stop Media with Sound`. After Jason approved changing only `homeassistant.elliottrook.com` to `Allow All Auto-Play`, a short spoken Assist turn played Aster's reply successfully. | Secure capture, STT, conversation, canonical TTS delivery and Safari automatic playback pass end to end. Record the Safari per-origin autoplay requirement in client setup. M7 remains open for a focused `B.C.`, `Jason's room`, far-field and household-noise acceptance set; do not treat the compound unknown-entity command as an entity-control acceptance test. |
| 2026-10-12 | M7 focused vocabulary and far-field acceptance | Consented Safari captures recognized `I live in BC.` and exactly recognized `Turn on the lights in Jason's room.`; Home Assistant matched the latter to the real area, turned on its lights and Aster spoke the confirmation. From approximately 2--3 metres, `What time is it?` was recognized exactly twice and Aster returned the time. Clear background programme speech was then captured as a new utterance during HA's automatic conversational follow-up window. The dialog was closed immediately after inspection. | `B.C.`, `Jason's room`, near-field, far-field and command-over-background-speech recognition pass; M7 is complete. One explicit client-behaviour limitation carries into M8: HA browser Assist continues listening after its reply and can treat intelligible background dialogue as another turn. Satellite/wake-word rollout must bound or disable that follow-up window; do not attribute it to a transcription mismatch. |
| 2026-10-12 | M8 model-aware HomeLab Doctor slice | Added explicit canonical health identity for `aster-bm-daniel`, Kokoro 1.0, policy v1 and `aster-base-en`; expanded the sanitized Doctor probe to require that exact identity and TCP reachability of the HA Wyoming listener while retaining legacy API, HTTPS, OIDC and JWKS checks. Five focused tests and exact-runtime compilation/tests passed. Deployed with checkpoint `/opt/aster-voice-candidate/backups/m8-pre-doctor-20261012`, restarted only the candidate, and observed its normal approximately 14-second model warm-up. The deployed probe returned all six statuses `ok`; production 9130, candidate 9131 and Wyoming 10300 remained available. The full HomeLab Doctor then emitted the strengthened Aster pass and independently confirmed the LXC 116 Proxmox archive and TrueNAS mirror were six hours old; its unrelated existing lab failures were left untouched. Live News ownership was reconciled to `news-aggregator-ui.service`, `news-aggregator-ingest.timer` and `news-aggregator-digest.timer`, all active/enabled as appropriate. | First M8 operations slice passes. The Doctor can no longer report green when the canonical voice identity or HA listener is wrong. A content-free bounded synthesis canary and tested backup-age failure behavior remain, followed by monitoring, isolated restore, systems-of-record reconciliation and two final passes per consumer surface. |
| 2026-10-12 | M8 bounded synthesis canary | Extended the same sanitized probe with a fixed `Aster health check.` request authenticated from the protected candidate environment. The canary has a five-second timeout, accepts only a 44-byte-plus RIFF/WAVE response capped at 2 MiB, discards audio immediately and reports only status/error class. Seven focused tests cover success, malformed audio, missing credential and prior failure cases; all passed both locally and in the pinned LXC runtime. Deployed without a service restart after preserving `/opt/aster-voice-candidate/backups/m8-pre-synthesis-canary-20261012-health_check.py`; the live probe returned all seven statuses `ok`. | Pass. Doctor now proves canonical synthesis rather than trusting health metadata alone. No user content, output audio or secret is logged or retained. Tested backup-age failure behavior is the remaining Doctor sub-item. |
| 2026-10-12 | M8 Doctor backup-age failure gate | Exercised the actual Proxmox and TrueNAS guest-age functions with synthetic fresh, stale, missing and future timestamps. Six focused backup tests pass alongside the existing six Doctor regression tests. Fresh six-hour LXC 116 archives pass; a 31-hour archive fails, a missing archive fails and a future timestamp warns without mutating live backups. | HomeLab Doctor M8 item complete. Its live run independently observed both LXC 116 copies at six hours old; monitoring/alerting is the next operations item. |
| 2026-10-12 | M8 application metrics and monitoring transport | Added dependency-free Prometheus counters, histograms and gauges for bounded caller/outcome classes, request and queue latency, queue depth, workers busy, cancellation and renderer failures. Sixteen scheduler/protocol/metrics tests passed in the pinned runtime. Deployed after checkpoint `/opt/aster-voice-candidate/backups/m8-pre-metrics-20261012`; health and synthesis remained green, the canary populated the metrics, and LXC 114 was refused with HTTP 403. OPNsense rule `f4355d1a-94f2-49ee-a6cf-da15159354bf` permits only `192.168.20.31 -> 192.168.70.14:9131/TCP`, protected by `config-aster-metrics-before-20261012-172358.xml`. Prometheus config/rules passed `promtool`; after correcting the reload-readability mismatch to `root:prometheus` mode 0640, the target reported `up=1` and all five service rules loaded. Beszel independently reports `Aster Speech LXC 116` at `192.168.70.14` as up; its agent is active/enabled, so host-resource telemetry remains there and is not duplicated. | Metrics transport and resource reconciliation pass. No request IDs, text, transcript, audio, device or user labels are exported. Prometheus evaluates service conditions, but its installation has no Alertmanager route; wire equivalent actionable rules into the existing Grafana email policy and test one firing/resolution before completing the monitoring item. |
| 2026-10-12 | M8 alert delivery and exporter credential rotation | Provisioned Grafana rule `homelab-aster-voice-service` to bridge firing `AsterVoice*` Prometheus conditions, with alert name/severity labels, into the existing HomeLab email policy. A temporary `AsterVoiceNotificationTest` reached Prometheus firing state and Grafana's local notifier with no notifier/SMTP errors; the rule was then removed, the five-rule production file passed `promtool`, the synthetic series disappeared and Grafana retained no active instance. The Proxmox exporter credential exposed during inspection was rotated with overlap: the first replacement failed only an over-specific validation string and automatically restored/revoked itself; the corrected replacement proved the Proxmox node up before the old token was revoked. Only `observability-m8` remains and both `proxmox` and `aster-voice` targets report `up=1`. | Monitoring/alerting item complete. Repeated renderer errors, p95 latency, persistent interactive queue/saturation and target loss are actionable; single cancellations remain signal-only. No service secret is recorded in Git or this evidence. |
| 2026-10-12 | M8 backup, isolated restore and recovery correction | Created a fresh running-guest snapshot, ran the established TrueNAS pull and proved both 4.04 GB copies identical. Restored it to temporary VMID 9116 with no network interface or boot enablement; critical service source, unit, model, voice and protected-environment hashes matched production. The isolated local-renderer start exposed deployment drift: Git's `KokoroRendererPool.healthy()` existed but the guest copy predated it, so local recovery rendered but `/health` raised. Added an explicit regression assertion, passed four tests locally and in the pinned runtime, checkpointed/deployed the Git copy to production and the restore, and returned both health endpoints to the exact approved identity. The isolated guest then produced a valid 97,290-byte 24 kHz WAV and non-empty STT result in 2.038 seconds without retaining audio/transcript. Production Doctor remained all green; VMID 9116 and staging were removed. A final post-fix snapshot `vzdump-lxc-116-2026_10_12-10_54_36.tar.zst` was mirrored and both copies hash to `3ddf410e47f872a7982f64629617fbcc27489b498d159b2b59ce43bd40fe2925`; direct archive extraction proves the corrected runtime matches live. | Backup/recovery item complete. The first isolated failure was fail-closed and production-safe, and it repaired a real fallback-health gap before graduation. The earlier pre-fix archive remains under normal retention rather than being deleted ad hoc. |
| 2026-10-12 | M8 NetBox, human wiki and derived mirror reconciliation | Verified live LXC 116 resources/MAC/IP/VLAN and VM103 `.20.11` plus observability `.20.31` independently. After a NetBox database checkpoint, idempotently recorded canonical 9131, legacy 9130 and Wyoming 10300 services; the Wyoming description names the exact HA consumer. Published `/wiki/services/aster-voice-service/` and enrolled it as reviewed local source `aster-voice-service`. The normal full refresh quarantined eight unrelated changing upstreams and published nothing; a bounded rerun preserved all 30 accepted inputs byte-for-byte and accepted only the reviewed source. Pipeline 1.5.0 double-built and verified 1,810 entries across 26 source directories, accepted-input `d5e5311fa84c7946bfe0f4cedbbe36657b1872c79450cc9228a3a30c62e6724a` and content `7bd9e61fd4d522f38d80f7e82157cfd8dae8189a31c066c1fe70f793767e3a24`. | NetBox, human wiki and derived-mirror items complete. Permission drift in the wiki upload and last-good paths was repaired to the intended service identities; parent write access used for the atomic mirror build was removed immediately afterward. |
| 2026-10-12 | M8 Aster snapshot activation | Built twice from HomeLab `a27da00`, reference `e411960` and mirror `7bd9e61f`; both 1,839-source archives matched SHA-256 `94f87e3879a4bf749e299e8676de758191e2e04743cefdb2bfae4b6f34e5ea37`. Staging proved exact provenance and 14 source-located voice entries. The first readiness probe incorrectly used loopback; it failed safely and automatically restored the prior directory. The corrected private-bind activation passed health and exact provenance with `root:aster` 0550/0440 modes. | Snapshot item complete. `/var/lib/aster/knowledge.pre-voice-20261012` retains the prior active generation; no inference, network, model or credential changed. |

## Close-out

Open. Final close-out will record the selected protocol/ports, release hashes,
consumer inventory, measured performance, restore/rollback evidence, accepted
limitations, maintenance owner and any deliberately deferred satellite work.
