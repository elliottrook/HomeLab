# EPUB Narration Compiler and New-Title Monitor

> Status: Complete — Stream A; HP Lab deployment accepted, BOSGAME unchanged
>
> Owner: Jason
>
> Proposed and started: 2026-10-26
>
> Authorization: **Stream A — Autonomous**, explicitly granted by Jason for
> this subproject on 2026-10-26
>
> `service_id`: `epub-narration-compiler`
>
> Service release: `V1`
>
> Current environment: Lab; compiler/monitor and HP direct-launch beta deployed
>
> Target environment: Accepted HP Lab workflow backed by TrueNAS; any BOSGAME
> promotion is a separate optional project
>
> Build/model reference: repository commit pending; Kokoro ONNX
> `kokoro-v1.0.fp16.onnx`, SHA-256
> `f3a290d384fbb27966d462905c71a46cef9e5fd00516b40df32a0b4afe77ac96`
>
> Configuration revision: `epub-narration-v1-hp-lab-2026-10-26`
>
> Rollback reference: LXC snapshot `epub-narration-m3-pre-20261026`, exact-file
> compiler checkpoints and HP absent-state checkpoint

## Purpose and desired outcome

Build a private, resumable narration compiler that detects new or changed
DRM-free EPUB titles in the existing Calibre library, produces chapter audio in
Aster's canonical voice with honest timing metadata, validates every artifact,
and atomically exposes only complete generations to Aster Books.

The normal path is pre-generated narration. Live narration is a later,
separately gated missing-chapter fallback and is not the primary pipeline.

Success means a newly added or changed eligible EPUB enters a durable queue,
is processed by one low-priority worker without changing Calibre, and becomes
visible only after all chapter audio, timing, metadata, hashes and the immutable
generation manifest pass. An interrupted or failed replacement leaves the
last-known-good generation visible.

## Current state and evidence

- Calibre's live library is `/mnt/Media/media/books` on TrueNAS. Its
  `metadata.db` is the metadata authority. On 2026-10-26 the database was
  1,155,072 bytes, owned by `apps:apps`, and a URI-mode read-only query found
  **505** book records.
- The same sanitized query found 167 EPUB, 14 AZW3, 14 KFX, 325 KFX-ZIP and 151
  MOBI format rows. The filesystem contained 167 EPUB files totalling
  300,562,467 bytes (55,526 to 40,484,490 bytes each). Titles and text were not
  emitted.
- The earlier documented inventory of 723 books was accurate when observed on
  2026-09-05, but it is not the current count. Calibre remains authoritative;
  neither figure is silently substituted for the other.
- `calibre-web-automated` was running and healthy on 2026-10-26. It mounts the
  Calibre library read-write as the established application writer. This
  compiler must mount the same library read-only and must never compete as a
  writer.
- Pool `Media` reported 9.45 TiB used and 14.6 TiB available. No
  `AsterReader` dataset, quota or production compiler was created during M0.
- Aster Speech LXC 116 remains a six-core, 4 GiB, VLAN 70 transitional guest.
  `aster-speech.service` and `aster-voice-candidate.service` were active.
- The installed canonical model is 163,527,961 bytes at the hash recorded in
  the header. Installed `kokoro-onnx` 0.6.1 exposes `create_timed()` and returns
  waveform, sample rate and native timing entries. No model download or
  replacement is justified.
- The canonical contract is Kokoro ONNX `kokoro-v1.0.fp16.onnx`, voice
  `bm_daniel`, language `en-gb`, speed `0.95`, with the established News Digest
  cleanup and sentence/clause cadence.
- AsterTV v2 already contains a deterministic synthetic EPUB reader proof and
  strict timing gates. Its ASR word-timing trial matched all 161 words but
  rejected one zero-length span as `alignment-time-order`. Its native Kokoro
  timing trial also failed closed as `phoneme-alignment-time-order`. These are
  negative evidence: they do not authorize interpolation, inferred word spans
  or a weaker gate.
- Sentence highlighting is therefore the V1 timing level. Each sentence cue is
  bound to its separately rendered PCM sample range and validated encoded
  chapter offset. Word highlighting remains disabled unless a later exact
  method passes the existing strict contract.
- The private 20-book quantile benchmark completed successfully. Its 0.8898
  hours of encoded audio occupied 17.635 MiB at a measured 46.181 kbit/s. Mean,
  median and worst-sample render factors were 0.9672, 0.9633 and 1.0644 times
  audio duration. The report is SHA-256 `7692ef8d…88979b`; all reported audio
  and timing hashes, Opus format/duration checks and timing bounds passed.
- Quantile integration projects about **1,976.5 narrated hours** and **38.25
  GiB** of Opus for the 166 currently accepted EPUBs. This is a planning
  estimate, not an inventory promise. M3 should begin with a **128 GiB quota**,
  no reservation and a 75% warning threshold. That is about 3.3 times the
  estimated ready corpus, leaving room for an old ready generation, its
  replacement, bounded work data, timing/state and estimation error.
- At the measured mean render factor, the current accepted backlog represents
  about 1,912 worker-hours: roughly 80 days continuously or 239 days in an
  eight-hour daily window. M3 must therefore prove load/lease admission and
  pause behavior before scheduling the backlog; increasing concurrency is not
  implied by the benchmark.

## Scope and exclusions

### In scope and authorized change classes

- Read Calibre metadata and EPUB files through a read-only mount or read-only
  database/file descriptors.
