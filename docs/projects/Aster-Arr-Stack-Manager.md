# Aster ARR Stack Manager

> Status: Active — advisory-only foundation
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
- [ ] Identify the smallest useful sanitized health schema; it must contain no
  API keys, URLs with credentials, media titles, paths outside approved roots,
  or raw service responses.
- [ ] Record every existing automation that can create, search, rename, import
  or delete so the manager never duplicates it blindly.

Completion gate: the review names every source, excluded field and dependency;
two independent reviewers can locate no credential or private-library content.

## Milestone 1 — Advisory Hermes skill and Aster knowledge

- [x] Create a versioned Hermes ARR-manager skill that is advisory-only.
- [ ] Install the reviewed skill into Hermes' user-local skill directory and
  verify a fresh Hermes session recognizes it.
- [x] Add reviewed ARR operational material to the Aster snapshot manifest.
- [ ] Run source-aware question tests for Sonarr, Radarr and Lidarr basics,
  Prowlarr sync, SABnzbd/import failures, stale-source traps and missing facts.
- [ ] Run adversarial tests for API-key requests, destructive cleanup, forced
  acquisition and prompt injection embedded in ARR notes.

Completion gate: Aster answers the accepted questions with provenance, refuses
unsafe or secret-bearing requests, and does not claim live state without the
sanitized report.

## Milestone 2 — Bounded read-only live evidence

- [ ] Build a root/operator-owned report producer outside Aster that reads
  approved ARR health endpoints with private credentials.
- [ ] Validate the report schema, restrictive ownership and freshness window.
- [ ] Give Aster read-only access to only that report directory.
- [ ] Test stale, malformed, partial and unavailable reports; the manager must
  report uncertainty rather than retry arbitrary network targets.

Completion gate: Aster can diagnose a bounded service/queue/import state
without holding a service credential or making arbitrary HTTP requests.

## Milestone 3 — Action-proposal rehearsal

- [ ] Define each candidate action as a separate project decision with target,
  identity, validation, audit output, timeout, rollback and exact approval
  moment.
- [ ] Start with dry-run/proposal output only; compare it against a manually
  reviewed operation.
- [ ] Treat every mutation as a separate graduation gate. No standing approval
  or natural-language request grants general ARR control.

Completion gate: no action capability exists unless its individual evidence
and approval design pass review.

## Milestone 4 — Graduated ARR read and repair capability

This milestone is the only path from advisory answers to Aster being able to
read current ARR state and repair a defined problem. It does **not** grant a
general ARR administrator, a raw service API key, broad shell access, media
library access, or standing permission to make changes.

- [ ] Define a dedicated ARR broker with one narrow, authenticated operation
  per endpoint. The broker, not Aster or Hermes, holds any private service
  credential and rejects every undeclared route, method, field and target.
- [ ] Select each initial repair action separately. For each one record: exact
  request schema; permitted resource scope; preconditions; expected result;
  idempotency/replay behavior; validation; audit record; timeout; rollback or
  explicit non-reversibility; and Jason's approval moment.
- [ ] Start in a disposable or no-op mode. Aster may form a proposal and the
  broker must return a complete dry-run only; compare it against an operator's
  independent manual result before enabling a real mutation.
- [ ] Add a current, sanitized report for reading service health and aggregate
  queue/import stages. Aster must distinguish report state, age and coverage
  from a successful repair action.
- [ ] Enable no more than one low-blast-radius repair action at a time. Any
  action that can acquire content, remove media, rename files, alter indexers,
  profiles, root folders, download-client settings or monitoring scope needs
  its own later decision and must not be smuggled into the first broker.

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
