# AsterTV v3 M10 — Beszel appliance monitoring

Date: 2026-11-05

Status: Bedroom, Family and Jen up

## Design

The LibreELEC clients use Beszel 0.18.7's outbound hub connection to the
existing private hub at `192.168.20.20:8090`. No inbound firewall rule or
appliance listener exposure was added. Each client has an independently
revocable 40-character enrollment token in a mode-`0600` environment file;
tokens never entered Git, command output or evidence.

The new `beszel-client-v1` composition overlay owns only the host-bound systemd
unit and the pinned agent contract. Its unit selects the exact appliance
hostname, requires the private environment file and binary, and carries the
existing hub's public SSH key. The external x86-64 glibc binary is pinned to
Beszel 0.18.7 SHA-256
`99e7f48d…f3158`, matching both the official immutable release asset and the
already deployed fleet binary.

## Transaction and deployment

Before inserting records, the live PocketBase SQLite database was backed up to
`/opt/beszel/backups/astertv-m10-before-20261105.db`, mode `0600`; both backup
and live `integrity_check` returned `ok`. A later Family enrollment retained a
second pre-change checkpoint at
`/opt/beszel/backups/astertv-m10-family-before-20261105.db`. Immediate
transactions created only `AsterTV Bedroom` (`192.168.1.140`), `AsterTV Family`
(`192.168.1.157`) and `AsterTV Jen` (`192.168.1.180`) plus their
fingerprint/token rows. The registration helper is idempotent and refuses
name/address conflicts.

Bedroom was installed and validated first. An initially malformed quoted
public-key assignment caused the service to fail closed before connection; the
unit renderer and its regression test were corrected, then only the agent was
restarted. Bedroom reported `up` before the identical contract was installed
on Jen. Family was enrolled only after its live Ed25519 identity, hostname,
hardware serial, MAC and address independently matched the pinned fleet
record. Kodi was never restarted for monitoring enrollment.

All transient enrollment files were removed from LXC 100, Proxmox and the
administration workstation after each persistent client file was installed.

## Validation and exclusions

- Bedroom, Family and Jen agents are enabled and active;
- Beszel reports all three systems `up` with populated metrics;
- all binaries match the pinned SHA-256 and all private environment files
  remain mode `0600`;
- Kodi remains active on all appliances;
- composition guards include the unit payload plus service, binary and
  credential-mode assertions and report every deployed device clean.

Beszel owns host resource history and availability only. Existing Doctor and
service-native checks retain application drift and functional failure
ownership; no duplicate alert was added.

## Rollback

Stop and disable only `beszel-agent.service` on the affected client, remove its
unit, pinned binary and private environment file, then delete only that
system/fingerprint pair from Beszel in one checked transaction. Restore the
database checkpoint only if targeted record rollback cannot preserve unrelated
monitoring history.