- Create repository design, implementation, tests, service definitions and
  non-secret monitoring candidates.
- Create a separate, quota-bounded TrueNAS dataset/output hierarchy after the
  20-book benchmark and checkpoint gate.
- Deploy one low-priority, single-concurrency monitor/worker with durable
  `queued`, `extracting`, `narrating`, `aligning`, `ready` and `failed` states.
- Use the unchanged canonical Aster voice model and contract through a bounded
  batch path; stage changes incrementally with before/after health evidence.
- Publish private, validated results to an Aster Books-only generated-narration
  root; add monitoring, backup/recovery metadata and operating documentation.
- Add a later missing-chapter live fallback only after the pre-generation path
  graduates and only with the same source-hash lock, parser, voice and timing
  gates.

### Explicit exclusions

- No write to the live Calibre library, `metadata.db`, book directories or CWA
  ingest path; no generated sidecars inside that tree.
- No DRM bypass, decryption, KFX/KFX-ZIP handling, inferred access rights or
  conversion of an unsupported source merely to make it eligible.
- No publication, external sharing or public ingress for generated narration.
- No real book text, audio, timing, progress, title list or private manifest in
  Git, project logs, monitoring labels or Aster's knowledge mirror.
- No mixing with `/mnt/Media/media/audiobooks` or the purchased-audiobook
  library. If Audiobookshelf is considered later, generated works use a
  separate library and progress namespace.
- No production AsterTV change in this project phase and no weakening of its
  exactness gates. Aster Books integration requires its own bounded milestone,
  rollback bundle and regression proof.
- No new Kokoro/Whisper model, download, voice, language, speed or cloud TTS
  provider without evidence and an in-scope gate. Piper is not an automatic
  fallback.
- No unbounded queue, parallel synthesis, automatic deletion of the last ready
  generation or off-site backup of reproducible bulk audio by default.
- No remote Git write without Jason's fresh explicit confirmation immediately
  before that push.

## Authority model

| Fact or artifact | Authority | Compiler treatment |
|---|---|---|
| Owned book metadata and EPUB membership | Live Calibre `metadata.db` | Read-only; schema and source paths validated |
| EPUB bytes | File selected by the Calibre format row | Stable-stat plus SHA-256; copied to private bounded work area |
| Eligibility/legal decision | Jason plus file accessibility/format gates | DRM-free EPUB only; ambiguity fails closed |
| Voice identity | Local AI platform contract and project standard | Exact model hash, `bm_daniel`, `en-gb`, `0.95` |
| Speech cleanup/cadence | Versioned canonical News Digest contract | Pinned in every generation manifest |
| Queue and attempt state | Compiler state database | Durable, private, schema-versioned |
| Published generation | Immutable generation manifest and hashes | Visible only through an atomic ready pointer |
| Listening position | Aster Books private progress store | Never inferred from Calibre or mixed with Audiobookshelf |
| Infrastructure placement/IP/service facts | NetBox and live state | Reconciled only when deployed |
| Human operation and recovery | Wiki/runbook and this project | No private content included |

## Architecture and data flows

```text
Calibre metadata.db + EPUBs (authoritative, read-only mount)
                 |
          stable read + SHA-256
                 v
 private queue.db: queued -> extracting -> narrating -> aligning
                 |              |             |
                 |       bounded EPUB     canonical Kokoro
                 |       extraction       one low-priority worker
                 v
  /work/<attempt>/ (private, quota-bounded, never consumer-visible)
                 |
       hash/format/duration/timing validation
                 v
 /generations/<calibre-id>/<source-hash>/ (immutable)
                 |
        atomic ready-pointer replacement
                 v
 /ready/<calibre-id>.json -> Aster Books reader
```

Proposed dataset root: `/mnt/Media/AsterReader`, as a new child dataset rather
than a directory in the Calibre or audiobook datasets. M2 supports an initial
128 GiB quota, no reservation and a 75% warning threshold. M3 still owns the
final dataset name, recordsize and compression decision after a recoverable
checkpoint. The logical hierarchy is:

```text
state/queue.db
state/worker.json
work/<attempt-id>/
generations/<calibre-id>/<source-sha256>/manifest.json
generations/<calibre-id>/<source-sha256>/chapters/*.opus
generations/<calibre-id>/<source-sha256>/timing/*.json.zst
ready/<calibre-id>.json
failed/<attempt-id>.json
```

The monitor opens SQLite with `mode=ro`, enables `query_only`, and selects only
the fields needed to locate EPUB format rows. It never uses `immutable=1`
against the live changing database. A source is accepted only if its resolved
path remains beneath the read-only library root and its size, device, inode,
mtime and SHA-256 remain stable across the copy.

The EPUB extractor enforces member-count, uncompressed-byte and expansion-ratio
limits, rejects unsafe archive paths, reads the OPF spine in order, removes
non-content elements and produces private chapter text. The worker records no
text in routine logs.

Narration uses sentence/clause-sized canonical cleanup units. Each unit is
rendered independently. Sentence cue start/end values come from actual PCM
sample counts plus explicit inserted samples, then are reconciled against the
encoded Opus duration; no word timing or proportional distribution is
invented. A cue or chapter that is missing, overlapping, non-monotonic,
non-finite or outside encoded duration rejects the complete generation.

The provisional retained format is **48 kbit/s mono Opus**. The manifest pins
codec settings, ffmpeg build, parser and cleanup revisions, voice/model hash,
source hash, every output hash, measured duration and validation result.
Publication first renames a fully validated staging directory into its unique
immutable generation path, then atomically replaces the small ready pointer.
An existing ready pointer is retained until both operations succeed.

