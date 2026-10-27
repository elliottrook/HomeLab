# F2 exact-cycle activation result — 2026-10-28

**TIMED TEST: GO — SCHEDULED / CONDITIONAL.**

Jason authorized using the day to reproduce and fix the repeated F2 failures,
perform a real archive scan, and test the stable candidate against tonight's
fresh backup. Platform source `f2022140` binds the corrected installed path.

Before activation:

- the corrected installed hashes and root custody matched;
- 63/63 target tests passed;
- the installed no-scan rehearsal resolved all three current archives;
- the October 28 state, lease, locks and retained receipt were absent; and
- LXC104/110/116 and Proxmox daemons were healthy.

The exact one-shot prepare/final timers are enabled, active and waiting for
01:15/01:20 PDT. Their hashes remain `69d0e4d2…a843` and
`b71e87d0…5545`. Recurring F2 timers remain disabled/inactive. No scan, receipt
or lease occurred during activation.

Automation `aster-f2-october-28-reconciliation` is active once at 01:42 for
observation and spent-unit cleanup. Runtime backup, TrueNAS task 1, exact
archive identity, load and quiet-host gates remain fresh and fail closed, with
no retry.
