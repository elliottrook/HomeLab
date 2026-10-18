# F2 diagnostic phase — disabled target-Linux release candidate

**Status: HOLD / source-only.** This card is not approval to install, replace
the guard, start a scan, enable a timer, acquire a lease, write a receipt or
change a schedule. The October 17 one-cycle approval is consumed and remains
FAILED/UNKNOWN.

## Purpose and safety boundary

The candidate adds only a content-free failure phase to a future guard result:
`preflight`, `observer`, or `result`. It emits no child output, archive path,
exception text or receipt content. It preserves fail-closed behavior and does
not identify the exact failed predicate. The synthetic replay denies each
preflight gate without launching a child.

## Pins

| Artifact | Candidate SHA-256 | Future target path / mode |
|---|---|---|
| Diagnostic guard source | `6d18f9c88067edb11a04eae84d7c5fb3f0d3f4eb518b359f57277205539f3a2f` | `/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py`, root:root `0644` |
| Focused test source | `1582fb7ffc9ed3a851ce0346cc0fc727a6550759e3537c261eabd1c60c2459d6` | private stage only |
| Existing manual controller | `67ca223d03a4922603f570c6db87fed919879aedf3706e586b2684f7be84073c` | unchanged dependency |
| Existing observer | `f07071d3544fafd0579a4e360674664ec95dd32bd2c4114c3e073c849805e363` | unchanged dependency |
| Existing producer | `5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb` | unchanged dependency |
| Host exclusion | `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` | unchanged dependency |
| Retained-integrity runtime | `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` | unchanged dependency |
| Fixed-source runtime | `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9` | unchanged dependency |

The currently installed guard old bytes must be rechecked immediately before
any future stage; the documented prior disabled-install pin is
`d50ee2207bc4185db266ad01af540b9b719397dec3855ee579ee18f983a3535d`. Drift
is a hard stop. The candidate has no timer and must remain effect-disabled.

## Offline evidence

- Focused diagnostic suite: 14 passed.
- The replay matrix covers one denial each for the start window, installed
  custody, lease/receipt absence, host quietness and TrueNAS state; every case
  proves no observer child launch.
- Complete `scripts/local-ai` suite: 219 passed, 4 expected macOS
  root-custody skips.
- No archive, `zstd`, TrueNAS task, lease, receipt or service was contacted.

## Required target-Linux stage before any scan consideration

1. Obtain a new bounded approval for staging only. Copy the pinned guard and
   test into a new root-owned mode-0700 private directory; do not copy an
   archive, receipt or secret.
2. Recheck every installed dependency hash/mode/owner, fixed schedules,
   inactive timers, no lease/receipt, running guests and unchanged backup and
   News schedules. Run imports and the 14 focused synthetic tests only.
3. If a disabled host replacement is later approved, checkpoint the exact old
   guard bytes root-only, atomically replace only that one file, verify the
   candidate hash and rerun the synthetic tests. Do not invoke
   `--read-only-authorized`.
4. On any mismatch, failed test or uncertain write, restore only the old guard
   bytes and verify the old hash. If a scan or lease exists, do not swap code;
   stop for operator reconciliation.

A later scan needs a separate fresh-cycle approval, current backup/TrueNAS
preflight, quiet host and lease evidence. This card never authorizes a retry
of October 17.
