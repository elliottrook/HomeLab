# AsterTV v3 M7 — Family disabled content-state rollout

Date: 2026-11-06  
Target: `AsterTV-Family` (`192.168.1.157`)  
State: live content-state transport; volume automation disabled

## Outcome

The owner confirmed that Family was idle and authorized the validated
candidate push plus a disabled-first Family rollout. The bounded content-state
transport is now live from Family Kodi through Aster Agent to Home Assistant.
The Family volume profile remains disabled: there is no live
`content_volume` configuration and this rollout could not issue a receiver
volume command.

This was deliberately not a playback or volume-automation acceptance test.
Those gates remain separate.

## Recovery and deployment order

The deployment gate matched `AsterTV-Family`, the pinned SSH fingerprint and
zero active players. Recovery remains available from:

- Aster Agent checkpoint
  `/var/lib/aster/checkpoints/astertv-v3-m7-family-content-20261106/`, whose
  gateway is `a064cfc5…8518`;
- Home Assistant snapshot `astertv-m7-content-pre-20261106` and component
  checkpoint
  `/mnt/data/supervisor/homeassistant/.aster-checkpoints/astertv-v3-m7-family-content-20261106/`;
- exact Family live/stable checkpoint
  `/storage/.aster-checkpoints/astertv-v3-m7-family-content-20261106/`, whose
  service and manifest are `a8b26f93…709b8` and `4bd3abfc…02734`.

The candidate was installed in the required order: Aster gateway, Home
Assistant component, then Family client. Home Assistant configuration passed
before restart. Family was rechecked idle before Kodi was stopped, the live
and stable clients were changed together, the accepted room installer
validated its private boundaries, and Kodi restarted with zero restarts.

## Installed hashes

| Owner | Installed object | SHA-256 |
|---|---|---|
| Aster Agent | derived Family gateway | `715b172a62e978ccaf79dfd3f9801da641cd067da72ad7187658efa9ccc0d73a` |
| Home Assistant | component | `0ab1cad5bda6754c50fae11c6752df04d2d26bcb137796bbfd34f94b1e43db77` |
| Home Assistant | content policy | `98453ad7ed0d54735e5b9ed5bf25eb4af9706e1aabe63ce330b1d916d06e8a9d` |
| Home Assistant | contract | `ea42ebedcb59703b93d592b40da90d7796b65ab213a10f7caf671b61f131434f` |
| Family | Remote service, live and stable | `b443edc794f86fc66b1c92d46a048ed18871d9aa325835a2cb8b486d265415c3` |
| Family | content-session helper, live and stable | `a85f477bc877f835d18a7027c7532fcbacdd3ff932912a976bdb5a0b5cfd8acb` |
| Family | stable manifest | `b3cebef42445ee286738f0219b60954dece1236a98a54832616d787dcc34793a` |

The desired Family composition remains
`a09ef2b5974a464738069caeb9fccab44c1feefc9d20763b83eb84bd92a79411`.

## Disabled-first proof

- The authenticated current-state endpoint returned only schema
  `astertv-room-playback.v1`, idle/Unknown/page/screensaver state, opaque
  session and sequence. It returned no title, path, filename, plot, account or
  other media identity.
- During a 27-second idle observation the sequence advanced from `8` to `9`,
  proving live freshness without starting playback.
- Home Assistant recorder inspection found zero content entities, zero content
  events and zero rows containing the playback schema. State remains volatile
  in `hass.data`.
- Home Assistant has zero live configuration files containing
  `content_volume`; the controller has no volume authority.
- The Onkyo remained on, unmuted and at `0.44` across the rollout. Recorder and
  Remote equipment state agreed; no adjustment occurred.
- `ha core check` passed after deployment. Aster Agent and Kodi are active with
  zero restarts, Family still reports zero active players, Remote is HTTP 200,
  and the Family release guard is clean.
- Dolby/HDR, Kodi audio, display, voice, standby and equipment-control settings
  were not in the changed-file set.
- Exact deployment staging files were removed. Checkpoints and the Home
  Assistant snapshot were retained.

Existing Home Assistant warnings about the unrelated Aster Home registry and
the unavailable Bedroom LG entity predate this rollout and were not changed.

## Open acceptance gates

1. With the Family profile still disabled, play one short known item and prove
   playing/class transition, freshness, replay denial and no history while the
   receiver remains untouched.
2. Separately authorize activation of the Family profile, then prove one
   bounded class start, physical/app manual override, stale and duplicate
   state, Home Assistant outage, restart recovery and Dolby passthrough.
3. Repeat the independent disabled-first and profile-calibration process for
   Bedroom; do not infer Family HDMI behavior for Bedroom stereo/CEC.

Machine-readable receipt:
`services/kodi/astertv-fleet/releases/astertv-v3-family-content-state-disabled-rollout-2026-11-06.json`.
