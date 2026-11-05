# AsterTV v3 M5 podcast-request read-only audit

Date: 2026-11-04

State: capability and authority audit complete; no request submitted

## Result

Audiobookshelf is the appropriate podcast discovery, catalogue and listening
authority, but AsterTV's existing playback identity cannot and should not add
podcasts directly. A submission path requires a separately authorized
server-side semantic boundary or an owner-approved request queue. Seerr remains
film/television-only.

No credential value, podcast title, feed URL, household listening state or
library mutation was exported during this audit.

## Verified live contract

- The server reports Audiobookshelf `2.36.0`.
- The live source route is singular:
  `GET /api/search/podcast?term=...&country=...`; the controller comment and
  older documentation still say plural, so code must pin and test the live
  versioned route rather than trust the stale comment.
- A content-neutral search returned 50 results. Each result exposes a provider
  ID, feed URL, title, artist, artwork and descriptive metadata suitable for a
  preview; no state changed.
- The podcast library currently contains seven items. All seven expose both a
  provider ID and feed URL. Hash-only comparison found zero duplicate provider
  IDs and zero duplicate normalized feed URLs.
- AsterTV-Jen's existing restricted Audiobookshelf identity is type `user`,
  has all-library/download access, and has update, delete and upload disabled.
- Audiobookshelf's live `PodcastController.create` requires `isAdminOrUp`, a
  valid podcast library/folder, a path inside that folder and podcast metadata.
  It creates a directory and database item, can download artwork and may enable
  automatic episode downloads. It is therefore a material write, not a safe
  extension of the playback credential.

The official Audiobookshelf documentation confirms podcast search/add support,
while its API reference explicitly warns that it is no longer maintained. The
installed 2.36.0 route/controller source and content-neutral live probes are
therefore the compatibility authority for this project:

- <https://audiobookshelf.org/docs/documentation/introduction/>
- <https://api.audiobookshelf.org/>
- <https://github.com/advplyr/audiobookshelf>

## Required semantic contract

The television client may receive only:

- search results with provider ID, canonical feed URL hash, display metadata
  and artwork proxy reference;
- duplicate status: already subscribed, already requested, available to
  request, approved, rejected, processing or failed;
- one opaque proposal ID bound to profile, provider ID, normalized feed hash,
  server/library identity and expiry; and
- an explicit final request action using that proposal ID and a single-use
  idempotency key.

The client must never receive an Audiobookshelf admin key, filesystem path,
library folder ID, arbitrary URL-fetch primitive or general API proxy.

## Implementation choices requiring an owner decision

### Recommended: owner-approved request queue

A dedicated service performs public discovery and hash-only duplicate checks,
then stores an idempotent request for owner approval. Approval is a separate
authenticated administrative action. Only that action invokes a server-local
Audiobookshelf adapter with a fixed podcast library/folder and safe generated
path. This keeps a compromised television from immediately creating folders,
downloading artwork or enabling feeds.

### Higher-risk alternative: immediate subscription broker

A dedicated server-side broker holds an independently revocable admin-or-up
credential and immediately creates the podcast after an explicit television
confirmation. It must enforce the same fixed library/folder/path policy,
canonical HTTPS feed allowlist/SSRF controls, duplicate and idempotency journal,
download defaults, rate limit and audit trail. This is faster but gives the
broker materially broader authority and blast radius.

## Proposed bounded Stream A gate

After the owner selects one model, a new envelope may:

1. build and test the semantic proposal/duplicate/idempotency contract with
   synthetic fixtures;
2. deploy one isolated server-side service with no general proxy surface;
3. expose only search, status, propose and explicit-submit operations to one
   lab AsterTV identity;
4. use a synthetic, reversible feed or queue-only fixture, with a verified
   checkpoint and cleanup path;
5. prove duplicate replay, stale proposal, wrong profile, bad feed, service
   outage and interrupted submission fail closed; and
6. connect the accepted podcast-request UI only after those gates pass.

This audit authorizes no service identity, admin credential, container,
firewall change, podcast creation, episode download or AsterTV deployment.
