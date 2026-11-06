# AsterTV v3 M10 — Bedroom NetBox reconciliation

Date: 2026-11-05

Status: complete; Family deliberately unchanged

## Verified identity

Two independent read-only sources agreed on Bedroom's active Wi-Fi identity:

- appliance: `AsterTV-Bedroom`, HP ProDesk 400 G5 Desktop Mini, serial
  `MXL0153FGS`, `wlan0` `58:96:1D:DF:DC:FC`, `192.168.1.140/24`;
- OPNsense ARP/reservation state: the same address and MAC on Trusted VLAN 10.

NetBox already contained the `192.168.1.0/24` Trusted prefix, VLAN 10, Mini
Atlas site and Media Client role. It had no conflicting device, serial, MAC or
address. Family remained blocked because its SSH identity and chassis/serial
facts were not independently verified; it was not changed.

## Recovery and change

Before the write, LXC 111 had 27 GiB free. A mode-0600 PostgreSQL checkpoint
was created at
`/root/astertv-checkpoints/netbox-before-astertv-bedroom-20261105.sql`:

- bytes: `1,070,897`;
- SHA-256:
  `a00f406e01ca96ae2222b60b216c7529ecaa9a343f751e941186623929b6b3f1`.

`services/kodi/astertv-v3/m10/register_bedroom_netbox.py` then used one Django
transaction to create only:

- HP manufacturer and HP ProDesk 400 G5 Desktop Mini device type;
- device 25, active Media Client at Mini Atlas HomeLab;
- Wi-Fi 5 interface 22;
- MAC record 26; and
- IP record 38 with primary address and private DNS name.

The bounded script supports only `check`, `apply` and exact-identity
`rollback`. Rollback refuses a changed serial, MAC, interface or address and
removes the newly created manufacturer/device type only when unused.

## Validation

A schema-restricted readback returned the exact model, serial, role, site,
interface type, MAC and primary address. A second script run was idempotent and
reported `already-present` with the same object IDs. No appliance, firewall,
DHCP, DNS, monitoring service or Family record changed.

At clean commit `24da9d2df1ac6e6310027164e093c8da69fa4c2a`, two full
M10 runs were byte-identical at SHA-256
`b93db1b2a103dc51a3ed8e3b9ee4a04d6aaafa5e3219c12f436af17cb15f883c`.
All 52 local test files passed, 93 candidate inputs scanned clean and the
operational-readiness projection retained the 11 remaining gaps.
