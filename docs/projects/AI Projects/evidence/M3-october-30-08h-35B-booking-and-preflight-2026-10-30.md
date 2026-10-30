# M3 October 30 08:00 35B booking and preflight — 2026-10-30

The authoritative Lab Hours ledger reported the complete 08:00–09:15 PDT
execution-and-recovery window clear. Exact registered workload
`m3-joint-semantic-35b-public-v1` is booked separately as
`aster-stream-a-m3-35b-20261030-0800` from 08:00 to 09:00 with its registered
900-second recovery reserve through 09:15.

Static preflight passed after the mount-order correction:

- all 32 installed release-manifest pins match platform commits
  `d411ca18`/`76a7dd3c`;
- the whole-host lease is exactly ready and drain/operation state and locks are
  absent;
- no candidate mount, 35B process or M3 transaction remains;
- LXC104/110/116, Aster Agent, accepted 9B/SYCL with authentication, Speech,
  EPUB and News timers, dispatcher, Doctor, `pvescheduler` and `pvestatd` are
  healthy;
- the one-time 09:15 reconciliation is active.

This is conditional GO only. The runner must freshly recheck the reservation,
release pins, lease, shared lock, production health and competing processes
before effects. Any drift fails closed. The booking cannot promote a model,
open calibration or holdout data, or enable automatic routing.
