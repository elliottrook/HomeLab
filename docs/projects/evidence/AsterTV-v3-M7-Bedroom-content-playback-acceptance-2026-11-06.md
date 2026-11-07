# AsterTV v3 M7 — Bedroom content playback acceptance

Date: 2026-11-06 (America/Vancouver)  
Target: `AsterTV-Bedroom` / `192.168.1.140`  
Outcome: accepted Movie/class transport; no equipment or volume authority

## Authorization and preflight

Jason explicitly authorized one bounded playback test after the disabled-first
rollout. The immediate preflight proved:

- exact hostname `AsterTV-Bedroom`;
- Kodi active with zero restarts and no active player;
- the retained Aster, Home Assistant and Bedroom rollback checkpoints present;
- exact installed publisher and content-session hashes;
- Home Assistant configuration and contract still at the accepted Bedroom
  disabled-first hashes;
- `HA-Bedroom` still had `actions: []` and no `content_volume` profile; and
- the authenticated state endpoint was fresh idle/Unknown at sequence `59`.

Kodi exposed 1,069 library movies. The test selected one internally without
printing or retaining its title, item ID, path, filename, plot or account.

## Live proof

- Kodi reported exactly one active internal video player.
- The authenticated content endpoint returned only the bounded coarse schema:
  playing/Movie at sequence `1`, then the same session at sequence `2` six
  seconds later.
- Kodi application volume stayed unmuted at `97` before, during and after the
  test.
- The adopted Bedroom LG entity stayed on, unmuted and at its unchanged
  reported level `0.0` before, during and after the test. This records the
  entity's observed state; it does not infer soundbar gain from that value.
- Home Assistant recorder contained zero state-attribute rows and zero
  event-data rows with the playback schema.
- Playback was stopped through the same local Kodi interface and Home window
  `10000` was explicitly restored.
- Final authenticated state was idle/Unknown/page `media` at sequence `3`.
- Final Kodi state was zero active players, Home visible, service active and
  zero restarts. Aster Agent was active with zero restarts.

No volume service call, equipment command, file/configuration change, account
change, network change or media-history record was part of the test. The
source-local probe was removed immediately afterward.

## Result and next boundary

Bedroom now passes the disabled content transport gate: idle → playing/Movie
with advancing freshness → idle, while all action and automatic-volume
authority remain absent.

This does not calibrate Bedroom listening levels and does not authorize a
Bedroom `content_volume` profile. Any later calibration must account for the
Bedroom LG/soundbar chain independently rather than reuse Family's Onkyo
targets.

Machine-readable receipt:
`services/kodi/astertv-fleet/releases/astertv-v3-bedroom-content-playback-acceptance-2026-11-06.json`.
