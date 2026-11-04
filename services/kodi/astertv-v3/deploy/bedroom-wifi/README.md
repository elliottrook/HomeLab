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
`iw dev wlan0 set power_save on`.

## Installed evidence — 2026-11-04

- target: `AsterTV-Bedroom` (`192.168.1.140`)
- unit SHA-256: `6a829d42832076bb8ec2756c5cd577939af8ab0a900462376c5dbb98ab1f6b90`
- checkpoint:
  `/storage/.aster-checkpoints/astertv-bedroom-wifi-AsterTV-Bedroom-20261104-1241`
- service: enabled and active
- Kodi: remained active; it was not restarted
- power saving: off
- post-install latency: 20/20 received, average 2.244 ms, maximum 4.974 ms

The approved reboot check completed at 2026-11-04 12:50 local time. After a
14-second boot, the unit was enabled and active, power saving was off, Kodi was
active, and 20/20 packets returned at 4.085 ms average / 35.617 ms maximum.
Boot persistence therefore passes. The same reboot exposed an unrelated stale
release-guard unit whose `%H` expanded to `LibreELEC`; its 535-file accepted
manifest independently verifies clean when addressed as `AsterTV-Bedroom`.

The approved bounded repair replaced only that unit with the checked-in literal
host version. Its SHA-256 is
`5839efc05f743c17f1cacf8397702deb77414e6f5d5c60f65701355392c5be65` and
its checkpoint is
`/storage/.aster-checkpoints/astertv-bedroom-release-guard-AsterTV-Bedroom-20261104-guardfix`.
The one-shot then completed with `Result=success` / `ExecMainStatus=0`; the
accepted-manifest hash remained `474c887d…f204`, all 535 files remained clean,
Kodi stayed active, Wi-Fi power saving stayed off and no systemd units remained
failed. Rollback is to restore `astertv-release-guard.service.before` from that
checkpoint and run `systemctl daemon-reload`; doing so deliberately restores
the diagnosed boot failure and is for recovery inspection only.

The two machine-specific settings are release-safe by construction:

- the Wi-Fi unit lives in `/storage/.config/system.d`, outside the release
  guard's seven add-on roots under `/storage/.kodi/addons`, and ordinary
  releases neither snapshot nor remove it; and
- the reliability installer validates the client hostname and renders that
  literal identity into the boot unit. It never leaves systemd's early-boot
  `%H` token in an installed unit.

`test_wifi_service.py` gates both boundaries. The checked-in
`astertv-release-guard-bedroom.service` is the exact host-bound recovery unit
used for the one-time live repair; future reliability installs must render the
same `--host AsterTV-Bedroom` argument.

The Mac's stale `.140` host-key entries were separately corrected after the
live ED25519 fingerprint matched the previously approved
`SHA256:CFJcdaUaL72BX/yg6wsxksJs6UXSSDpnXQuWVTco61c`. Recovery copy:
`/Users/jelliott/.ssh/known_hosts.astertv-bedroom-20261104`.
