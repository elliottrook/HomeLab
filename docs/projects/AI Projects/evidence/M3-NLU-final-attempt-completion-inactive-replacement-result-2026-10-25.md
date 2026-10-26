# M3 NLU final-attempt completion inactive replacement result — 2026-10-25

Status: **PASS — CORRECTED PACKET INSTALLED INACTIVE**

Jason approved the exact one-file replacement in
[the frozen card](M3-NLU-final-attempt-completion-inactive-replacement-card-2026-10-25.md).
The transaction completed at 2026-10-26T06:21:55Z.

## Result

- Installed runner SHA-256:
  `88af8eb7f196c03563a31ed2c2fe513d054d491c4903ba4c29dfd765dba36ca0`.
- Packet-manifest SHA-256:
  `835bcb55ba93d25427b322c6cf93aee06cba1b5e7221af7fb63dbd41d1aab114`.
- Exact predecessor `a8cca4da…5a0f` is retained in the root-only checkpoint
  `/var/lib/aster-nlu-calibration/checkpoints/completion-0e4b7311-20261026T062155Z`.
- The corrected manifest independently validated all 11 staged files, totalling
  99,633 bytes, under root-only custody.
- All 17 target-Linux runner regressions passed, including final-case transport
  and engine failures failing closed.
- The target import check passed with bytecode writes disabled.

Independent postchecks found exactly the eleven expected regular files. The
runner is root:root mode `0600` with one hard link. `run.json`,
`attempt-journal.jsonl`, `__pycache__` and a runner process are absent.
`aster-llama.service` is active/running with zero restarts and the lease is
`ready`.

Both October 26 F2 timers remained active. The current-cycle F2 state, lease
and lock were absent. No model call, service restart, lease acquisition,
threshold selection, holdout access, route change or F2 invocation occurred.

This closes the inactive NLU packet correction. It does not release live
calibration. The platform's current-packet F6 activation/recovery card must pin
this runner and packet-manifest digest before review.
