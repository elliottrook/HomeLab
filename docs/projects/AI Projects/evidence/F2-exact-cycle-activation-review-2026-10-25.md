# F2 exact-cycle activation — independent review for 2026-10-25

**Reviewed:** 2026-10-24 America/Vancouver. **Platform source:** full commit
`3b15f8c6412180bf2340c89e293c2e23f82d9912`.

## Candidate

The platform owner prepared two new nonpersistent, date-specific timers only:

| Unit | Exact Vancouver trigger | SHA-256 |
|---|---:|---|
| `f2-preflight-prepare-20261025.timer` | 2026-10-25 01:15 | `5902182e3da484cda6f5fc8503127840aaf752adb36e73d3a521571f3e52b5b8` |
| `f2-preflight-final-20261025.timer` | 2026-10-25 01:20 | `0b6783ab6ae2e8625d48730cd8e5c2858cee9df9e619f62a9e55d77a0d00eeed` |

Both use one-second accuracy, zero randomized delay and `Persistent=no`. They
target the existing prepare/final services and do not create a recurring
schedule.

## Independent target check

- Clean committed bytes match both card hashes.
- Target `systemd-analyze verify` accepted both units.
- Target calendar parsing resolved exactly to 01:15 and 01:20 PDT on October
  25 (08:15 and 08:20 UTC).
- Installed diagnostic source hashes match the approved `770107df` correction;
  both are `root:root 0644`.
- The October 25 terminal state, cooperative lease state/lock and trusted F2
  receipt are absent.
- Recurring prepare/final timers are absent and inactive.
- Temporary validation files were removed; neither candidate was installed or
  enabled during review.

## Decision boundary

The candidate is ready for one separate activation approval. Activation may
install and enable only these two timer units, without manually starting a
service. A one-occurrence observation-only reconciliation at 01:42 must clean
up the spent units and report the terminal state. Fresh backup/task-1, load,
lease, exclusion, process, source-pin and snapshot gates still fail closed at
runtime. No receipt, lease, production stop, model call, F3 or same-cycle retry
is authorized.
