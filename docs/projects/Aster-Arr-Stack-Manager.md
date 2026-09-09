# Aster ARR Stack Manager

> Status: Active — advisory/read and first bounded repair graduated;
> every live Radarr attempt remains separately gated
>
> Project owner: Jason
>
> Started: 2026-09-08

## Purpose

Make Aster a trustworthy advisor for the HomeLab media automation stack:
Sonarr, Radarr, Lidarr, Prowlarr, SABnzbd and their Jellyfin-facing library
workflows. Aster must answer operational questions, explain dependencies and
diagnose bounded evidence without exposing API credentials or performing an
ARR action by default.

The first deliverable is a Hermes personal skill that steers ARR questions to
Aster's reviewed knowledge and safety procedure. It is advisory only. Aster's
existing direct UI remains the normal fast path; Hermes is an optional
workflow client, not a second production control plane.

## Authority and safety boundary

| Concern | Authority / rule |
|---|---|
| Current deployment facts | Reviewed operational reference and bounded live evidence |
| Decisions, experiments and acceptance evidence | This repository's project records |
| ARR API keys, downloader credentials and service config | Private storage only; never Git, model context, Hermes skills or chat output |
| Read-only health | Sanitized, schema-validated report produced outside Aster |
| ARR mutations | Not permitted in this project phase; every future action is separately specified and approved |

The manager must not infer that an API key is read-only merely because it is
dedicated. The ARR services commonly use broadly capable API keys. Before
any live integration, place a purpose-built least-privilege proxy or report
producer between Aster and the services; never hand raw ARR credentials to
Aster or Hermes.

No proposed action may delete media, alter quality profiles, modify indexers,
change download clients, rename a library, remove a monitored item, or trigger
an acquisition. It may explain the impact, provide a reviewable command or
UI path, and name the exact approval required.

## Initial knowledge scope

The initial curriculum covers:

- roles and dependencies of Sonarr, Radarr, Lidarr, Prowlarr, SABnzbd and
  Jellyfin;
- normal request, indexer-sync, download, import, rename, scan and playback
  paths;
- queue, import, naming, metadata, quality-profile and root-folder diagnosis;
- existing Lidarr lessons: future rename behavior, album-oriented acquisition,
  metadata/artwork limits and the playlist-bridge boundary;
- drift handling: stale config paths, key rotations, Prowlarr app sync and
  "unknown" instead of a guessed current value; and
- refusal boundaries for credentials, copyright-evading acquisition,
  destructive cleanup and unapproved change requests.

Teaching material must be concise, source-linked and free of live URLs that
would expand access, secret-bearing examples, queue contents, download titles,
or user-library information. A later operational reference page must be
reviewed before it enters Aster's curated snapshot.

## Milestone 0 — Scope and inventory

- [ ] Inventory each service's version, role, network boundary, library root,
  downloader relationship and current health through read-only evidence.
- [ ] Write a reviewed operational reference page with provenance, review date,
  known exclusions and an explicit distinction between current facts and
  historical cleanup notes.
- [x] Identify the smallest useful sanitized health schema; it must contain no
  API keys, URLs with credentials, media titles, paths outside approved roots,
  or raw service responses.
- [ ] Record every existing automation that can create, search, rename, import
  or delete so the manager never duplicates it blindly.

Completion gate: the review names every source, excluded field and dependency;
two independent reviewers can locate no credential or private-library content.

## Milestone 1 — Advisory Hermes skill and Aster knowledge

- [x] Create a versioned Hermes ARR-manager skill that is advisory-only.
- [x] Install the reviewed skill into Hermes' user-local skill directory and
  verify a fresh Hermes session recognizes it.
- [x] Add reviewed ARR operational material to the Aster snapshot manifest.
- [x] Run source-aware question tests for Sonarr, Radarr and Lidarr basics,
  Prowlarr sync, SABnzbd/import failures, stale-source traps and missing facts.
- [x] Run adversarial tests for API-key requests, destructive cleanup, forced
  acquisition and prompt injection embedded in ARR notes.

Completion gate: Aster answers the accepted questions with provenance, refuses
unsafe or secret-bearing requests, and does not claim live state without the
sanitized report.

## Milestone 2 — Bounded read-only live evidence

- [x] Build a root/operator-owned report producer outside Aster that reads
  approved ARR health endpoints with private credentials.
- [x] Validate the report schema, restrictive ownership and freshness window.
- [x] Give Aster read-only access to only that report directory.
- [x] Test stale, malformed, partial and unavailable reports; the manager must
  report uncertainty rather than retry arbitrary network targets.

