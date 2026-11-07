# AsterTV v3 M7 — Family content playback acceptance

Date: 2026-11-06  
Target: `AsterTV-Family` (`192.168.1.157`)  
State: accepted playback/class transport; volume automation disabled

## Outcome

After the disabled-first rollout, the owner instructed the assistant to carry
on. Family was independently rechecked as the pinned host with Kodi active and
no player. Home Assistant still contained no `content_volume` configuration,
and the Onkyo baseline was on, unmuted and at `0.44`.

One recently added library movie was started through Kodi's local JSON-RPC
interface. No title, item ID, path, filename, plot or account value was printed
or retained in this evidence. The bounded test then stopped playback and left
Family idle.

## Live proof

- Family reported one active video player.
- The authenticated gateway returned schema `astertv-room-playback.v1`,
  playback `playing`, class `Movie`, no screensaver and sequence `3`.
- A second sample retained the same opaque playback session and advanced to
  sequence `4`, proving live freshness rather than a cached transition.
- During playback the Onkyo remained on, unmuted and exactly `0.44`.
- Home Assistant recorder queries returned `0` content-state attribute rows and
  `0` content-state event rows.
- Playback was stopped through the same local Kodi interface. The bridge then
  reported playback `idle`, class `Unknown` and sequence `5`.
- Kodi initially exposed the empty underlying custom window after the synthetic
  local launch stopped. The cleanup explicitly activated window `10000` Home;
  a live screenshot confirmed the complete Aster Media Home rendered normally.
- Final Kodi state is zero active players, service active and zero restarts.
- Final Onkyo state is on, unmuted and exactly `0.44`.

The result proves the Family playing/class/idle transition and no-history
contract while the controller has no volume authority. It does not authorize
or prove automatic volume behavior.

## Remaining gate

Activation requires a separate owner authorization. Before enabling Family's
profile, retain the existing checkpoints and snapshot, then prove bounded ramp,
nighttime ceiling, physical/app manual override, stale and duplicate state,
Home Assistant outage, restart recovery and Dolby passthrough. Bedroom remains
an independent disabled-first rollout and calibration.

Machine-readable receipt:
`services/kodi/astertv-fleet/releases/astertv-v3-family-content-playback-acceptance-2026-11-06.json`.
