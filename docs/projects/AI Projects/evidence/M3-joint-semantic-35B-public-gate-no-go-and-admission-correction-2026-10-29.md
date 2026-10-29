# M3 joint-semantic 35B public gate NO-GO and admission correction — 2026-10-29

## Timed result

Booking `aster-stream-a-m3-35b-20261029-1500` was claimed at its exact 15:00
PDT start and immediately failed closed. The root-custodied terminal state is:

- state: `no_go`;
- first failure phase: `claim`;
- failure code: `WORKLOAD_RUNNER_NOT_REGISTERED`;
- production restored: `true`;
- start and finish epoch: `1793311200`.

No attempt record or public result exists, so the 24-case quality gate did not
run and no score can be inferred. The lease, shared state and locks remained
absent; LXC110 retained no model mount; no 35B process existed; LXC104/110/116,
Aster Agent, accepted 9B/SYCL, Speech, the Lab Hours dispatcher, Doctor,
`pvescheduler` and `pvestatd` all passed the postcheck.

## Root cause and mitigation

The workload registry and command builder both supported the exact M3 runner
kind, but the final live admission allowlist still contained only three older
kinds. The earlier tests checked registry and command composition separately
and missed their joined admission boundary.

Platform commit `c424d0a2` replaces that inline set with one named immutable
allowlist, adds the registered M3 kind, and adds a regression that resolves the
exact workload through the registry before checking admission. The corrected
runner and repinned release manifest are installed inactive. All 32 installed
pins, joined admission, Doctor and production postchecks pass; rollback is
retained at `/var/lib/local-ai-lab/checkpoints/m3-admission-c424d0a2`.

The spent booking was not retried or rescheduled. Automatic routing remains
off, calibration and holdout custody are unchanged, and the next quality gate
is one fresh conflict-free booked public run.
