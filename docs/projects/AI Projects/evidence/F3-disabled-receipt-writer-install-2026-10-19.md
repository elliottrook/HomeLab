# F3 retained-receipt writer disabled installation — 2026-10-19

Status: **INSTALLED INACTIVE; EFFECT-ENABLED USE CLOSED**

Jason approved staging the F3 receipt path without invoking it. The platform
owner installed the complete release set on Proxmox and retained all prior
bytes in `/root/aster-f3-receipt-rollback-9e04061e`, root:root mode 0700,
with saved files mode 0600.

## Validation and correction

The initial installation report incorrectly described the release as 11
files and contained two stale source claims. Stream A's independent hash check
found the discrepancy before any receipt was written. The platform lane then:

1. reconciled the inventory to 12 files, including the entrypoint;
2. pinned the deliberate `source_receipts.py` compatibility variant;
3. corrected the `host_exclusion.py` source and prior-installed hashes;
4. reran 46 target-Linux tests against the actual installed directory; and
5. produced clean commits `625505ed` and `df4c7866` whose 12 source hashes
   exactly match the live installed hashes.

The full local suite passed 336 tests with eight expected skips. The installed
modules compile and retain root custody. The retained archive producer remains
`EFFECTS_ENABLED = False`.

## No-effect boundary

The receipt producer was never invoked. The receipt, lease and lock remain
absent; exact-cycle F2 timers remain active; daily F2 timers remain disabled;
F2 services are inactive and its state directory is empty. No daemon reload,
schedule change, production stop or model request occurred.

This closes inactive installation and source provenance only. F3 remains
blocked until F2 succeeds and Jason separately approves one effect-enabled,
current-cycle receipt run. That later action must revalidate the 12 hashes,
current-cycle evidence and rollback before writing anything.
