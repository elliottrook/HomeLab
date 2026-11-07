# AsterTV v3 M11 — Bedroom physical controls and wake acceptance

Date: 2026-11-07  
Scope: AsterTV Bedroom only  
Outcome: owner-accepted live; reconciled into the fleet composition candidate

## Accepted behavior

- The Bedroom G20 receiver is `4842:0001` on the accepted host. Owner-observed
  input codes are Volume Down `114`, Volume Up `115`, Mute `113`, and Power
  `116`.
- Volume Up produced exactly one LG step (`0.14` to `0.15`). Mute reported
  true and a second press restored false. The LG later settled at `0.10`, so
  volume targets remain a separate calibration decision rather than an
  inferred copy of Family values.
- Power Off turned off the LG/Vizio chain while the AsterTV appliance remained
  running and idle.
- Raw routed wake was unreliable over the LG Wi-Fi path. The accepted wake
  helper sends one native FreeBSD frame plus six fixed-MAC UDP magic packets
  to the IoT subnet broadcast. The owner-observed final physical Power test
  woke the LG/Vizio chain in about one second.
- Existing Bedroom navigation remained outside the new equipment key overlay.

## Bounded control path

`G20 -> Bedroom Kodi keymap -> room-scoped Aster equipment action -> Home
Assistant Aster room bridge -> fixed shell_command -> OPNsense forced-command
SSH key -> fixed-MAC wake helper -> LG/Vizio CEC chain`

The gateway cannot supply a Home Assistant service, entity, MAC, interface or
command. `power_on_service` is schema-restricted to
`shell_command.astertv_bedroom_lg_wake`. The OPNsense public key is restricted
to source `192.168.20.11`, a single forced command, no forwarding, no PTY and
no user rc. Private key material is deployment-owned and is not recorded here.

## Network and recovery facts

- LG webOS entity: `media_player.lg_webos_tv_oled55g4sub_dccqljr`
- LG IoT address/MAC: `192.168.30.141` / `74:90:bc:ab:a6:c8`
- OPNsense rule: `2c486e0a-6db5-4a31-9bb0-bf512dd12a01`, Servers interface,
  source `192.168.20.11`, destination interface address, TCP 22, sequence
  `1690`, logged and placed before the firewall self-block.
- Wake helper: `/usr/local/sbin/astertv-bedroom-lg-wake`, accepted SHA-256
  `939fe37af159d5d703e822e48df82f5f097c27c3798888b89f30cce9d27c1973`.
- OPNsense checkpoint:
  `/conf/backup/config-astertv-bedroom-wol-before-20261107.xml`.
- OPNsense authorized-keys checkpoint:
  `/root/.ssh/authorized_keys.astertv-bedroom-lg-dualwake-20261107.bak`.
- Home Assistant configuration checkpoint:
  `/config/configuration.yaml.astertv-bedroom-wol-relay-20261107.bak`.
- Home Assistant component checkpoint:
  `/config/custom_components/aster_room_bridge/__init__.py.astertv-bedroom-wol-direct-20261107.bak`.
- Kodi keymap checkpoint:
  `/storage/.aster-checkpoints/astertv-v3-bedroom-equipment-keys-20261107`.

## Regression findings folded into the composition

- The Bedroom Remote add-on and its stable staging tree were both missing
  `equipment.py`; both were repaired from the reviewed repository candidate.
  The existing `remote-client-v3` overlay owns that helper, so a future
  composition install restores it rather than preserving the omission.
- A deliberate manual Kodi stop displayed `AsterTV guard failed`, although two
  guard runs completed successfully across all 535 files. This is a display
  status defect, not release drift, and must not be used as evidence of a
  failed guard without the unit result and file verification.
- The accepted physical keymap and Bedroom bridge are now named overlays in
  `astertv-bedroom.yaml`; future global releases must compose them explicitly.

## Validation

- Home Assistant configuration check passed before each restart.
- Home Assistant recovered the Bedroom equipment bridge and reported fresh
  power, volume and mute observations.
- The source-restricted OPNsense rule appeared in the loaded `pf` ruleset.
- A direct HA-to-forced-command test returned success without shell authority.
- Repository unit tests cover the fixed service allowlist, power-on-only use,
  exact G20 codes, fixed MAC/interface, UDP broadcast target and absence of
  caller-controlled wake arguments.