## Privacy and security design

- All source and output processing remains local. There is no Internet egress
  requirement and no public listener.
- The monitor identity receives read-only traversal of only the Calibre library
  and read-write access only to the AsterReader dataset. The rendering identity
  accepts bounded narration units and cannot administer Calibre or AsterTV.
- Queue/log metrics use counts, ages, opaque attempt IDs and error classes;
  titles, paths, text, audio, progress, source hashes and principal identifiers
  are excluded from metric labels and normal logs.
- State, staging, manifests and generated media are owner/service-readable, not
  world-readable. Temporary text is deleted after a successful generation and
  after a bounded failure-retention interval.
- EPUB archives are untrusted inputs. Parsing is offline, non-executable and
  constrained against path traversal, entity expansion and decompression bombs.
- Generated narration is private household material derived from lawfully
  accessible DRM-free sources. It is not published or shared.
- AI administration: not currently supported. The compiler has no admin API
  that justifies a credential. Human control is through the private host,
  systemd and documented rollback. Aster Books is a read-only consumer.

## Pre-start risk assessment and authorization envelope

Jason accepted this Stream A envelope in the 2026-10-26 delegation. It covers
the enumerated changes above, not adjacent media or AsterTV work.

| Risk | Likelihood / impact | Control and residual risk |
|---|---|---|
| Calibre corruption or writer conflict | Low / critical | Read-only mount, SQLite `mode=ro` + `query_only`, no CWA config change, denied-write test. Residual filesystem/admin misconfiguration stops deployment. |
| Changed source during scan | Medium / high | Stable-stat/hash/copy verification; retry to `queued`, never publish mixed bytes. |
| EPUB parser abuse or malformed structure | Medium / high | Offline strict ZIP/XML limits, safe paths, bounded extraction, fail closed. Some legitimate unusual EPUBs may fail and require review. |
| Inexact highlighting | High without gate / high | Sentence cues only from measured audio sample boundaries. Existing strict word gates remain unchanged. Residual limitation is coarser highlighting. |
| Voice/model drift | Medium / high | Exact hash and voice contract in manifest; preflight refuses mismatch. No automatic fallback. |
| Compute contention with interactive Aster | Medium / high | One low-priority worker, load/lease admission, bounded unit, pause/cancel behavior, 20-book throughput benchmark. Interactive speech wins. |
| Unbounded storage/workspace | Medium / high | Dataset quota after measurement, per-attempt cap, one worker, staging GC that cannot delete ready/LKG data. |
| Partial or corrupt publication | Medium / high | Immutable generations, per-file hashes, validation then atomic rename/pointer, consumer sees only `ready`. |
| Legal/privacy leakage | Low / high | DRM-free/local-household-only policy; no text/audio/timing/progress in Git or telemetry; no public route. Eligibility ambiguity fails closed. |
| Recovery loss | Medium / medium | Source EPUB remains authoritative; manifests/config/state protected; ZFS snapshots; LKG retention; isolated regeneration/restore proof. Reproducible audio is not initially off-site. |
| Inventory estimate drift | Observed / medium | Live 505/167 baseline replaces historical 723 for execution; preserve dated history; benchmark 20 representative eligible EPUBs before capacity decision. |
| Aster Books regression | Low now / high later | Production AsterTV excluded from current phase; future staged bundle, synthetic validation, checkpoint and immediate rollback required. |

No destructive or irreversible operation is required. Dataset creation,
service deployment and Aster Books publication are reversible. Removal of a
generation is never authorized when it is the only ready copy. No auth,
firewall, DNS, certificate or public-ingress change is expected. A new narrow
internal renderer capability or service identity, if required, must be scoped
and held in central secret custody without exposing its value.

Abort or pause on a Calibre write path, changed model hash, unexplained source
count collapse, unsafe EPUB member, failed checkpoint, timing inconsistency,
loss of interactive speech health, quota breach, inability to preserve LKG,
new DRM question, public exposure, or materially different deployment target.

## Persistence plan

- Queue schema version, compiler contract and generation state are durable in
  `state/queue.db`; process absence never means success.
- The six allowed states are `queued`, `extracting`, `narrating`, `aligning`,
  `ready` and `failed`. Only documented forward transitions are automatic.
- Every attempt has an opaque ID, source SHA-256 and finite retry count. Retry
  is explicit and idempotent for the same generation key.
- A lock permits one worker. Startup requeues only an interrupted non-ready
  attempt after recording its prior state and cleaning its uncommitted work.
- Ready generations are immutable. Replacement failure leaves the prior ready
  pointer untouched. Superseded generations receive a grace-period marker and
  are never deleted by the worker itself in V1.
- Resume sequence: reread `AGENTS.md`, the project standard and this document;
  inspect Git status; verify Calibre read-only access, dataset/checkpoint,
  queue schema, worker lock, voice hash and Aster health; then continue the
  current milestone from its first unchecked gate.

