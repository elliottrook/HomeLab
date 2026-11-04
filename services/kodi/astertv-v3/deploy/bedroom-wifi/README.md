# AsterTV Bedroom Wi-Fi stability

This bounded Stream M repair disables 802.11 power saving on Bedroom's `wlan0`
after networking is online and before Kodi starts. It is host-bound to
`AsterTV-Bedroom`; it does not alter the Wi-Fi profile, password, DHCP
reservation, Kodi, audio or media configuration.

Evidence before installation on 2026-11-04:

- Intel Wireless-AC 9560, `-54 dBm`, 866.7 Mbit/s transmit link;
- power saving enabled;
- 20/20 packets received, average 107.540 ms, maximum 211.173 ms; and
- no repeated driver disconnect or reboot evidence.

A volatile `power_save off` trial produced 20/20 packets received, average
2.440 ms and maximum 4.973 ms. The persistent unit is therefore limited to
reapplying that proved runtime setting at boot.

Rollback is `systemctl disable --now astertv-wifi-stability.service`, removal of
the unit and candidate, `systemctl daemon-reload`, then
`iw dev wlan0 set power_save on`. A reboot test remains required to prove boot
persistence after the initial non-disruptive installation.

## Installed evidence — 2026-11-04

- target: `AsterTV-Bedroom` (`192.168.1.140`)
- unit SHA-256: `6a829d42832076bb8ec2756c5cd577939af8ab0a900462376c5dbb98ab1f6b90`
- checkpoint:
  `/storage/.aster-checkpoints/astertv-bedroom-wifi-AsterTV-Bedroom-20261104-1241`
- service: enabled and active
- Kodi: remained active; it was not restarted
- power saving: off
- post-install latency: 20/20 received, average 2.244 ms, maximum 4.974 ms

The Mac's stale `.140` host-key entries were separately corrected after the
live ED25519 fingerprint matched the previously approved
`SHA256:CFJcdaUaL72BX/yg6wsxksJs6UXSSDpnXQuWVTco61c`. Recovery copy:
`/Users/jelliott/.ssh/known_hosts.astertv-bedroom-20261104`.
