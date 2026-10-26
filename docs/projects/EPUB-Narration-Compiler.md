# EPUB Narration Compiler and New-Title Monitor

> Status: Active — Stream A; M0–M1 complete, private benchmark next
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
> Current environment: Lab; repository-only synthetic fixtures and tests
>
> Target environment: Production application/storage workflow on TrueNAS,
> consuming the stable Aster voice contract through a separately validated
> batch-render path
>
> Build/model reference: repository commit pending; Kokoro ONNX
> `kokoro-v1.0.fp16.onnx`, SHA-256
> `f3a290d384fbb27966d462905c71a46cef9e5fd00516b40df32a0b4afe77ac96`
>
> Configuration revision: `epub-narration-v1-draft-2026-10-26`
>
> Rollback reference: no production deployment yet; later milestones must keep
> the existing Aster Books release and the last ready generation independently
> usable

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
than a directory in the Calibre or audiobook datasets. The exact dataset name,
recordsize, compression, reservation and quota are decided after the benchmark.
The logical hierarchy is:

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

## Milestones

- [x] **M0 — Read-only discovery and accepted envelope.** Read repository
  standards and relevant AsterTV/Calibre/voice records; verify sanitized live
  inventory, storage headroom and installed voice contract; record scope,
  exclusions, risks, rollback and stop conditions.
- [x] **M1 — Synthetic compiler foundation.** Implement read-only catalogue
  discovery, state machine, bounded synthetic EPUB extraction, immutable
  manifests and atomic publication. Pass local tests with no real content.
- [ ] **M2 — Private 20-book benchmark.** Select a representative sample from
  the 167 eligible EPUBs by size/structure only; checkpoint; measure extraction,
  real-time factor, CPU/memory, Opus size, cue validity and failures. Keep all
  text/audio/timing private. Revise dataset capacity and schedule.
- [ ] **M3 — Dataset and worker pilot.** Create the bounded TrueNAS dataset and
  least-privilege mounts; deploy one low-priority worker disabled by default;
  prove restart, interruption, quota, source-change and LKG behavior.
- [ ] **M4 — Monitor and incremental reconciliation.** Enable the new/changed
  EPUB scan with missed-run recovery, finite retry, failure quarantine and
  useful non-secret status. Prove a synthetic new-title and changed-title run.
- [ ] **M5 — Aster Books beta integration.** Consume only atomic ready pointers
  in a non-production or inactive staged bundle; keep sentence highlighting;
  validate playback, seek, chapter change, progress privacy and rollback. Do
  not modify production AsterTV without this gate and checkpoint.
- [ ] **M6 — Recovery, integrations and graduation.** Restore state/manifests
  and regenerate a sample in isolation; reconcile Doctor, monitoring, Beszel,
  NetBox, wiki/mirror, registry, runbook and user handover; run two independent
  production-path passes and the intent/efficiency review.
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

- [ ] **HomeLab Doctor** — add and failure-test bounded workflow checks in M4/M6.
- [ ] **Monitoring/alerting** — add non-secret queue/worker/capacity signals;
  confirm existing TrueNAS Beszel coverage and no duplicate alerting.
- [ ] **Backup and recovery** — add state/manifest coverage, snapshot retention
  and isolated regeneration/restore evidence.
- [ ] **NetBox** — at deployment, register/reconcile the compiler service on
  existing TrueNAS and any narrow speech dependency; no new IP is expected.
- [ ] **Human wiki** — add normal operation, statuses, failure meaning, privacy
  boundaries and recovery after the pilot stabilizes.
- [ ] **Aster mirror/snapshot** — publish only a sanitized operational summary
  with provenance; no title, text, timing, progress or source hash.
- [ ] **Operational reference/runbook** — add exact status, retry, disable,
  checkpoint, restore and LKG procedures.
- [x] **Environment/release lifecycle** — registered as V1 Lab foundation with
  a production target and explicit promotion gates.
- [x] **Repository documentation** — project and portfolio entry created; M0
  evidence recorded.
- [x] **Diagrams/rack** — not applicable: no physical topology change.
- [ ] **Homepage/service discovery** — not expected; document not applicable if
  no human web UI is introduced.
- [ ] **Authentication/authorization** — define least-privilege service and
  renderer identities before deployment; no shared human/root credential.
- [x] **DNS/certificates/firewall** — no change planned; stop if a new ingress
  path is proposed.
- [ ] **Automation/schedules** — define systemd ownership, lock, missed-run and
  last-success behavior before enabling.
- [ ] **Security inventory** — record file ownership/modes, model hash, secret
  custody identifiers and temporary-data retention.
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
- Production Aster Books passes two independent playback/progress runs and a
  rollback without weakening AsterTV timing exactness.
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
| 2026-10-26 | The shared worktree advanced concurrently while the M1 files were staged; repository snapshot `d67fd678` contains the complete M1 project/code/test set as well as the other task's already-staged work. The unrelated work was not rewritten. | This scoped follow-up records the milestone and portfolio state; future project commits must recheck the shared index immediately before commit. |

## Close-out

Open. Final architecture, ownership, recovery references, accepted limitations
and deliberately deferred live fallback will be recorded after graduation.

## Documentation adequacy reflection

At M0 the repository documents Calibre authority, the canonical voice and the
negative AsterTV timing evidence well enough to design safely. It does not yet
contain a compiler runbook, deployed dataset contract, renderer service
identity, benchmark evidence or Aster Books handover. Those are explicit
milestone deliverables rather than assumed knowledge.
