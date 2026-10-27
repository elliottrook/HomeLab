# F3 from F2 exact-cycle effect review — 2026-10-28

## Decision

**CONDITIONAL GO under Jason's October 27 daytime-to-tonight authorization.**
Platform commit `d9ae516f` may convert the October 28 F2 result exactly once,
only after the 01:42 reconciliation accepts three exit-zero rows and removes
the spent exact-date timers.

The card pins the installed converter `64b325da…3421`, backup adapter
`26a7741b…8a2f`, corrected coordinator `efe8bc99…87ec` and integrity verifier
`11b536ed…54a5`. All installed hashes and root custody match. The focused
converter/card suite passes 10/10 locally and 10/10 on target Linux.

The effect writes one root-owned retained receipt without rescanning an
archive. It fails closed if F2 is incomplete, stale, changed or uncertain; if
the receipt already exists; if any timer, lease, lock, process, source,
schedule or production gate differs; or if independent verification fails.
There is no retry. Preserve all uncertain evidence.

This review does not authorize F4, a lease, service stop, restart, model call
or automatic promotion. F4 requires a subsequent fresh cycle and effect gate.
