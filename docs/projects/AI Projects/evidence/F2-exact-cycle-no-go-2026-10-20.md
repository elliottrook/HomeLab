# F2 exact-cycle result — 2026-10-20

Status: **NO-GO; no archive scan result; no retry**

## Observed result

The exact-cycle timers fired at their intended Vancouver times, but the slow
preparation did not complete:

| Unit | Start | End | Result |
|---|---|---|---|
| `f2-preflight-prepare.service` | 01:09:00 PDT | 01:09:05 PDT | exit 1 / failed |
| `f2-preflight-final.service` | 01:10:00 PDT | 01:10:00 PDT | exit 1 / failed |

The root-custodied terminal state is schema `aster-f2-scheduled.v1`, cycle
`2026-10-20`, phase `final`, state `no_go`, error class
`ScheduledF2Error`. It contains no archive rows. The preparation snapshot
directory contains no file. The final coordinator therefore had no exact
prepared state from which it could admit the observer.

The specific preparation sub-gate is **UNKNOWN**. Both services deliberately
discard standard output/error, and the final run replaced the earlier
content-free preparation state with a generic final error. Systemd retained
only the exit status. It would be a hallucination to name backup, TrueNAS,
archive identity, load, pin or another individual preflight check as the
cause. This diagnostic-loss behavior must be corrected and tested offline
before another cycle is considered.

## Safety and production postcheck

- no `zstd`, F2 coordinator or F2 observer process remained;
- whole-host and application-B60 lease/lock paths were absent and the lease
  helper reported `ready`;
- no current trusted receipt was found;
- Aster Agent, accepted llama.cpp and Aster Speech were active;
- both News timers were active and enabled;
- `pvescheduler` and `pvestatd` were active;
- the two spent exact-date timers were stopped and disabled;
- the old daily F2 timers remained disabled.
- the one-occurrence Codex observer automation was paused after reconciliation.

No service was stopped, no model was called, and no receipt, lease, full-stop
drill or A1 run followed.

## Decision and next safe action

F2 remains failed/unmeasured for the October 20 cycle. F3 effect-enabled use,
F4 and the full-stop drill remain blocked. Do not retry this cycle.

The platform owner should preserve the first failing phase and a bounded
failure-class code so the final gate cannot overwrite the preparation cause,
then pass offline and target-Linux regression tests. A later scan needs a
fresh exact-cycle card and approval after that correction; a calendar slot
alone is not sufficient.