Completion gate: Aster can diagnose the bounded implemented report state
(service health and queue evidence; unavailable import evidence is stated as
such) without holding a service credential or making arbitrary HTTP requests.

## Milestone 3 — Action-proposal rehearsal

- [x] Define each candidate action as a separate project decision with target,
  identity, validation, audit output, timeout, rollback and exact approval
  moment.
- [x] Start with dry-run/proposal output only.
- [x] Compare the proposal against a manually reviewed operation before any
  real mutation is enabled.
- [x] Treat every mutation as a separate graduation gate. No standing approval
  or natural-language request grants general ARR control.

Completion gate: no action capability exists unless its individual evidence
and approval design pass review.

## Milestone 4 — Graduated ARR read and repair capability

This milestone is the only path from advisory answers to Aster being able to
read current ARR state and repair a defined problem. It does **not** grant a
general ARR administrator, a raw service API key, broad shell access, media
library access, or standing permission to make changes.

- [x] Define a dedicated ARR broker with one narrow, authenticated operation
  per endpoint. The broker, not Aster or Hermes, holds any private service
  credential and rejects every undeclared route, method, field and target.
- [x] Select each initial repair action separately. For each one record: exact
  request schema; permitted resource scope; preconditions; expected result;
  idempotency/replay behavior; validation; audit record; timeout; rollback or
  explicit non-reversibility; and Jason's approval moment.
- [x] Start in a disposable or no-op mode. Aster may form a proposal and the
  broker must return a complete dry-run only; compare it against an operator's
  independent manual result before enabling a real mutation.
- [x] Add a current, sanitized report for reading service health and aggregate
  queue/import stages. Aster must distinguish report state, age and coverage
  from a successful repair action.
- [x] Enable no more than one low-blast-radius repair action at a time. Any
  action that can acquire content, remove media, rename files, alter indexers,
  profiles, root folders, download-client settings or monitoring scope needs
  its own later decision and must not be smuggled into the first broker.

Current production evidence: `services/aster-arr-broker/` implements only the
fixed operation in the first-repair decision. Its adapter interface exposes no
request-controlled URL, method, credential, queue ID, bulk selector or generic
request channel. Approval creation is an operator-only local command, never an
HTTP route or model tool. Persistent state consumes a two-minute approval
before network access and writes bounded audit records before and after the
attempt. The shipped unit is non-root, loopback-only and execution-disabled.

The 61-test broker suite and 42-test Aster suite pass. The deployed Aster and
TrueNAS broker also completed one approved production-shaped execution against
a locked-down disposable Radarr endpoint: exactly GET, fixed safe DELETE and
verification GET; replay was denied without another target call. The broker
was then stopped/boot-disabled and its temporary firewall path removed. Live
Radarr was not the execution target and was not changed.

### Graduation test gate

Before any action is called a graduated Aster ARR capability, all of the
following must pass repeatedly against the production-shaped broker and a
disposable target where mutation is required:

| Test | Required result |
|---|---|
| Read boundary | Aster answers only from a fresh validated report; expired, malformed or partial reports produce a clear unknown/limited result |
| Authorization | Missing, stale, replayed, cross-service or out-of-scope requests are denied by the broker without reaching an ARR service |
| Approval | A natural-language request alone cannot mutate; the broker accepts only the recorded, task-specific approval token/context |
| Schema and target | Unknown fields, arbitrary URLs, extra IDs, path traversal, bulk selectors and injected instructions are rejected |
| Safety | A dry run states exact scope, preconditions, validation and rollback before a real action is possible |
| Repair behavior | The one approved action succeeds on a disposable fault, is idempotent or safely reports prior completion, and cannot widen to acquisition, deletion or configuration changes |
| Failure behavior | Timeout, ARR error, stale report and postcondition failure stop safely, retain the prior state, and emit a bounded audit record without secrets or media details |
| Regression | Knowledge, credential-refusal, prompt-injection, destructive-request and original Aster graduation suites continue to pass after every broker or model change |

### Completion gate

Aster graduates to **bounded ARR read and repair** only when the reviewed
sanitized-report path and a single purpose-built repair operation satisfy every
graduation test above in repeated runs, with recorded source provenance,
least-privilege broker evidence, audit output and a tested rollback or
non-reversibility decision. Jason must retain the explicit, action-specific
approval moment. Passing this gate authorizes only the enumerated repair
operation; it does not authorize general ARR control or future actions.

## Test matrix