Current resume state (2026-10-26): M6 completed successfully. The private plan
remains at SHA-256
`08ee0f4b2d6935a806e7d1ec718d3477530fc14b755e719f1339e10ad6d51928` and the
private report is SHA-256
`7692ef8dc516024b4464d9fa3131de3fcf0f9ae7e7189931db9bb8e2bb88979b`.
Preserve the root-private M2 checkpoint; do not rerun or publish its real
content. M3/M4 deployed the 128 GiB `Media/AsterReader` dataset, Proxmox-hosted
least-privilege NFS mounts, unprivileged LXC 116 bind mounts, daily monitor and
static single-attempt worker. The monitor is active and idempotent; the worker
is intentionally inactive and the full backlog has not started. Daily 14-day
dataset snapshots and the protected configuration export now cover queue,
status, ready pointers and manifests while excluding generated audio/timing.
M5 then added an inactive HP Aster Books beta at
`/storage/.aster-staging/aster-books-compiler-beta1`. It has no production
entry, service, network access or shared progress. Its dedicated checkpoint is
`/storage/.aster-checkpoints/aster-books-compiler-beta1-20261026`; the active
Kodi process was not restarted. M6 added the separate HP-only direct-launch
bundle at `/storage/.aster-staging/aster-books-compiler-hp-beta1`, compiled one
private two-chapter pilot in an isolated queue, passed two final native
playback/progress runs and extended protected backup coverage for pilot
state/pointers/manifests. The full backlog and normal HP/BOSGAME routes remain
unchanged. Optional BOSGAME promotion and M7 fallback require separate scope.

## Milestones

- [x] **M0 — Read-only discovery and accepted envelope.** Read repository
  standards and relevant AsterTV/Calibre/voice records; verify sanitized live
  inventory, storage headroom and installed voice contract; record scope,
  exclusions, risks, rollback and stop conditions.
- [x] **M1 — Synthetic compiler foundation.** Implement read-only catalogue
  discovery, state machine, bounded synthetic EPUB extraction, immutable
  manifests and atomic publication. Pass local tests with no real content.
- [x] **M2 — Private 20-book benchmark.** Select a representative sample from
  the 167 eligible EPUBs by size/structure only; checkpoint; measure extraction,
  real-time factor, CPU/memory, Opus size, cue validity and failures. Keep all
  text/audio/timing private. Revise dataset capacity and schedule.
- [x] **M3 — Dataset and worker pilot.** Create the bounded TrueNAS dataset and
  least-privilege mounts; deploy one low-priority worker disabled by default;
  prove restart, interruption, quota, source-change and LKG behavior.
- [x] **M4 — Monitor and incremental reconciliation.** Enable the new/changed
  EPUB scan with missed-run recovery, finite retry, failure quarantine and
  useful non-secret status. Prove a synthetic new-title and changed-title run.
- [x] **M5 — Aster Books beta integration.** Consume only atomic ready pointers
  in a non-production or inactive staged bundle; keep sentence highlighting;
  validate playback, seek, chapter change, progress privacy and rollback. Do
  not modify production AsterTV without this gate and checkpoint.
- [x] **M6 — Recovery, integrations and HP Lab graduation.** Restore state/manifests
  and regenerate a sample in isolation; reconcile Doctor, monitoring, Beszel,
  NetBox, wiki/mirror, registry, runbook and user handover; run two independent
  HP production-shaped passes and the intent/efficiency review.
- [ ] **M7 — Optional live missing-chapter fallback.** Separate later decision;
  absent by default and unable to race the background generation key.

## Validation and evaluation

- Catalogue: open URI read-only, reject missing schema/format/path escape, and
  prove an attempted DB write fails.
- Detection: new source queues once; unchanged source is idempotent; changed
  bytes create a new generation while retaining the old ready pointer.
- EPUB: valid synthetic EPUB follows spine order; traversal, malformed XML,
  missing spine, excessive members/bytes/ratio and empty chapters fail closed.
- State: invalid transitions fail; restart recovers interrupted attempts;
  bounded retries terminate in `failed`; lock rejects a second worker.
- Voice: exact model hash/voice/language/speed/cleanup contract; sentence and
  clause units; canonical pronunciation regressions; no fallback drift.
- Timing: monotonic finite sentence cues derived from sample counts, chapter
  duration reconciliation and strict rejection of overlap/zero/out-of-range.
- Publication: incomplete or hash-mismatched staging is invisible; atomic
  pointer switch preserves LKG under injected failure.
- Codec: 48 kbit/s mono Opus, decoded duration and sample format verified; no
  retained WAV except bounded private diagnostic failure evidence.
- Performance: representative 20-book wall time, real-time factor, CPU/memory,
  thermal/load interaction, queue age and storage expansion; revise capacity.
- Privacy/security: no source content in Git/logs/metrics; owner modes; no
  egress; read-only mount and denied writes; no audiobook-tree path.
- Recovery: isolated queue/manifest restore and source-driven regeneration;
  source removal leaves already-ready material intact pending human decision.
- Regression: Calibre/CWA health, Aster interactive speech and production
  AsterTV remain unchanged through M0–M4; critical final path passes twice.

## Observability and maintenance

- HomeLab Doctor candidate checks: worker heartbeat, queue age/count by state,
  oldest queued age, failed count, last successful ready generation, free/quota
  headroom, manifest sampling and read-only source visibility. Output is
  non-secret and actionable.
- Metrics must avoid title, path, hash, text and progress labels. Failure codes
  are bounded enums such as `source-changed`, `unsupported-format`,
  `epub-invalid`, `voice-contract`, `timing-invalid`, `quota` and `publish`.
- The scheduled monitor uses a systemd timer with randomized delay, persistent
  missed-run behavior, single-instance lock and no overlap with the worker.
- Beszel: TrueNAS already has infrastructure coverage; before graduation,
  verify it remains reporting and document Doctor/service-native ownership of
  queue and manifest semantics rather than adding a duplicate agent.
