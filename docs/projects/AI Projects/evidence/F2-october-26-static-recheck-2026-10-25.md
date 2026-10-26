# F2 October 26 static recheck — 2026-10-25

> Result: **STATIC PASS; TIMED TEST REMAINS SCHEDULED / CONDITIONAL**

At 10:18 PDT, Stream A independently re-read the installed October 26 F2
schedule and source boundary. This was observation only. No service was
started, no archive was scanned and no lease or receipt was created.

## Observed state

- `f2-preflight-prepare-20261026.timer`: enabled, active and waiting for
  2026-10-26 01:15 PDT; installed SHA-256
  `e356915e419afa6199afa86bd997231b1d48c2a2e9f46356069d8ee5ce4788fe`.
- `f2-preflight-final-20261026.timer`: enabled, active and waiting for
  2026-10-26 01:20 PDT; installed SHA-256
  `fd05327676d3a5dc9383d23ca747b81be7dba1dfb88fe39a2ee535679bc6a8f4`.
- The five installed source hashes match the activation card:
  `e61b7de…a5c34`, `3011c419…c858`, `b39680d5…3b61`,
  `6340c29e…c684` and `9efe6e5d…e8a1`.
- The October 26 terminal-state file, cooperative lease, cooperative lock and
  trusted archive receipt were absent.
- The general lease status remained `ready`; Aster Agent, accepted llama.cpp
  SYCL and Speech were active in the adjacent read-only health check.

## Decision

The static release has not drifted. F2 is still conditional on the future
00:30 backup, 01:00 TrueNAS pull, exact archive identities, quiet-host checks
and absence gates at execution time. A failed or uncertain fresh gate must
produce NO-GO without retry. Only three independently reconciled exit-zero
archive rows can complete F2 and open the later F3 decision.

## Late preflight

A second read-only check at 22:46 PDT found the same two timer and five source
hashes exact. The date-specific timers were enabled, active and waiting for
01:15/01:20; recurring timers were disabled and inactive. The October 26 state,
archive receipt, cooperative lease and lock remained absent, and the general
lease reported `ready`. LXC104/110/116 were running; Aster Agent, accepted
llama.cpp/SYCL, Speech, `pvescheduler` and `pvestatd` were active. No archive
scanner or F2 runner was active. The result remains **TIMED TEST: GO —
SCHEDULED / CONDITIONAL**; only the runtime backup, TrueNAS, archive identity,
load and exclusion checks remain fresh gates.
