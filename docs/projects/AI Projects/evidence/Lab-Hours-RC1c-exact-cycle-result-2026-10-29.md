# Lab Hours RC1c exact-cycle result — 2026-10-29

## Outcome

**GO — COMPLETE.** The independently scheduled RC1c transaction started at
04:05:00 PDT and completed at 04:08:40 PDT, a 220-second end-to-end window.
The root-custodied terminal state is `complete`, records exactly three fixed
tool-free requests, and records `production_restored=true`.

The owner receipt reports `pilot-complete`, generation 1, exit status zero and
the pinned `accepted-9b-direct-control-smoke-v1` profile. The terminal and
attempt records remain root-owned mode `0600` under
`/var/lib/local-ai-lab/lab-hours-attempts/night-rc1c-20261029/`.

## Independent reconciliation

- all nine installed RC1c source files still match their terminal-state pins;
- the accepted model, llama.cpp/SYCL binary and production unit match their
  pinned SHA-256 values;
- the exact owner scope and guardian are inactive and collected;
- the lab listener on port 11436 and the lab smoke process are absent;
- the shared drain state, drain lock and operation lock are absent;
- the whole-host lease is exactly `ready`;
- LXC104, LXC110, LXC114 and LXC116 are running;
- Aster Agent, accepted llama.cpp/SYCL and Speech are active with zero service
  restart counts;
- the accepted model health endpoint returns `ok`;
- both News timers are active and waiting;
- the EPUB timer is active and its static worker is running its resumed
  bounded attempt;
- `pvescheduler` and `pvestatd` are active.

The spent date-specific service and timer were stopped, disabled, removed and
daemon-reloaded after reconciliation. Both now have `LoadState=not-found` and
the retained attempt evidence was not altered.

## Meaning

LH3 is complete. The release candidate proved the complete scheduled
transaction against a real current-cycle backup: production consumers were
isolated, lab ownership ran the fixed three-request workload, and the accepted
production stack and ongoing EPUB work were restored without retained lab
state.

This result does not create a recurring Lab Hours schedule. LH4 remains a
separate reviewed operating decision covering the recurring reservation,
monitoring and collision policy. It also does not promote F2–F5, change a model
or backend, or authorize repair actions.

