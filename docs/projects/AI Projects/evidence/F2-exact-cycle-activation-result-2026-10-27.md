# F2 exact-cycle activation result — 2026-10-27

**Decision:** TIMED TEST: GO — SCHEDULED / CONDITIONAL.

Jason explicitly approved the reviewed October 27 activation from platform
commit `9550e53aad222f0a4d45ceb2ae1632a50e93fb3d`. The platform activation
record is commit `019c2cc7b4860308889d67be214672477e96a2f7`.

## Verified activation

| Unit | Trigger | SHA-256 | Observed state |
|---|---:|---|---|
| `f2-preflight-prepare-20261027.timer` | 2026-10-27 01:15 PDT | `7551c94a7b3d367059724aecb7b32863ad341fa9fb39a4ce08b04ea8d760493d` | enabled, active, waiting |
| `f2-preflight-final-20261027.timer` | 2026-10-27 01:20 PDT | `2cdb512508ac4d889c4c1b94fdb6d42d95504cb721b2e450e7ad572b56592cd6` | enabled, active, waiting |

Both installed files are `root:root 0644`, regular and one-link. Unit
verification and calendar resolution passed. No service was manually started;
recurring F2 timers remain disabled and inactive.

The corrected installed coordinator matched `6a1d520a…8193`, its real-default
launcher assertion passed, its focused suite passed 15/15 and the broader
target-Linux suite completed 51/51 with 50 passes and one expected skip. The
new-cycle state, receipt, lease and locks were absent. The October 26 evidence
digest remained `51e296ea…de6`, and all three guests, Aster, accepted
`aster-llama` SYCL, Speech, News timers and Proxmox control daemons remained
healthy after activation.

The one-occurrence `aster-f2-october-27-reconciliation` heartbeat owns the
01:42 observation and spent-unit cleanup. It may not invoke or retry F2.

## Remaining runtime gates

The fresh 00:30 backup, 01:00 TrueNAS task 1, exact archive identities, source
pins, host load, exclusion, lease absence and quiet-host checks still decide
whether the read-only archive checks start. Any failed or uncertain gate is
terminal NO-GO without retry. This activation grants no F3 receipt, lease,
consumer stop, model call or recurring schedule.
