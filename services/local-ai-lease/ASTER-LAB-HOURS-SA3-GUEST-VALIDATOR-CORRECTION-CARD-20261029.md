# SA3 guest validator correction — inactive installation card

Status: **source-complete correction; no workload effect**

The first independent post-install invocation exposed a namespace error: the
inactive validator tried to read the four evaluation files on Proxmox, while
the reviewed dormant installation correctly placed them inside LXC110. It
failed closed before any booking, lease, drain or model request.

This correction replaces exactly two Proxmox files against their installed
hashes:

| Target | Existing SHA-256 | Corrected SHA-256 | Mode |
|---|---|---|---|
| `lab_hours_inactive_target.py` | `f670077ec2be3001058c8a7f18b8da55e5f717422305c400afd97350bc7cefab` | `fd467544649cc877ca06f831d8f84aaca495416c19072256bd228fc11601ae33` | `0644` |
| `lab_hours_release_manifest.json` | `7aa4a8c1d04d0e208b0cc732931592c94a6e49e18e3a1bdaf52c1532d7ff2c14` | `51a9cd3a450710ad755cf924aef0df6e900edcf6cca2db4cffe054cb2437f74c` | `0644` |

The corrected validator has no arbitrary command or guest selector. It invokes
a fixed read-only Python verifier through `pct exec 110`, passes only the four
hash pins from the registered workload on standard input, verifies root-owned
single-link regular files and local import closure inside the guest, and still
requires the target service/timer to be absent on Proxmox.

The installer checkpoints both old files under the fresh root-only identity
`sa3-guest-validator-v1`, writes atomically, verifies manifest closure, invokes
the corrected no-effect validator and rolls back both files on any failure.
The combined focused suite passes 29/29. Two independent bundle builds match
SHA-256 `cc4673fb5cb8841f935b9e31978bc194f2f84f250bf082ff9f657e63332a4f3e`.

This correction creates no booking, reservation, lease, lock, attempt, model
request, drain, service, timer, schedule, routing, model change or restart.
