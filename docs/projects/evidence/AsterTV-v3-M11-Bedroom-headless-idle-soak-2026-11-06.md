# AsterTV v3 M11 Bedroom headless idle soak — 2026-11-06

Date: 2026-11-06 America/Vancouver / 2026-11-07 UTC  
Target: `AsterTV-Bedroom` / `192.168.1.140`  
Outcome: pass for headless idle/Wi-Fi/service stability; full-composition and
owner-assisted soak remain open

## Authorization and boundary

Jason authorized a Bedroom soak provided the television and sound system could
stay off. The test therefore sent no playback, navigation, camera, volume, mute,
power, CEC, display or audio command. It made no file, service, account,
credential, network, Home Assistant or appliance configuration change.

This is deliberately not the final M11 Bedroom soak. It proves the current
accepted predecessor/content-transport state can remain healthy while the AV
chain is off. Complete-composition deployment, physical equipment/volume
acceptance, reboot and normal-use playback still require their own gates.

## Preflight

- Strict host verification resolved exact hostname `AsterTV-Bedroom`.
- LibreELEC remained nightly `20261021-440640e`.
- Kodi was active, idle and at zero restarts.
- The Wi-Fi stability unit was enabled/active with power saving off.
- Beszel was active at zero restarts.
- The accepted release guard verified 535 files with zero drift.
- Aster Remote was enabled; live and stable client hashes matched:
  - `service.py` `b443edc7…15c3`;
  - `content_session.py` `a85f477b…8acb`.
- Appliance uptime was two days, ten hours and thirty minutes.

## Soak

Twenty fail-fast samples ran every 55 seconds from `06:21:03` through
`06:38:32 UTC`, a 1,049-second (17 minute 29 second) interval. Every sample
required:

- no active Kodi player;
- Kodi, Wi-Fi stability and Beszel active;
- zero Kodi and Beszel restarts; and
- Wi-Fi power saving off.

All twenty samples passed.

| Measure | Observed range |
| --- | --- |
| One-minute load | `0.07–0.50` |
| Available memory | `14,658,200–14,693,852 KiB` |
| Thermal zone | `41–45 °C` |
| Wi-Fi signal | `-56 to -54 dBm` |
| Negotiated transmit rate | `260.0–866.7 Mbit/s` |
| Active players | zero in every sample |
| Kodi restarts | zero |
| Beszel restarts | zero |
| Wi-Fi power saving | off in every sample |

The negotiated transmit rate adapted while idle, but signal, latency, services,
power policy and player state did not degrade.

## Post-soak proof

- The release guard again verified the same 535 files with zero drift.
- Kodi remained active, idle and at zero restarts; Beszel also retained zero
  restarts.
- Kernel journal classification found zero Wi-Fi disconnect, deauthentication,
  timeout, firmware-error or crash lines during the window.
- Kodi's error-priority JSON journal contained zero entries; the earlier
  line-count result was the human-readable `-- No entries --` marker.
- Twenty ICMP probes had 0% loss and
  `1.404/1.946/2.646/0.322 ms` min/average/max/standard deviation.
- Appliance uptime advanced continuously to two days, ten hours and forty-eight
  minutes.

## Result and next boundary

Bedroom passes the headless idle stability slice: strong Wi-Fi, persistent
power-save disablement, stable memory/temperature, clean guard, healthy
monitoring, idle Kodi and no restart while the TV and sound chain stay off.

Still open:

1. exact Bedroom physical equipment-key capture and LG/ARC/eARC/CEC
   volume/mute/power observation;
2. Bedroom-specific content-volume selection and safety tests;
3. full desired-composition deployment rather than the bounded content-only
   slice;
4. reboot persistence of that complete composition; and
5. two normal-use production-path runs with audible playback confirmation.

Machine-readable receipt:
`services/kodi/astertv-fleet/releases/astertv-v3-bedroom-headless-idle-soak-2026-11-06.json`.
