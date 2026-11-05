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

## Approved start and recovery gate

Jason approved SA-M7-ROOMS on 2026-11-05. Immediately before effects, Family
and Bedroom both returned an empty `Player.GetActivePlayers` result, Home
Assistant passed `ha core check`, and the protected 2026-11-05 backup was
verified at both `.local` and `Backup_Synology` (the retained historical mount
name now backed by TrueNAS). Proxmox had about 603 GiB free in `local-lvm` and
created snapshot `astertv-m7-pre-20261105`; VM 103 thawed normally and the
snapshot appears in `qm listsnapshot`.

The supported Home Assistant browser config flow was opened next. Its first
normal local login returned `Invalid username or password`, so that attempt
made no change. The owner later completed the normal login in Safari; no
registry file was edited and no authentication workaround was used.

## First bounded integrations

The Family Onkyo was admitted through one exact OPNsense rule from Home
Assistant (`192.168.20.11`) to the verified receiver (`192.168.1.186`) on port
`60128`. Home Assistant's `aioonkyo` interview uses UDP discovery against the
specified host and ongoing receiver control uses TCP, so the final rule is
`TCP/UDP`, not a general inter-VLAN permit. The rule UUID is
`af4ef3e0-e9ad-45c7-b2a7-2fe59cb50cff`; its pre-change checkpoints and
machine-readable proofs remain under `/conf/backup/` on OPNsense. A real
interview from the Home Assistant container returned model `TX-RZ30`, MAC
`0009B06385BC`, address `192.168.1.186` and port `60128` before the native
integration was accepted. Home Assistant created the main, Zone 2 and Zone 3
entities. Only the main entity is in M7 scope; it is displayed as **Family Room
Receiver** and reported `off`, consistent with physical standby. No receiver
command has yet been issued. Zone 2 and Zone 3 remain excluded because the
selected TV source is not valid as their `MAIN SOURCE`.

The owner then completed the LG television's native on-screen pairing for the
verified Bedroom endpoint `192.168.30.141`. Home Assistant created
`media_player.lg_webos_tv_oled55g4sub_dccqljr` and the disabled-by-integration
screen switch for model `OLED55G4SUB.DCCQLJR`. The primary entity immediately
recorded state `on`, matching the television being awake for pairing. The
device is displayed as **Bedroom TV** while its stable technical entity ID was
left unchanged. No power, volume, source or playback command was sent.

These integrations establish identity and fresh observation only. Aster Remote
equipment controls remain disabled until explicit command/feedback,
duplicate-command, standby/wake and physical-remote recovery tests pass.

### Family TCL local-only control boundary

The powered Family television advertised `_androidtvremote2._tcp` as **Family
Room TV** at `192.168.30.162:6466`, with wake port `6465` and Bluetooth address
`0C:91:60:75:7C:5D`. Its Google Cast record independently identified model
`Smart TV Pro`, manufacturer TCL and port `8009`. The authoritative DHCP lease
shows network-interface MAC `0C:91:60:75:7C:5C`; the Bluetooth address is not a
DHCP identity.

OPNsense rule `bfaf8ab8-9e66-43fe-8be0-f25a6ca13d47` blocks this one host to
`any` on IoT at sequence `950`, after the existing local DNS/NTP permits and
private-network block but before the general IoT Internet permit. Its
checkpoint and proof are
`config-astertv-m7-family-tcl-wan-{before,proof}-20261105.*`. The loaded PF rule
immediately accumulated denied packets while Android TV Remote discovery and
Home Assistant local state stayed live.

The owner completed the television's native pairing code flow. Home Assistant
created `media_player.family_room_tv` and `remote.family_room_tv`, both
reporting `on`, for device ID `a07a69273c840d81e53346d9c3500b27` and config
entry `01M6PNBDBDHEN6ENK4H691HG9C`. No control command was sent.

The first reservation draft used the integration-advertised Bluetooth address
ending `5D`. A post-reload comparison against the authoritative DHCP lease
caught the mismatch before lease turnover. The reservation was corrected in
place, with its own immutable before/proof pair, to network MAC ending `5C`.
The running dnsmasq configuration now contains exactly
`dhcp-host=0c:91:60:75:7c:5c,192.168.30.162,family-room-tv`; Home Assistant
observation and the privacy rule remained live throughout. The clean-install
script and regression test also use `5C`, while the one-time correction and
its test retain the incident/recovery evidence.

The first post-privacy cache-expiry test then found a second fail-closed edge:
the host-to-`any` Internet block also matched the television's unsolicited
multicast discovery replies. Home Assistant's established session stayed live,
but a fresh Android TV Remote resolution timed out. Two rules were therefore
added ahead of the block for this host only: `224.0.0.251:5353/UDP` (mDNS) and
`239.255.255.250:1900/UDP` (SSDP). No unicast destination or Internet service
was opened. After filter reload, a fresh Android TV Remote browse again
resolved `192.168.30.162:6466`, AirPlay resolved the TCL at
`192.168.30.162:7000`, Home Assistant remained `on`, and the following
host-specific Internet block remained loaded before the general IoT pass. The
discovery change has its own immutable checkpoint/proof and apply/rollback
tests.

The owner then placed the television into normal standby rather than full
shutdown. Home Assistant recorded both Family Room TV entities changing to
`off` at 13:29:50 while fresh Android TV Remote and AirPlay discovery still
resolved, proving that the local standby path survives the Internet block. A
single explicit **Turn on** action was then issued through the native Home
Assistant entity; no blind toggle, volume, navigation or playback command was
used. Both entities returned to `on` at 13:31:09 and the live media controls
reappeared. The owner confirmed that standby powered both the TCL and Family
Room Receiver off through CEC, and the explicit TV wake brought both back on.
The owner then deliberately powered the chain off again at 13:34:11, proving
that the physical control path remained available. A fresh explicit wake
returned the TV entity to `on` at 13:35:22. Sending the same explicit **Turn
on** command once more while already on produced no new state transition and
did not invert the entity: it remained `on` with the original 13:35:22 event.
The owner confirmed that both devices remained on after the duplicate command.
Family power therefore passes explicit-command, fresh-feedback, standby/wake,
duplicate-command, CEC and physical-recovery acceptance. This does not confer
volume, mute, source, playback or navigation authority; each remains separately
gated.

