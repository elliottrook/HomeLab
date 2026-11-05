# AsterTV v3 SA-M5P1 podcast broker core evidence

Date: 2026-11-04

State: local broker core complete; no live deployment

## Boundary

This milestone implements only the owner-approved queue semantics. There is no
Audiobookshelf admin credential, approval endpoint, subscription executor,
folder creation, feed fetch, episode download, client deployment or firewall
change.

## Implemented contract

- Hash-only bearer-token registry binding one token to a client/profile pair.
- Read-only Audiobookshelf 2.36 adapter using the verified singular
  `/api/search/podcast` route and podcast-library inventory.
- HTTPS-only canonical feed and artwork URLs; no credentials, fragments,
  non-default ports or arbitrary client-supplied fetch operation.
- Opaque 15-minute candidate references scoped to the authenticated client and
  profile. Provider IDs and feed URLs are not returned to AsterTV.
- Duplicate state from both provider ID and canonical feed hash.
- Explicit request confirmation plus profile-scoped, single-use idempotency.
- Queue status `pending_owner_approval`; no transition can execute a request.
- Private locked JSON state with atomic replace, directory fsync, mode checks
  and a four-megabyte hard bound.
- Minimal HTTP surface: unauthenticated inert health plus authenticated search,
  request and status. There is no general URL, HTTP or service proxy.
- Non-root container definition; live image digest and runtime mounts remain
  part of SA-M5P2 validation.

## Validation

`python3 -m unittest discover -s services/aster-podcast-request-broker -p 'test_*.py'`

Result: 13 tests passed.

The tests cover:

- exact token success and wrong-token denial;
- strict candidate/search/request schemas and unsafe feed rejection;
- the installed Audiobookshelf route and bounded response mapping;
- feed/provider duplicate detection;
- opaque client output with no provider ID or feed URL;
- explicit confirmation, same-key replay and new-key duplicate behavior;
- candidate expiry and cross-profile candidate/status denial;
- already-subscribed denial;
- private atomic persistence;
- inert unauthenticated health, authenticated semantic dispatch and 404 for an
  attempted general proxy route.

All modules also pass Python bytecode compilation and `git diff --check`.

## Next gate

SA-M5P2 must checkpoint the TrueNAS service area and Jen credential target,
pin the base and built image, create only read-only server and Jen client
identities, add only the exact Jen-to-broker firewall path, then prove restart,
wrong-token, stale/cross-profile, dependency-outage and queue persistence. It
must stop before any AsterTV UI connection or Audiobookshelf subscription.