- Updates to parser, cleanup, model, voice, encoder or manifest schema create a
  new compiler contract and queue a replacement; they never mutate an immutable
  generation in place.

## Backup, restore and rollback

- Existing Calibre/source protection remains authoritative and unchanged.
- Protect repository configuration, queue schema/state, ready pointers and
  immutable manifests through local snapshots and the normal configuration
  backup path. Keep secrets outside Git.
- Generated audio/timing is reproducible bulk data: retain ZFS snapshots and
  LKG locally; do not consume scarce encrypted off-site capacity until the
  benchmark and recovery review show a need.
- Before deployment, create and verify a recoverable dataset/config checkpoint.
  Restore into an isolated directory, never over the live dataset first.
- Rollback disables monitor/worker, removes Aster Books' generated-root pointer
  from the staged bundle, and selects the previous service artifact. It does not
  change Calibre or delete generations.

## Documentation and systems-of-record updates

- [x] **HomeLab Doctor** — added and failure-tested bounded mount, timer,
  status-age, queue and worker-resource checks; live full-suite regression is
  retained for M6 alongside the other infrastructure checks.
- [x] **Monitoring/alerting** — HomeLab Doctor owns non-secret mount,
  queue/worker/status and backup signals. LXC 116's existing active Beszel agent
  owns host-resource history; TrueNAS retains its existing native/Doctor
  coverage. No duplicate agent or alert was added.
- [x] **Backup and recovery** — daily 14-day dataset snapshots and protected
  state/status/ready/manifest export are live and verified. The current archive
  restored all 167 queue records into an isolated temporary database with a
  clean integrity check and no media; isolated synthetic regeneration also
  passed. No ready pointer/manifest exists yet because the real worker remains
  inactive.
- [x] **NetBox** — reconciled the offline compiler workload on the existing
  `aster-speech` VM and validated it through the read-only API. The canonical
  speech service already records batch synthesis. No fake port-bearing Service
  object was created because the compiler has no listener; no IP changed.
- [x] **Human wiki** — added normal operation, statuses, failure meaning,
  privacy boundaries and recovery in a focused local wiki commit; no remote
  synchronization was performed.
- [x] **Aster mirror/snapshot** — added an allowlisted sanitized operational
  reference with provenance; no title, text, timing, progress or source hash.
  Rebuilt the corpus with the accepted derived mirror, checkpointed the prior
  corpus, atomically deployed it and revalidated Aster health.
- [x] **Operational reference/runbook** — exact status, disable, checkpoint,
  restore, failure and LKG procedures are documented.
- [x] **Environment/release lifecycle** — registered as V1 Lab foundation with
  a production target and explicit promotion gates.
- [x] **Repository documentation** — project and portfolio entry created; M0
  evidence recorded.
- [x] **Diagrams/rack** — not applicable: no physical topology change.
- [x] **Homepage/service discovery** — not applicable. The compiler has no web
  UI/listener and the inactive Aster Books bundle has no normal entry point;
  adding a dead or privileged dashboard tile would be misleading.
- [x] **Authentication/authorization** — UID/GID 568 compiler identity, source
  read-only bind, output-only write path and execute-only renderer/model parent
  ACLs deployed; no application credential or shared human identity exists.
- [x] **DNS/certificates/firewall** — no change planned; stop if a new ingress
  path is proposed.
- [x] **Automation/schedules** — daily randomized persistent monitor timer,
  single-instance locks and atomic private status are deployed; worker has no
  enable target or recurring schedule.
- [x] **Security inventory** — owner-only state/status, read-only source,
  no public listener/credential, pinned model/cleanup hashes and bounded
  temporary work are recorded. The NFS exports are restricted to the trusted
  Proxmox host because unprivileged LXC cannot mount NFS directly.
- [x] **AI administration** — not currently supported; private human/systemd
  administration is safer than adding an admin API.

## Graduation criteria

- The 20-book benchmark replaces provisional capacity and throughput estimates.
- Every eligible new/changed EPUB deterministically reaches `ready` or a
  bounded actionable `failed`; unsupported/DRM-ambiguous formats fail closed.
- Calibre remains byte-for-byte outside the compiler's write authority.
- Every ready generation has verified source/output hashes, immutable manifest,
  canonical voice identity, valid Opus chapters and exact sentence cues.
- Interrupted replacements, restarts, quota exhaustion and dependency failure
  preserve the last-known-good result and are resumable.
- One worker cannot materially degrade interactive Aster; admission and pause
  behavior are measured, not assumed.
- Doctor/monitoring, recovery, NetBox/Beszel decisions, wiki/runbook, registry
  and user handover are complete and consistent.
- HP Lab Aster Books passes two independent playback/progress runs and retains
  an absent-state rollback without weakening AsterTV timing exactness.
- Post-deployment intent and efficiency review confirms useful narration,
  reasonable throughput/storage, minimal permissions and supportable operation.

## Evidence log

