# AsterTV v3 M10 — Family operations and isolated restore

## Outcome

AsterTV Family is now reconciled in NetBox, Beszel and fleet Doctor. Its live
Ed25519 identity matched the pinned key before any mutation; hostname,
Bosgame Ecolite model/serial, DNB20 board identity, Ethernet MAC
`84:47:09:a1:d3:55` and `192.168.1.157/24` agreed with independent appliance
and OPNsense observations.

NetBox registration is exact and idempotent: device 26, interface 23, MAC 27
and IP 39. The protected pre-change PostgreSQL dump is
`/root/astertv-checkpoints/netbox-before-astertv-family-20261105.sql`, SHA-256
`23e50529ff97d3502da97e514fe8675d8b0c4f7e7422591634c0cce01cd8a805`.

Beszel 0.18.7 reports **AsterTV Family** `up` with populated metrics. Its agent
binary and host-bound unit match the fleet hashes, the environment is mode
`0600`, Kodi remained active, and all transient token copies were removed.

## Composition transaction and recovery

The first Family composition transaction exposed an unsupported typed
`pulseaudio.masked` assertion. The runner automatically restored every
checkpointed file, the predecessor accepted state and release-guard boot edge;
Kodi restarted, and the original 533-file release verified clean. The runner
now maps masked assertions to the real systemd unit, checkpoints/restores the
masked state, and has a dedicated regression test.

The corrected transaction checkpoint
`/storage/.aster-checkpoints/astertv-platform-m10-family-r2-20261105`
reconciled only eight declared payload or mode differences. The accepted
composition is `5959c121ad682d761653af3a6bca465b5a90bb37598bea5ee98c01ac75d2c6e1`.
All 36 payloads, 30 typed assertions and nine dependencies pass; the release
guard is enabled and clean, Kodi and Beszel are active, and fleet Doctor reports
Bedroom, Family and Jen clean.

## Isolated restore proof

The hash-bound Bedroom and Family bundles were each installed into a disposable
root. The rehearsal then corrupted one package member, removed a second,
changed a third member's mode and damaged both accepted-state directories.
Rollback restored every byte, mode and accepted-state marker:

- Bedroom: 26 payloads, composition `a927073cb6009611519b3dc18f39607acd9e0f34f4843be322e5b816fe946d5c`;
- Family: 36 payloads, composition `5959c121ad682d761653af3a6bca465b5a90bb37598bea5ee98c01ac75d2c6e1`.

The disposable roots were removed automatically. No credential, profile,
database, household value or media content entered the fixtures. Together with
Jen's earlier live rollback/reinstall proof, all three deployed appliances now
have recovery evidence.
