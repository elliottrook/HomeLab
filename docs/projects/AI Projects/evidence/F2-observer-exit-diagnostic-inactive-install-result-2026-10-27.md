# F2 observer-exit diagnostic inactive installation — 2026-10-27

**Decision:** PASS. No timed cycle is scheduled.

Jason approved the one-file inactive installation from platform commit
`be6cafa47d77668a69181a80018a755d6f740840`. Read-only prechecks matched the
installed predecessor `6a1d520a…8193`, root custody, preserved October 27 state
digest `cf72cfbd…5d2a`, disabled/inactive recurring timers and ready lease.

The first clean test archive omitted repository card and systemd fixtures.
Focused target tests passed 31/31, the broader suite reported only missing-file
errors, and the transaction automatically restored the exact predecessor.
Read-back verified that rollback before the retry. The corrected complete
packet then passed:

- 31/31 focused coordinator and observer tests;
- 56/56 complete F2 target-Linux tests; and
- 4/4 direct checks against the installed projection function.

The installed coordinator now has SHA-256 `efe8bc99…87ec`, root:root mode
`0644` custody and one regular link. The predecessor remains at
`/root/aster-f2-observer-exit-rollback-be6cafa4/`. The preserved October 27
state digest is unchanged.

Postchecks found all F2 timers disabled/inactive, no F2 or `zstd` child, no
retained receipt, lease or operation lock, and healthy LXC104/110/116, Aster
Agent, accepted LXC110 llama.cpp/SYCL, Speech, `pvescheduler` and `pvestatd`.

This installation makes a future child failure distinguish preflight, scan and
result phases. It cannot reconstruct October 27 and authorizes no timer, scan,
F3 conversion, receipt, lease, service stop, restart, model call, schedule
change or Git push.
