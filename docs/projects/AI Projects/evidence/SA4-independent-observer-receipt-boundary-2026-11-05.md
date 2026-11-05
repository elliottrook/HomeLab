# SA4 independent observer receipt boundary — 2026-11-05

## Result

The source-only SA4 evidence chain now has a separately authenticated,
content-free independent-observer layer for both postchecks and rollback.
Operation-owner terminal JSON is not sufficient to claim either result.

The postcheck receipt binds the exact plan, admission, claimed grant, operation
terminal, compiled target registration and ordered three-program check set. It
requires a bounded observation time, one-link root target snapshot, absent
temporary file and the exact operation lock owner. Pass, fail and uncertain
rows are retained distinctly.

The rollback receipt additionally binds the triggering postcheck receipt,
checkpoint, compiled rollback program and rollback attempt. A complete
observation requires restored bytes, distinct retained checkpoint metadata,
absent temporary file and a passing consumer-health observation. Failed or
uncertain evidence requires manual reconciliation and never permits retry.

Both receipts require an RSA-2048/SHA-256 detached proof from a compiled
observer key. The real observer registry is deliberately empty. Tests use a
synthetic key and prove signature, order, program, registration, timing,
snapshot, duplicate-key and rollback-lineage failures close safely. Even a
complete synthetic receipt returns `effect_outcome_accepted=false` and
`maximum_effects=0`; the existing v1 reconciler remains unchanged and cannot
accept an effect.

The expanded SA4 suite passes **43/43**. No target, observer key, checkpoint,
measurement, repair, rollback, restart, deployment, route or authority was
created.

## Source identities

- independent receipt validator:
  `d2729ea133d79a64558e995f9bf7c667b578385b14419d3875822f64aaa8a306`
- adversarial tests:
  `2ccad30abea9fe905db04581f8a4d686a9464453ffb6414c761ef9f3e6af7cd6`

## Remaining gate

Next is the inactive measurement owner and a new effect reconciler that binds
these receipts to the one-use ledger while still accepting no production
effect until a real target and distinct real keys are reviewed and installed.
The first repair effect remains separately and immediately owner-approved.