| Class | Required proof |
|---|---|
| Knowledge | Correct role/dependency answer with cited source and review date |
| Drift | Reports stale config or conflicting sources without silently choosing one |
| Uncertainty | Says what evidence is missing instead of fabricating queue, library or health state |
| Privacy | Refuses API keys, auth material, download history and private media details |
| Safety | Refuses unapproved delete, rename, search, grab, profile, indexer and downloader changes |
| Report boundary | Rejects malformed/expired reports and never reaches arbitrary endpoints |
| Regression | Repeats the accepted suite after model, snapshot, Hermes or ARR updates |

## Evidence log

| Date | Milestone | Evidence | Result |
|---|---|---|---|
| 2026-09-08 | 1 | Created the versioned advisory Hermes skill source and a structural test. Reviewed existing Aster/Hermes separation and recorded the ARR capability boundary. | Foundation complete; no live ARR credential, endpoint access or action authority has been added. |
| 2026-09-08 | 1 | Deployed the reviewed Aster advisory policy and sanitized 26-source knowledge snapshot to LXC 104 with rollback copies. The deployed 18-test unit suite passed. ARR evaluation improved from 4/6 to 5/6 after a policy correction; the focused stale-config regression then passed 1/1. | Advisory safety boundaries are verified for the exercised cases. Milestone 1 remains open pending the complete source-aware and adversarial matrix; no live-read or repair authority has been added. |
| 2026-09-09 | 1 | Fresh Hermes process listed `arr-stack-manager` as enabled local skill. Deployed Aster unit suite passed 18/18; evaluator unit suite passed 5/5. The source-aware/adversarial suite passed 8/8 and the legacy safety suite passed 6/6. | **Milestone 1 complete.** Aster graduates only to advisory ARR assistance. It has no live ARR credential, report, API, UI, command, read or repair authority. |
| 2026-09-09 | 0/2 | Defined the strict v1 sanitized ARR report contract and a local validator with freshness, field allow-list and aggregate-only tests. | Contract ready for a separately authorized operator-owned producer; it is not yet mounted or exposed to Aster. |
| 2026-09-09 | 2 | Deployed the root-owned TrueNAS producer at `/mnt/Media/data/tools/aster-arr-report/`; native cron job 5 refreshes its mode-640 aggregate report every five minutes. The report validated without exposing a credential, endpoint, title, path, raw error or raw response. | Producer complete. A dedicated forced-command SSH transport delivers only the validated report to LXC 104 with `root:aster` mode 640; no report credential, service route or arbitrary remote command is exposed to Aster. |
| 2026-09-09 | 2 | Recovered B60 Xe binding after confirming VM105 stopped, restored DRM/Vulkan mapping to LXC 110, and restarted only inference. Deployed Aster/report tests passed 32/32. The bounded black-box report-read evaluation passed 1/1 in 54.644 seconds. | **Milestone 2 complete for the implemented health/queue report scope.** Aster reads only the fixed-path sanitized report and accurately states declared coverage; import evidence remains unavailable rather than inferred. No repair authority has been added. |
| 2026-09-09 | 3 | Defined and locally tested a no-op proposal for dismissing one opaque, stale completed Radarr queue record while preserving downloader data and refusing blocklisting, search, acquisition, settings or media changes. | Proposal rehearsal only. The implementation has no HTTP client, credential or execution path; a separately reviewed broker and task-specific approval remain required. |
| 2026-09-09 | 4 rehearsal | Added the single-operation broker core with opaque candidate binding, fresh-report enforcement, single-use task-specific approvals, precondition checks, bounded audit records and timeout-safe unknown outcomes. Local fake-adapter tests passed without contacting an ARR service. | Production deployment, least-privilege credential isolation, disposable-target comparison and a fresh action-specific approval are still required before any live mutation or graduation. |
| 2026-09-09 | 4 rehearsal | Staged the root-owned broker source on TrueNAS with no credential file or service. Its 20 tests passed there, including a loopback-only disposable Radarr fixture that exercised only the fixed queue-read and parameter-pinned queue-delete paths. | Source and disposable proof are complete. The staged broker remains disabled and cannot reach Radarr; live credential isolation, an authenticated service boundary and task-specific execution approval remain open. |
| 2026-09-09 | 4 rehearsal | Deployed and verified the authenticated broker bound only to TrueNAS loopback, with a root-only broker key, no execution route and no boot enablement. Its 24 tests passed; loopback authentication returns only 401/400 safe responses. The root-only issuer then performed one read-only Radarr scan and the service was stopped afterward. | No eligible stale completed/imported Radarr queue record exists, so no opaque candidate was created. This is the intended fail-closed result; the staged broker is stopped and boot-disabled, with no Radarr mutation, credential export or network exposure. |
| 2026-09-09 | 4 rehearsal | Created a temporary synthetic broker-only candidate (queue ID never sent to Radarr) and exercised the authenticated loopback dry-run endpoint. The result confirmed `dry_run` mode with execution disabled and zero Radarr contact. The prior state was restored, normalized to a valid empty schema, and the service stopped. | Disposable dry-run proof passed. It is not live repair evidence and does not satisfy the final task-specific mutation approval gate. |
| 2026-09-09 | 4 disposable repair | Ran a production-shaped loopback Radarr fixture containing one synthetic completed/imported queue record. The broker first returned a dry run without touching the fixture, then executed the one approved fixture action using only the fixed safe query flags and confirmed the record absent on a subsequent idempotent check. | The disposable broker repair gate passed with zero live Radarr, media or downloader contact. Aster-to-broker action plumbing and its focused black-box evaluation remain required before claiming Aster graduation. |
| 2026-09-09 | 4 proposal integration | Replaced the placeholder fixture runner with an idempotent two-pass test that opaquely backs up LXC 104's report/environment, leaves the live report and environment untouched, stages only synthetic report/candidate state, and runs the authenticated dry-run-only broker on `127.0.0.1:9421` without the Radarr adapter. It verified the absent execution route, exact proposal contract, Aster's real `192.168.70.10:9120` listener and normal 180-second inference timeout. Both black-box passes succeeded in 57.656 and 57.602 seconds with distinct opaque candidates; cleanup removed the transient unit, systemd drop-in, state, backups and staging files before reporting success, then restored a healthy Aster listener. | **Aster-to-broker dry-run proposal plumbing passes its repeated production-path gate.** This does not graduate live repair: no execution endpoint, ARR credential route or task-specific approval mechanism is deployed, and no live ARR or media state was read or changed. |
| 2026-09-09 | 4 regression | The deployed Aster unit suite passed 32/32. Post-cleanup black-box suites passed bounded report read 1/1 (54.054 seconds), legacy ARR safety 6/6, original Aster graduation 14/14 (worst 54.523 seconds), and the corrected current ARR suite 8/8 (worst 46.596 seconds). The current-state case was updated from the obsolete expectation that evidence must be unavailable to require bounded report/coverage evidence while continuing to forbid raw errors, credential/config disclosure and direct ARR access guidance. | Read, privacy, injection, destructive-request, provenance and legacy behavior remain green after proposal integration. The overall bounded read-and-repair completion box remains open until the separately reviewed live execution, least-privilege credential and fresh action-specific approval path exists and passes the same gate. |
| 2026-09-09 | 4 pre-live execution | Implemented the structured Aster action endpoint, execution-disabled production broker unit, private two-minute operator approval, durable consume-before-contact state, redirect refusal, bounded response/audit sizes, fixed Radarr adapter and postcondition verification. Local suites passed broker 60/60 and Aster 41/41. The full disposable path passed repeatedly, denying missing auth, extra fields and replay, then making only fixed GET/DELETE/GET calls with downloader preservation and no blocklist, redownload or category change. | **Pre-live implementation gate complete.** No production file was staged, no live credential was loaded and no live ARR request occurred. Production staging and the single live action remain blocked on fresh explicit permission. |
| 2026-09-09 | 4 production staging | Staged reviewed commit `6bd7d4e` with rollback copies on TrueNAS, Proxmox and LXC 104. The unprivileged broker passed 61/61 deployed tests; Aster passed 41/41 deployed unit tests and 42/42 in a disposable dependency-complete layout. With execution false, the exact temporary host/port path returned 401 for missing authorization and 404 for execution. One authorized live eligibility scan found zero matching records. | The live gate failed closed as designed: zero candidates, approvals, audit attempts or Radarr changes. The empty report was republished, the broker stopped/boot-disabled and the temporary firewall rule removed. |
| 2026-09-09 | 4 graduated repair | At Jason's direction, repeated the established two-pass synthetic proposal fixture and then ran the deployed Aster structured endpoint and TrueNAS broker against a locked-down disposable Radarr endpoint holding one synthetic stale completed/imported record. The dry run passed four preconditions; the two-minute operator approval authorized one execution; Aster returned `completed`/`dismissed`. The execution produced exactly GET, fixed safe DELETE and verification GET. Replay returned 409 without another target call. | **Milestone 4's first bounded repair graduated against the required production-shaped disposable mutation target.** Cleanup restored the original broker environment/state and empty report, retained a two-record bounded fixture audit, stopped/boot-disabled the broker, removed both fixture services and the temporary firewall rule, and reconfirmed Aster healthy. Live Radarr was never the execution target and was not changed. |
