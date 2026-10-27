# F2 repeated overnight failure analysis and daytime mitigation — 2026-10-27

## Decision

**NO-GO for another exact-date activation until a daytime installed-path
rehearsal passes twice.** The October 28 timer candidate remains technically
reviewed, but scheduling it now would repeat the failed process of using the
overnight window as the next integration test.

## Measured pattern

The failures from October 20 through 27 were different deterministic defects,
revealed one layer at a time:

| Cycle | First preserved failure |
|---|---|
| October 20 | preparation detail overwritten and service output suppressed |
| October 21 | preflight required a future LXC110 mirror state |
| October 22 and 24 | final-guard failures collapsed to a generic class |
| October 25 | stale installed `host_exclusion.py` pin |
| October 26 | default launcher used `subprocess.run` but called Popen-only `communicate()`; the test injected a Popen-shaped fake |
| October 27 | child returned a bounded failure projection, but the coordinator checked its nonzero exit before parsing the phase |

This is an integration-test gap, not evidence of random backup timing. Each
narrow correction passed the tests immediately around it, but the exact
installed coordinator/child/producer chain was not exercised below the real
subprocess boundary before the next overnight activation. Fail-closed error
projection then hid the next defect, limiting diagnosis to one layer per day.

## Current-cycle replay

A read-only source replay used the preserved current-cycle Proxmox inventory,
job, guest-completion logs, whole-job journal and TrueNAS task state. A
synthetic 01:20 clock and a controlled sentinel below the archive probe reached
the first probe boundary. This proves those prerequisite checks accepted the
October 27 evidence. It does not claim an archive integrity result and does
not reproduce the exact historical load/process state.

The October 27 final child exited nonzero in about four seconds with zero
archive rows, which is consistent with a failure at or immediately below the
observer/probe boundary. The preserved evidence is insufficient to name a
more specific cause without speculation.

## Mitigation candidate

Platform source commit `28edce6d628496023875e17a5680a7682b3262c0`
adds a diagnostic-only daytime rehearsal. Platform commit `2d167ca0` freezes
its bounded inactive-install/run card. The rehearsal:

- starts a real child with `Popen.communicate()`;
- uses the production producer and current-cycle fixed sources;
- validates all three archive identities, sizes and deadline calculations;
- substitutes only the `zstd` probe and receipt writer;
- cannot be accepted as F2/F3 evidence; and
- reports explicitly that no archive scan or receipt occurred.

The new real-process transport test and existing F2 suites pass 57/57 locally.
The next action is one reviewed inactive installation followed by two daytime
target runs. A mismatch is corrected during the day. Only two matching passes
make a later exact-date activation approval-ready.

No timer, scan, receipt, lease, service stop, restart or model call is approved
by this analysis.
