# AsterTV v3 M7 equipment preflight — 2026-11-05

## Scope

This is a read-only Stream A preflight for the planned Home Assistant bridge
and room-equipment controls. It made no Home Assistant configuration change,
created no credential or firewall rule, sent no equipment command and changed
no AsterTV runtime setting.

## Live inventory

| Boundary | Observation | Consequence |
| --- | --- | --- |
| Home Assistant | VM 103 is running. Core reports `2026.9.1`; `2026.11.0` is available but was not installed. Existing config entries include Hue, Lutron, Matter, Apple TV, Sonos, HomeKit and Wyoming, but no `kodi`, `onkyo`, `androidtv_remote` or `webostv` entry. | M7 is a new bounded integration, not repair of an existing equipment bridge. The unrelated Core update remains out of scope. |
| Family display | The live HDMI EDID identifies manufacturer `TCL`, product `Beyond TV`, HDR static metadata and a Dolby vendor block. | Retain the planned TCL Android/Google TV Remote evaluation; do not infer its network endpoint or standby behavior solely from EDID. |
| Family receiver | DHCP identifies `Onkyo-TX-RZ30-6385BC` at `192.168.1.186`; TCP `60128` and `80` answer. | The receiver's native local control path is present and remains the preferred volume/mute/power authority. Pairing and commands were not attempted. |
| Bedroom display | The connected DP-to-display path identifies manufacturer `GSM`, product `LG TV SSCR2`, HDR metadata and a Dolby video block. DHCP identifies `LGwebOSTV` at `192.168.30.141`; TCP `3000` and `3001` answer. | Add the Bedroom LG TV to M7 and evaluate Home Assistant's native webOS TV integration. The exact consumer model and network standby behavior remain to be verified before acceptance. |
| Bedroom audio | The current display EDID advertises two-channel PCM on this path. The owner has separately accepted the present Bedroom playback sound. The soundbar/receiver make and model are not yet recorded. | Do not change the accepted playback route or generalize the low-spec/stereo constraint. Equipment-control acceptance needs the soundbar model and a real standby/volume test. |
| Kodi clients | Family and Bedroom both report `services.webserver=false`, port `8080`, authentication enabled and the generic username `kodi`. | Native Home Assistant Kodi registration cannot be enabled safely as-is. M7 needs separate room credentials, source-restricted paths and an idle, checkpointed web-server activation. |
| Existing HA-to-client path | Home Assistant currently has source-restricted SSH delivery only for the read-only Aster Home display feed. | Do not repurpose the forced-command feed identity for Kodi or equipment control. New paths must be independently revocable and minimal. |

## Proposed bounded implementation order

1. Record the TCL network endpoint and exact Bedroom LG/soundbar models; verify
   network-standby settings without issuing a power command.
2. Add native Home Assistant equipment integrations one at a time: Family
   Onkyo first, then Family TCL, then Bedroom LG. Preserve physical remotes and
   prove state feedback before wiring any Aster action.
3. Give Family and Bedroom separate Kodi credentials. Open only Home Assistant
   `192.168.20.11` to each client's authenticated Kodi HTTP endpoint, with no
   general Trusted/Servers path and no arbitrary JSON-RPC exposed to Aster.
4. Export only bounded room state and semantic actions through the M7 bridge.
   Keep volume, mute and power disabled in Aster Remote until the corresponding
   device passes command, feedback, duplicate-command, standby and recovery
   tests.
5. Add content-class volume profiles only after direct room controls work.
   Apply on class transition, ramp safely, enforce the night ceiling and latch
   manual override for the current session.

## Pre-start risks and controls

- A blind power toggle can invert state: use explicit on/off where supported
  and require fresh feedback.
- CEC can relay a valid TV command into an unintended receiver change: test one
  device at a time and retain physical-remote recovery.
- Kodi credentials or general JSON-RPC could become a room-control backdoor:
  use unique mode-0600 credentials, exact source rules and semantic allowlists.
- A volume profile can override a person or damage listening comfort: ramp,
  cap, latch manual changes and never embed final room levels as release
  constants.
- Dolby/HDR or the accepted Bedroom audio path can regress if playback settings
  are touched: equipment work must not modify Kodi audio/video settings and
  must re-run playback route checks after each client change.

Stop on an unknown device identity, unverified checkpoint, broader network
reachability, credential output, stale state used for power, playback-route
drift or a command that affects equipment outside the selected room.

