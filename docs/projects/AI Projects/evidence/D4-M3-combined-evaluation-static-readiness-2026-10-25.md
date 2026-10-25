# D4 + M3 combined evaluation static readiness — 2026-10-25

> Decision: **STATIC PASS; LIVE LEASE / RECOVERY CHAIN NOT YET READY**

This check reconciles the two Stream A workloads intended for one
endpoint-retaining 90-minute evaluation lease. It does not acquire a lease,
stop a consumer, read a key or call the model.

## D4 candidate-G

- exact run digest:
  `03b0ad74a862ee04de75e012f52f6662c61192b69b279ea4d1d66c80d9ff9153`;
- eleven-file manifest SHA-256:
  `defaf6039e01c7ac0cc16b3c2a28568336335bc949ea8992ec288819d33c23b8`;
- decision-rule SHA-256:
  `35bedd86f244dc527606b463dcb223dde68c242c67d8028674d01553c5a9f089`;
- all 11 manifest file lengths and hashes match, totalling 107,871 bytes;
- the current focused SA3 suite passes 80/80; and
- a root-custody-shaped local tar packet was rebuilt at SHA-256
  `d5a36cd02be6fdd3d0935e6ca1b23c1d0cad1329d72b04bb4048505fec7e3d47`.

Candidate-G remains unspent. Jason's exact run approval remains recorded in
the prior lease-preflight NO-GO evidence. The tar packet is temporary Mac
preparation only and has not been copied to a guest.

## M3 calibration

- corrected staging manifest SHA-256:
  `69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165`;
- 11/11 inputs and 98,414 bytes are staged root-only in LXC110;
- exact custody and target imports passed, with no outputs or runner process;
- the pinned Pydantic 2.13.4 NLU suite passes 126/126; and
- the registered policy, candidate, source, release and model pins remain
  unchanged.

The M3 model run still needs one exact live-run approval after the platform
lease/recovery path is independently accepted.

## Shared platform gates

The four-file evaluation-lease library has completed inactive installation and
reports `effects=disabled`, `state=source-only`. It has no live entry point,
service or timer. The platform owner is preparing a manually invoked,
explicit-phase effect adapter and exact recovery/deployment card; it must be
reviewed and installed before any consumer can be quiesced.

The October 26 F2 prepare/final timers are enabled for 01:15 and 01:20 PDT, but
F2 has not passed and no current-cycle state exists yet. A successful F2 result
must still feed the separately gated F3/F4 retained-receipt chain. Scheduled
timers are not proof of either gate.

Therefore the next possible live sequence is:

1. reconcile October 26 F2 terminal evidence;
2. if F2 passes, complete the approved/reviewed F3/F4 receipt steps;
3. independently review and inactive-install the platform effect adapter;
4. obtain the exact lease/live M3 approval after fresh admission checks;
5. acquire the lease, run D4 once, conditionally run M3 once, then restore and
   independently verify production within the fixed reserve.

Any failed F2/F3, adapter, fresh-health, endpoint-idle, schedule or recovery
gate is a live-run NO-GO. Offline Stream A work continues independently.
