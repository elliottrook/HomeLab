---
name: arr-stack-manager
description: "Diagnose ARR workflows and propose safe next actions."
version: 0.1.0
author: Jason Elliott, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [ARR, Sonarr, Radarr, Lidarr, Prowlarr, SABnzbd]
    related_skills: [hermes-agent-skill-authoring]
---

# ARR Stack Manager Skill

Use Aster as the source-aware advisor for Sonarr, Radarr, Lidarr, Prowlarr,
SABnzbd and Jellyfin workflow questions. This skill guides diagnosis and a
reviewable proposal; it does not hold ARR credentials, call ARR APIs, inspect
live configuration, or execute an ARR action.

## When to Use

- Questions about how the ARR services, downloader and Jellyfin relate.
- Diagnosing a reported queue, import, indexer, naming or metadata problem
  from operator-provided, sanitized evidence.
- Preparing a change proposal for a monitored item, search, rename, indexer,
  quality profile or downloader setting.

Do not use it to retrieve credentials, browse private media, acquire content,
or make an unapproved ARR change.

## Procedure

1. Classify the request as a knowledge question, a bounded diagnosis, or a
   requested change. Completion: state which class applies before advising.
2. For knowledge questions, ask Aster and retain its cited source, authority
   and review date. Completion: distinguish current operational evidence from
   project history or derived memory.
3. For diagnosis, use only a sanitized report or facts the operator supplied.
   Completion: name missing or stale evidence; do not request a key, config
   path, raw queue payload or arbitrary endpoint.
4. For a requested change, produce a proposal with scope, expected outcome,
   validation, rollback and exact approval needed. Completion: no action is
   executed or implied.
5. Stop on conflicts, missing evidence, private-library details, credentials
   or any delete/rename/search/grab/profile/indexer/downloader mutation.
   Completion: explain the boundary and ask for the appropriate reviewed
   procedure or explicit approval.

## Known operating rules

- Prowlarr app synchronization and ARR API-key changes are coupled; stale
  configuration evidence can be misleading.
- Lidarr is album-oriented. A request for a track can imply an album-level
  acquisition, so it is never an automatic action.
- A successful download is not proof of a usable library item. Diagnose the
  complete path: queue, import, naming, metadata, scan and Jellyfin match.
- Aster's current live capability is read-only. Broad ARR API keys are not a
  suitable shortcut for a future read-only integration.

## Verification

- Every answer cites an approved source or labels the state unknown.
- Every proposal identifies its approval boundary and does not invoke a tool.
- No response reveals credentials, raw private-library content or a live
  service configuration location.