| Date | Action and evidence | Result / next safe action |
|---|---|---|
| 2026-10-26 | Jason explicitly authorized this bounded subproject as Stream A, including autonomous staged execution and the exclusions recorded above. | Authorization envelope accepted; remote Git writes still require fresh immediate approval. |
| 2026-10-26 | Read `AGENTS.md`, Project Creation Standard, Standards redirect, lifecycle standard, portfolio, registry, Calibre operations/recommender/unified-media records, Local AI voice contract, News canonical speech implementation and AsterTV v2 history. | M0 documentary prerequisites complete. |
| 2026-10-26 | Inspected AsterTV branch history without checkout. Strict Whisper and native Kokoro trials both failed closed on time ordering; sentence highlighting remained accepted. | Reuse exactness contract; do not infer word timing or modify production AsterTV. |
| 2026-10-26 | Sanitized TrueNAS read-only checks found 505 books, 167 EPUB records/files (300,562,467 bytes), healthy CWA and 14.6 TiB pool availability. Historical inventory was 723. No title/text was printed. | Benchmark 20 of the live 167 eligible EPUBs; no dataset reservation yet. |
| 2026-10-26 | Sanitized speech checks found both services active, Kokoro ONNX 0.6.1 `create_timed()`, and the unchanged 163,527,961-byte canonical model at the pinned hash. | No model download/replacement; continue with synthetic M1. |
| 2026-10-26 | Added repository-only compiler foundations for read-only Calibre EPUB discovery and stable hashing, bounded spine extraction, the six-state durable queue, exact PCM-sample sentence cues, immutable manifest validation and atomic ready-pointer publication. Fixtures contain only synthetic prose/media bytes. | Implementation remains disconnected from production and writes nowhere outside disposable test directories. |
| 2026-10-26 | Fourteen synthetic tests passed in normal and optimized Python. They cover missing/read-only catalogues, path escape, unsafe EPUB members, spine order/failure, idempotent and changed-source queueing, invalid transitions, bounded failure codes, sample-exact cues, manifest integrity, immutable generations and last-known-good preservation. Compile-only validation also passed with a sandbox-local bytecode cache. | M1 complete. Next safe action is a private, checkpointed 20-book benchmark harness; no dataset or runtime service has been created. |
| 2026-10-26 | M1 implementation/project evidence was committed locally as `4497558f`; the portfolio registration followed as `a7fdfd31`. A concurrent task had briefly advanced/amended the shared branch during staging, so path-scoped commits and immediate index checks were used; its unrelated work was preserved. | M1 has a focused durable checkpoint. Neither commit was pushed. |
| 2026-10-26 | Added and synthetically tested the private benchmark planner. It parsed/hashes sources on TrueNAS, selected deterministic word-count quantiles and wrote mode-0600 real samples under a mode-0700 root checkpoint. Sixteen tests pass in normal and optimized Python. | M2 preparation is reproducible without printing titles, paths or text. |
| 2026-10-26 | The live planner accepted 166/167 EPUBs and failed one closed at `epub-member-count`; the 20-book sample spans 2–419 chapters and 12–579,057 words. The bounded 500-word-per-book plan is 60,064 bytes at SHA-256 `08ee0f4b…d51928`. | Preserve the failure for later compatibility review; do not loosen the archive limit during the benchmark. |
| 2026-10-26 | Verified LXC 116 has 8.4 GiB root free, 3.7 GiB memory available, ffmpeg 7.1.5 with libopus, the pinned Kokoro model/voice pack and required Python libraries. Copied the plan, renderer and current canonical `digest_text.py` snapshot through root-private paths and verified end-to-end hashes/modes. | No model, package, service configuration or production consumer changed. |
| 2026-10-26 | Started transient benchmark invocation `a464d4a5f03644efb8785ff61847da6a` with one worker, nice 15, idle I/O, 300% CPU and 3 GiB memory limits. Initial memory was about 528 MiB; both existing speech services remained active. | M2 is running. Read the sanitized journal and source-local report; do not rerun silently on failure. |
| 2026-10-26 | The private 20-book run completed successfully. Source-local verification found 20/20 reported artifacts, zero audio/timing hash mismatches, zero Opus codec/channel/rate/duration mismatches, zero timing-order/bounds mismatches and owner-only modes. The plan hash matched, the report is `7692ef8d…88979b`, and service PIDs were unchanged across the run. | Private checkpoint retained. No source text, titles, paths, audio, timing data, progress or private identifiers entered Git. |
| 2026-10-26 | The sample produced 0.8898 audio hours and 17.635 MiB at 46.181 kbit/s. Mean/median/worst render factors were 0.9672/0.9633/1.0644. Quantile integration estimates 1,976.5 hours and 38.25 GiB for the 166 accepted EPUBs, or about 1,912 single-worker hours. | Use an initial 128 GiB quota with no reservation and a 75% warning; prove admission/pause behavior in M3 before starting the roughly 80-day continuous-equivalent backlog. |
| 2026-10-26 | Live unit checks retained the 300% CPU, 3 GiB memory, nice 15 and idle-I/O controls; maximum observed memory was 1,025,048,576 bytes. Both speech services remained active with valid PIDs. TrueNAS still reported 505 books and 167 EPUB rows through an immutable read-only query, and CWA remained running/healthy. | M2 regressions passed without a Calibre write, service restart, production consumer change or new dataset. |
| 2026-10-26 | Sixteen synthetic tests passed in normal and optimized Python after the benchmark; compile-only validation also passed with a sandbox-local bytecode cache. | M2 complete. Next safe milestone is the recoverable, disabled-by-default M3 dataset/worker pilot; the one archive-limit failure remains preserved for compatibility review. |
| 2026-10-26 | Created `Media/AsterReader` with a 128 GiB quota, no reservation, LZ4, 128K records, atime/exec off and 75%/90% warning properties. Preserved empty and populated checkpoints and enabled a daily 04:45 snapshot task with 14-day retention. | Capacity now reflects the measured 38.25 GiB estimate with about 3.3× headroom. No Calibre or audiobook dataset changed. |
| 2026-10-26 | The first in-guest NFS attempt failed closed under unprivileged-LXC mount restrictions. Retained the unprivileged guest and switched to standard Proxmox-host NFS mounts plus narrow `mp0` read-only and `mp1` read-write bind mounts. Source writes were denied; the compiler identity created and removed an owner-only output sentinel. Queue journalling was changed from WAL to SQLite's NFS-safe rollback journal. | Least privilege passed without privileged-container conversion or broader network access. Guest NFS packages were removed after validation; only the small ACL utility remains for execute-only renderer/model traversal. |
| 2026-10-26 | Deployed the daily persistent monitor and static one-attempt worker in LXC 116. Twenty-four synthetic tests passed there in normal and optimized Python, including NFS-safe queue journalling, restart/interruption, bounded retry, quota, changed source, LKG, unsafe EPUB, timing and publication gates. The optimized target pass also treated resource warnings as errors. Canonical model/voice/cleanup preflight passed. | M3 gate passed. Worker remains inactive with 3 GiB memory, 300% CPU, nice 15 and idle-I/O controls; no real generation was started. |
| 2026-10-26 | Two live monitor passes found 167 sources: the first queued 167 and the second queued zero. Queue/status files are mode 0600; output contains no ready or failed generation. CWA remained healthy with 505 books/167 EPUB rows and both speech services recovered active after the bounded guest restart. | M4 reconciliation is idempotent and active on its daily randomized timer. Full backlog remains intentionally paused. |
| 2026-10-26 | Added the compiler to the protected configuration exporter after an appdata checkpoint. A live export verified 20 application scopes and 23 SQLite databases; queue/status were present and compiler Opus/timing were absent. File Browser resumed unpaused. | Backup regime is live: full local dataset snapshots plus encrypted/off-site orchestration state and manifests. Isolated restore remains an M6 graduation gate. |
| 2026-10-26 | Added a content-silent HomeLab Doctor check with four failure-mode tests, the operational runbook and the deployed service-registry record. | M3/M4 documentation and observability complete; Beszel/wiki/mirror reconciliation and full recovery graduation remain M6 work. |
| 2026-10-26 | Recorded the offline compiler workload on NetBox's existing `aster-speech` VM and verified the updated object through `GET /api/virtualization/virtual-machines/16/`; the existing canonical speech service already declares batch synthesis. | NetBox reconciled without inventing a listener, port or new IP. Beszel/wiki/mirror and full recovery graduation remain M6 work. |
| 2026-10-26 | Full HomeLab Doctor regression passed the new compiler check with 167 queued, zero ready/failed and the worker inactive. Overall Doctor reported 84 passes, two warnings and four failures in unrelated existing Aster assurance/AI-PAM, surveillance freshness and subtitle automation checks; sandbox-denied local state-cache writes did not affect remote checks. | Compiler monitoring and backup checks passed. Unrelated Doctor findings were not changed under this project. |
| 2026-10-26 | Added a fail-closed Aster Books consumer for exact atomic ready pointers. It validates generation containment, manifest/file hashes, paired content/audio/timing chapter sets, normalized-text hashes, sentence source spans, PCM sample order, native Ogg/Opus format/duration and generation-bound private progress. The compiler now retains a private hash-bound normalized chapter document so sentence highlighting has an exact display source; configuration backup still excludes that content. | The consumer cannot inspect queue/work data or infer timing. Synthetic seek, chapter change, pause/save, resume, tamper and LKG rollback tests passed. |
| 2026-10-26 | Created a dedicated HP checkpoint and staged bundle manifest `76dd46c4…98bb4` at `/storage/.aster-staging/aster-books-compiler-beta1`. The first candidate failed closed before activation because LibreELEC lacks `ffprobe`; it is preserved under the checkpoint. A bounded native Ogg/Opus parser replaced that host dependency and verified two synthetic chapters. Bundle flags remain inactive, no production entry/network/shared progress exists, test progress was removed, Kodi retained PID 66637 with zero restarts, and BOSGAME production was untouched. | M5 passed without a menu/skin/service change. The bundle can be removed as one directory; its checkpoint records the absent pre-state. Production promotion remains outside this gate. |
| 2026-10-26 | Updated the installed inactive worker code after preserving the previous renderer at `/opt/epub-narration/rollback-m5-20261026`. The platform could not create another LXC snapshot, so deployment stopped before overwrite until that exact-file checkpoint and the retained M3 full snapshot were verified. Both speech services and the monitor stayed active; the worker remained static/inactive. | Future generations include the hash-bound content required by the beta without starting the real backlog. |
| 2026-10-26 | Ran isolated synthetic regeneration through catalogue reconciliation, queue state, worker publication and Aster Books ready-pointer loading in LXC 116. The one generated fixture reached ready and the restored SQLite integrity check passed; the temporary root was removed automatically. | M6 regeneration proof passed without real content or live queue mutation. Protected-archive restore verification is separate. |
| 2026-10-26 | Restored the compiler portion of the current protected 1.46 GB TrueNAS configuration archive into an isolated temporary directory source-locally. The queue database passed its archived hash, mode and SQLite integrity gates with 167 records. The archive contains no compiler media; ready-pointer and immutable-manifest counts are correctly zero because the real worker has not published a generation. | Protected-state restore gate passed. Local dataset snapshots remain the recovery path for generated media, and source-driven regeneration was proven separately. |
| 2026-10-26 | Added a private human-wiki operator page and a provenance-declared Aster operational reference. The wiki change is retained in local commit `20d9a86`; no remote was modified. Verified the existing LXC 116 Beszel agent remains active, so Doctor owns compiler semantics while Beszel continues host-resource history without a duplicate agent or alert. | Wiki and Beszel reconciliation complete. Build/validate the sanitized Aster snapshot and finish the production-path gate before graduation. |
| 2026-10-26 | Final M5/M6 regression passed 31 compiler/consumer/recovery tests in normal and optimized Python, 20 backup/Doctor tests, configuration coverage, compile-only validation and diff checks. Full HomeLab Doctor reported 85 passes and passed the compiler plus both backup checks; five warnings and ten failure lines were unrelated existing whole-lab findings, with zero EPUB/narration/backup failure lines. | The inactive beta and recovery integrations are regression-clean. Unrelated Doctor findings remain outside project scope. |
| 2026-10-26 | Rebuilt the Aster knowledge snapshot from the clean M5 commit plus a clean local clone of the committed reference repository and the accepted source-side derived mirror. The 1,841-source archive is `2e5a7562…bd5b1`; all provenance entries were clean and the EPUB operational reference was present. Checkpointed the prior LXC 104 corpus, validated the candidate before an atomic directory swap, restarted only `aster-agent.service`, and received healthy API status with PID 15982 and zero restarts. | Sanitized Aster publication passed without private book data or mirror loss. The retained prior directory and root-only checkpoint provide immediate rollback. |
| 2026-10-26 | Jason selected HP Lab Aster for the remaining reader deployment. Created an isolated one-item pilot queue from the previously accepted private benchmark set; the real compiler produced one two-chapter ready generation with verified hashes, owner-only modes and native Opus duration. The live 167-item queue remained queued and the static worker remained inactive. | Real-path compiler proof passed without starting the backlog or exposing book identity/content. |
| 2026-10-26 | Deployed the separate HP-only direct-launch bundle `7f770e8c…dcd8` after an absent-state checkpoint. Retained preflight results exposed and drove fixes for short-chapter end-callback replay, chapter-change settlement and private bytecode modes. Two final independent native passes then verified no autoplay, sentence highlighting, pause stability, chapter change, Back/save, reopen/resume, explicit cleanup and empty queues. | HP Lab beta accepted. Kodi retained PID 66637 with zero restarts; normal HP routes and BOSGAME were unchanged. |
| 2026-10-26 | Extended the protected exporter to cover the HP pilot queue, ready pointer, manifest and reconstruction marker while still excluding Opus, timing and content. A live 1.46 GB export verified 20 application scopes, 24 SQLite databases and zero pilot media/content files; an isolated restore verified both queue databases, 168 records, one pointer and one manifest. File Browser resumed healthy. Added immediate snapshot `Media/AsterReader@hp-beta1-accepted-20261026`. | Backup regime covers recovery-critical compiler and pilot state; generated bulk remains local/reproducible by design. |
| 2026-10-26 | Final regression passed 34 compiler/reader tests in normal and optimized Python, 12 backup/Doctor tests, compilation checks and two live HP passes. HomeLab Doctor passed the EPUB monitor and fresh configuration backup with 84 passes, two warnings and four unrelated existing failures. | M6 and the HP Lab objective are complete. No remote Git push was performed. |

