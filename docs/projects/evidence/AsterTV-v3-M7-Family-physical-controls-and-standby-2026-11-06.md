# AsterTV v3 M7 — Family physical controls and soft standby

Date: 2026-11-06  
Target: `AsterTV-Family` (`192.168.1.157`)  
Scope: Family only; Bedroom remains open

## Outcome

The owner accepted the four Family G20 equipment controls. Volume Down and
Volume Up each produced one Onkyo step, Mute toggled without changing the
level, and Power entered and exited AsterTV soft standby while coordinating
the TCL/Onkyo CEC chain. The box itself remains powered and network-live in
soft standby so the physical USB remote or Aster Remote can wake it.

## Identity and input capture

- USB device: `HAOBO Technology USB Composite Device Keyboard`
- VID:PID: `4842:0001`
- capture path at observation: `/dev/input/event5`
- Volume Down: `KEY_VOLUMEDOWN` / 114
- Volume Up: `KEY_VOLUMEUP` / 115
- Mute: `KEY_MUTE` / 113
- Power: `KEY_POWER` / 116
- capture record:
  `services/kodi/astertv-fleet/peripherals/captures/astertv-family-g20-20261106.json`

The pre-existing `g20s-pro-plus.xml` remained byte-identical at
`22b7d36e861fb96e56930ee3eaf1b4aa079fd9506463469cccc778fe3c3ead91`.
The additive equipment-only keymap is
`c09bef238457986f677d360b1cfa1d436495f5b952543ad75601ab66fb64bcfb`.
Kodi logged the new keymap as loaded.

## Checkpoints and deployed hashes

- Family checkpoint:
  `/storage/.aster-checkpoints/astertv-v3-m7-family-standby-20261106/`
- Aster Agent checkpoint:
  `/var/lib/aster/checkpoints/astertv-v3-m7-family-standby-20261106/`
- gateway predecessor:
  `39d6239df804a86a74f187f6c24eb185f6fe9bd2e5a56fdab4bb20c5fcba1231`
- accepted live gateway:
  `a064cfc5ea275e2f28c3c5d8e98cb2e3743a9a284ffe08760d91913304bb8518`
- Remote client service:
  `a8b26f93425e5f17cdfdb3348fd4adca1e711c0c976b8eab2fc8baab8c3709b8`
- Remote equipment helper:
  `0f560cf9022a5ff2c8f6be74fcede2bd3b5243acc26638318ed86fe4a17ed1b7`
- stable add-on tree:
  `4cb1a953070af5ba8a9ceecc7a6ac36100deea050b481853cb86cd8a494e2350`

The exact accepted gateway is stored as a Family recovery source rather than
being inferred from `services/aster-agent/aster_remote.py`. That general source
contains a later, unreleased content-state candidate. The separation prevents
a global materialization from silently replacing the accepted Family behavior.

## Owner-assisted acceptance

1. Aster Remote Power Off created mode-0600 standby state, stopped no active
   playback because the room was idle, and powered off the equipment chain.
2. Aster Remote Power On cleared standby state, restored Media Home and powered
   the chain on.
3. Physical Power repeated the same standby transition; the owner confirmed
   both television and receiver went off.
4. Physical Power woke the chain and restored Media Home; the owner confirmed
   it worked.
5. Physical Volume Down changed `0.560 → 0.555` exactly once.
6. Physical Volume Up changed `0.555 → 0.560` exactly once.
7. Physical Mute changed `false → true`; a second press restored `false` while
   retaining `0.560`.

After acceptance, Family reported power on, volume `0.56`, mute false, idle
playback and Media Home. Bedroom, Family and Jen Remote clients were all
connected. Direct unauthenticated gateway access remained HTTP 403.

During close-out, a separate `systemctl` client stopped `aster-agent.service`
cleanly after requesting a daemon reload, which made the public Remote route
return 502. The accepted gateway bytes were still intact. The enabled service
was started again; it returned active/running, the public route returned 200,
and all three clients reconnected with Family still on, idle, unmuted and at
`0.56`. This was a service-lifecycle interruption, not a standby-state or
equipment-control failure.

## Recovery

Restore the named Family and Aster Agent checkpoints above, remove only
`z-astertv-v3-m7-family-equipment.xml`, restore the predecessor gateway, and
restart Kodi/Aster Agent as recorded by their checkpoint receipts. The normal
G20 navigation keymap and original equipment remotes remain independent
recovery controls.

## Residual scope

This accepts Family only. Bedroom still requires its exact physical key
capture, LG-mediated volume/mute proof, standby/wake, duplicate-command and
reconnect tests. No Bedroom or Jen live state was changed by this acceptance.
