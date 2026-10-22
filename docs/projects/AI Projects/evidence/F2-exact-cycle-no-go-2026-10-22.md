# F2 exact-cycle result — 2026-10-22

## Decision

**NO-GO / UNMEASURED.** The approved October 22 cycle did not produce an
archive scan or any archive result row. It cannot advance F2 or F3 and must
not be retried in this backup cycle.

## Bounded terminal evidence

- the 01:15 prepare timer fired; its service exited successfully after five
  seconds and wrote an exact-cycle prepared state;
- the 01:20 final timer fired; its service exited `1` after one second;
- the retained terminal state is schema `aster-f2-scheduled.v1`, cycle
  `2026-10-22`, state `no_go`, first failure phase `final`, failure class
  `FINAL_FAILED`;
- the final state contains no result projection and therefore no archive row;
- the prepared snapshot recorded verified archive identity and a ready lease,
  but the suppressed final service output and the coarse `FINAL_FAILED` class
  do not identify which final-guard subcheck failed; and
- no claim is made about archive integrity because the scanner did not run.

## Postcheck and cleanup

No F2 or archive-scanner child remained. No lease state, lease lock or trusted
receipt existed. LXC104, LXC110 and LXC116 were running; Aster Agent,
`aster-llama`, Speech, `pvescheduler` and `pvestatd` were active. The two spent
October 22 timer units were stopped, disabled and removed, followed by a
daemon reload. The recurring F2 timers remain disabled and inactive.

## Consequence and next action

F2 remains open and F3 remains blocked. Production is normal. The next safe
action belongs to the platform owner: preserve a bounded final-guard subphase
or code before another attempt, reproduce the final path offline and on target
Linux, and present a new hash-pinned inactive correction. Another live cycle
requires a fresh card and approval; this result authorizes no retry, receipt,
lease, service stop, drill, A1 run or model call.
