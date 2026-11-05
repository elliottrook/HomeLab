# AsterTV v3 SA-M5P3/P4 podcast request client evidence

Date: 2026-11-04

Target: AsterTV-Jen (`192.168.1.180`) only

State: accepted request UI retained; subscription execution absent

## Installed boundary

- Added `script.astertv.podcast.requests` and one Podcasts-page entry labelled
  **Request a podcast**.
- The add-on reads only Jen's independently revocable mode-0600 broker token.
  It has no Audiobookshelf key, provider/feed identifiers, filesystem path,
  approval operation or subscription/download adapter.
- Results expose title, creator, artwork and duplicate state. Request requires
  a separate Yes/No confirmation and stores a private local receipt plus a
  crash-safe idempotency key.
- “Your requests” refreshes only opaque references through `/v1/status` and
  describes the sole executable state as **Pending owner approval**.
- Family, Bedroom, the podcast playback add-on, Audiobookshelf folders and
  podcast items were unchanged.

## Recovery and persistence

- Exact skin checkpoint:
  `/storage/.aster-checkpoints/astertv-v3-m5p-jen`
- Stable overlay source: `/storage/.aster-v3/m5p`
- Boot unit: `astertv-v3-m5p-jen.service`, ordered after M5 News and before
  Kodi.
- The service reapplies only two exact-base skin transforms and the add-on; an
  unknown base fails closed.
- Broker hardening checkpoint:
  `Media/appdata@aster-podcast-request-m5p3-20261105T040500Z`
- Active hardened image:
  `sha256:95e905988ca8e66c7356fcddf2fa08ddca63a17c3f2d3e3e2491b73cc35e3dee`

The first live add-on launch failed closed because Kodi 22 no longer provides
`xbmc.translatePath`. It performed no request. The client was corrected to
`xbmcvfs.translatePath`, covered by a compatibility assertion and reapplied
from the stable source.

## Live acceptance

- Seven client/install tests and fifteen broker tests pass.
- Books → Podcasts retained normal podcast artwork/playback navigation. Focus
  traversed the tile grid, existing filter, Clear, Request a podcast, then the
  search dialog in displayed order.
- Search opened Kodi's keyboard and returned live candidates with artwork.
- Result → Request and result → top rail focus paths worked; Back returned to
  the exact Request a podcast control on the Podcasts page.
- With the broker deliberately stopped, search returned to the still-open
  request dialog, Kodi stayed active and idle, and queue cardinality remained
  one. Broker restart restored health with `execution_enabled:false`.
- The existing synthetic **Discovery** request was replayed through the real
  confirmation UI. The broker returned the same duplicate record, Jen stored
  one local pending receipt, and server queue cardinality remained exactly one.
- “Your requests” refreshed that receipt and selected Discovery with pending
  owner status.
- Full Jen reboot ran guard → M4 → M4Y → M5N → M5P → Kodi successfully. The
  M5P unit exited zero, add-on `0.1.0` stayed enabled, the token stayed mode
  0600, both patched skin hashes persisted, search still worked and no player
  was active.

## Catalogue hardening found during acceptance

Audiobookshelf returned one malformed external feed URL for a Discovery
search. The original strict parser rejected the entire set with
`feed-url-url`. The broker now catches a contract failure per candidate and
omits only that unsafe record; it still rejects non-HTTPS feed/artwork URLs and
does not expose either to the client. A regression test pins this behavior.
After the hardened image was force-recreated, Discovery search returned 19
valid candidates, health was ready and queue cardinality remained one.

## Remaining authority gate

There is still no owner approval/subscription executor. Adding one would need a
separate authority design, write-capable service identity, approval UI,
Audiobookshelf side-effect and rollback review. This milestone grants none of
those capabilities.
