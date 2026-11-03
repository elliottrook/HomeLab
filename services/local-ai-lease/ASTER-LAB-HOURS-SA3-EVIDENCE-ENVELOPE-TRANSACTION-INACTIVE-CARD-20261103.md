# SA3 evidence-envelope transaction inactive installation card — 2026-11-03

Status: **CORRECTED SOURCE-COMPLETE; FIRST INSTALL ROLLED BACK**

The first approved install failed closed at the guest import check because the
new wrapper imported an older SA3 wrapper that is installed as a fixed
executable rather than an importable runtime module. Host and guest rollback
completed, all production services remained active and both failed-attempt
checkpoints were retained.

The corrected wrapper is self-contained and pins the accepted model, binary,
runtime files, listener command, ephemeral key and cleanup boundary directly.
The corrected transaction adds two dormant Proxmox modules, one dormant LXC110
wrapper and a release-manifest replacement. It retains root-only host and guest
checkpoints, requires the exact current manifest baseline and absent new
targets, installs atomically, validates imports and all release pins, and rolls
back on failure or uncertainty.

The effectful registered runner is deliberately unchanged, so the new workload
continues to fail closed with `WORKLOAD_RUNNER_NOT_REGISTERED`. No unit,
booking, schedule, lease, lock, model request, service stop, restart, route,
repair or promotion is included. The combined transaction/install and
inherited Lab Hours suite passes 58/58. The correction uses the fresh
`sa3-evidence-envelope-transaction-v2` checkpoint and bundle identity; it does
not overwrite or remove the failed v1 evidence.

Installation requires a separate approval after deterministic bundle hashes
and live baselines are revalidated. Target-Linux proof must complete before a
runner activation candidate or reservation-ledger query is considered.
