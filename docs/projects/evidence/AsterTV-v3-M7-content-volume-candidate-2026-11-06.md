# AsterTV v3 M7 content-state and volume-policy candidate

Date: 2026-11-06

State: repository-only contract and transport candidate; no Home Assistant or appliance effect

## Outcome

A strict content-free current-state contract now represents only room,
ephemeral session/sequence, freshness, availability, playing/paused/idle,
coarse content class, Aster page and screensaver state. Accepted classes are
Movie, Television, Music, YouTube, Podcast, News, Book/Audiobook and Unknown.
Extra fields such as title or history fail schema validation; stale, replayed
or out-of-sequence observations are rejected and only the current observation
per room is retained.

The pure volume-policy candidate can act only at playback start or a class
transition. Unknown class, unavailable state, non-playing state, unchanged
class and a per-session manual-override latch all produce no action. Targets
are external owner-selected room settings; the repository contains no Family
or Bedroom levels. A configured nighttime ceiling and maximum 0.05 ramp step
are mandatory. The contract has no Kodi volume, audio-route or passthrough
field and emits no Home Assistant service call.

The repository candidate now carries that envelope through the existing
outbound-only path. The Kodi client derives only the coarse class from the
active Aster window or Kodi item type, adds a boot-scoped session, monotonic
sequence and 30-second expiry, and publishes no title, filename, plot, path or
media identifier. The authenticated gateway validates freshness and sequence,
retains one current observation per room and exposes it only to the separately
scoped Home Assistant equipment identity. Home Assistant polls that exact room
state into volatile `hass.data`; it creates no entity, event or recorder row.
Repeated reads are idempotent while stale, malformed, replayed and wrong-key
requests fail closed.

Six focused policy tests, ten client tests, four component source tests and
eleven pinned gateway tests pass. The M10 integrated gate includes all three
Home Assistant room-bridge test files and passes 62 test files with zero
operations-readiness gaps. Fleet materialization pins the new Kodi client,
gateway, component and policy-module hashes so a later release cannot silently
substitute an older lineage.

## Remaining live gate

No live Kodi client publishes this state and the deployed Home Assistant does
not consume it. Coordinated checkpoints and rollout, separate live room
identity validation, Bedroom audio equipment identity, owner-selected room
levels, manual-override source, nighttime schedule, outage/restart tests and
physical Dolby/stereo verification remain required before deployment. The
candidate does not yet act on volume.
