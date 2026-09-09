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
- [ ] Add reviewed ARR operational material to the Aster snapshot manifest.
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

## Milestone 3 — Optional action proposals

- [ ] Define each candidate action as a separate project decision with target,
  identity, validation, audit output, timeout, rollback and exact approval
  moment.
- [ ] Start with dry-run/proposal output only; compare it against a manually
  reviewed operation.
- [ ] Treat every mutation as a separate graduation gate. No standing approval
  or natural-language request grants general ARR control.

Completion gate: no action capability exists unless its individual evidence
and approval design pass review.

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
