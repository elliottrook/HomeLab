# M3 35B Lab Hours admission correction — 2026-10-29

## Observed failure

Booking `aster-stream-a-m3-35b-20261029-1500` was claimed exactly at its
scheduled start and immediately failed closed with phase `claim` and code
`WORKLOAD_RUNNER_NOT_REGISTERED`. Its bounded terminal record states
`production_restored=true`. No attempt record, lease, service stop, model mount,
guest restart or model request was created.

The registered workload and command builder both name runner kind
`m3-joint-semantic-35b`, but the final admission allowlist in
`lab_hours_reserved_runner.py` still contained only the three older runner
kinds. The inactive installation tests validated registry and command
composition separately and therefore missed the joined admission decision.

## Correction

The runner kinds now have one named immutable allowlist used by the live
admission check. It includes the exact registered M3 runner kind. A regression
resolves `m3-joint-semantic-35b-public-v1` through the workload registry and
requires that resolved kind to be admitted. The release manifest is repinned to
the corrected runner.

This correction does not alter the workload, model, runtime, thresholds,
booking rules, recovery order or automatic-routing state. Installation replaces
only the runner and release manifest while inactive, with a root-only rollback
checkpoint. It does not create or retry a booking and performs no model or
service effect.
