# AsterTV v3 M7 — Family content-volume automation candidate

Date: 2026-11-06  
State: repository candidate; disabled; not deployed

## Outcome

The repository now contains a Family-only, owner-selected profile and the
fail-closed controller needed to apply it later. The profile remains
`enabled: false`; no Home Assistant configuration, gateway, Kodi client or
receiver state changed during this work.

## Control behavior

- The Kodi client publishes only coarse content class, playback state, Aster
  page, screensaver flag and an opaque playback-session/sequence. It publishes
  no title, path, plot, filename, account or history.
- Session identity rotates on an idle-to-playing transition. Pause/resume stays
  in the same session; a later playback start gets sequence 1 in a new session.
- A controller restart while media is already playing only primes state and
  never changes volume.
- Actions are possible only at a new playback start or content-class
  transition, through fixed `media_player.volume_set` calls to the configured
  room entity.
- Each ramp step is bounded by the profile (`0.02`, hard schema maximum
  `0.05`). Unknown, idle, paused, stale, unavailable or malformed state does
  nothing.
- A level change not produced by the controller latches manual override for
  that playback session. The next playback session clears the latch.
- Missing/unknown receiver level or night/day state consumes the transition
  without action, preventing a late surprise adjustment when context returns.
- Content polling and volume failures remain isolated from the accepted
  Family power, mute and direct volume controls.

## Family profile and night signal

`services/home-assistant/aster_room_bridge/profiles/family.json` records the
owner-selected values but is not a live configuration source. It maps Movie
`0.60`, Television `0.58`, YouTube `0.455`, Music `0.43`, Podcast `0.44`, News
`0.44`, and Book/Audiobook `0.44`, with nighttime ceiling `0.60` and maximum
step `0.02`.

A read-only Home Assistant VM 103 query verified the existing `sun.sun` state
as `below_horizon`. The candidate therefore declares exactly
`below_horizon` as night and `above_horizon` as day. Any missing or other state
fails closed. No helper or schedule was created.

## Verification

- 20 Home Assistant bridge policy/source/contract tests pass.
- 38 Aster Remote client, installer, keymap and session tests pass.
- 18 fleet materialization tests pass.
- Fleet materializers and compiler regenerate deterministically.
- Candidate source hashes:
  - Remote service:
    `b443edc794f86fc66b1c92d46a048ed18871d9aa325835a2cb8b486d265415c3`
  - content-session helper:
    `a85f477bc877f835d18a7027c7532fcbacdd3ff932912a976bdb5a0b5cfd8acb`
  - Home Assistant component:
    `0ab1cad5bda6754c50fae11c6752df04d2d26bcb137796bbfd34f94b1e43db77`
  - volume policy:
    `98453ad7ed0d54735e5b9ed5bf25eb4af9706e1aabe63ce330b1d916d06e8a9d`

## Remaining live gate

Before activation: confirm both relevant displays are idle; checkpoint Aster
Agent, Home Assistant and clients; deploy gateway first, Home Assistant second
and clients last; prove content freshness/replay/no-history while the profile
is still disabled; then enable Family only and test one bounded class start,
physical/app manual override, stale state, duplicate state, Home Assistant
outage, restart recovery and Dolby passthrough. Bedroom remains independent and
requires its own profile and stereo/CEC proof.