## Post-deployment intent and efficiency review

- The monitor delivers the requested new/changed-title detection and is
  idempotent. The real backlog remains deliberately queued because measured
  single-worker completion is roughly 80 continuous days and no household
  benefit justifies silently beginning that load.
- The worker has one-attempt execution, one lock, low CPU/I/O priority, a 3 GiB
  memory ceiling and no schedule. The 128 GiB quota is about 3.3 times the
  measured ready-corpus estimate. No concurrency increase is justified.
- The active direct-launch HP beta proves exact ready-pointer consumption, sentence
  highlighting, seek, chapter change, private progress/resume, Opus duration
  and rollback boundaries without changing a production route.
- Permissions remain minimal: Calibre read-only, output-only writes, no
  listener/credential/public ingress. Configuration backup excludes
  source-derived content/audio/timing while local snapshots protect bulk data.
- Operational friction is intentional: the one-item HP pilot is available only
  by direct launch, and the 167-item worker backlog still requires a deliberate
  operator start. This prevents a multi-month workload or normal-menu change
  from beginning merely because the monitor found a backlog.
- The implementation is supportable through Doctor, Beszel host history, the
  runbook, human wiki, protected state restore and source-driven regeneration.
  BOSGAME promotion is no longer a graduation dependency; it remains an
  optional separately checkpointed project.

## Close-out

M0–M6 are complete and handed over in
[the HP Lab handover](../handovers/EPUB-Narration-Compiler-HP-Lab-Handover.md).
The compiler/monitor, backup regime, isolated real pilot, direct-launch HP
consumer and recovery paths are deployed. BOSGAME remains unchanged and is not
a completion dependency. Live missing-chapter fallback remains deliberately
deferred to optional M7.

## Documentation adequacy reflection

The repository now documents the Calibre authority, canonical voice, negative
AsterTV timing evidence, benchmark, deployed dataset/mount contract, compiler
identity, backup regime, HP direct-launch Aster Books beta, operator runbook,
wiki and Beszel ownership. It records two independent HP real-path passes and
does not imply a BOSGAME menu or production promotion.
