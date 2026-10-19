# Cooperative lab-hours offline review — 2026-10-18

## Result

The earlier planner was not runnable: it reused the application benchmark
pre-lease contract, required contradictory News state, had no current-time
chronology, and did not hold a host exclusion or deny new starts. It is
replaced by a separate source-bound candidate in
`scripts/local-ai/cooperative_lab_session.py`.

The candidate remains disabled by default and has no live wrapper or schedule.
It preserves the `llama.cpp b11429 SYCL/Level Zero` backend and fixes the
daytime inventory to Aster 104, Speech 116, and the two News timers in 114.
Runtime systemd masks are applied before the lab window, so the fixed
consumers cannot restart during the window. Unmask/start recovery is explicit
and journaled.

## Safety properties tested offline

- source identity, backend, GPU/authentication, consumer health, active News
  timers, and deny-new-start capability are required;
- current time, start, end, and restore deadline are ordered and duration-bound;
- the 45-minute lab maximum and 15-minute restoration reserve are enforced;
- the first pilot can be bounded to 30 minutes and requires a fresh next-hourly-
  News-ingest timestamp plus a five-minute margin; a timer stop is not treated
  as permission to silently skip an ingest;
- a host exclusion is held across the effect and restore phases;
- state is atomically persisted and every effect has intent/observed journal
  events;
- failed effects leave the lock and state for reconciliation and do not
  auto-restore under uncertainty;
- restore requires owner presence and positive exact postchecks before releasing
  the lock; a missed deadline records an overdue event but does not block
  emergency recovery;
- the durable state carries an owner identity and heartbeat and can be resumed
  by a reviewed recovery process after the original owner process ends;
- restore derives and validates the canonical fixed command inventory instead
  of trusting caller-supplied commands, and the workload wrapper has an
  explicit source-bound lab-end cutoff hook;
- advisory mode executes no command.

Focused result: `test_cooperative_lab_session.py` — 5 passed.

The first usable pilot is still intentionally an isolation/recovery proof. The
backend remains available, but a separate reviewed workload declaration is
required before B60 requests are authorized. This candidate does not itself
authorize arbitrary model calls or a benchmark batch.

The preflight dataclass is an offline contract, not proof that its booleans,
epochs, or receipt came from the host. A live producer must obtain and
authenticate those values from the pinned backup, schedule, backend, GPU,
consumer and client-observer sources; caller-supplied JSON is not acceptable.
The exact observer callback must likewise be bound to read-only service/timer
state checks before target-Linux installation can be considered.
The owner-presence flag and clock passed to the offline methods are contracts
for that trusted wrapper, not independent authority; target-Linux work must
bind them to the operator session and a monotonic timer.

## Remaining gates

The owner-facing staged path is pinned in
`COOPERATIVE-MACBOOK-B60-LAB-ADMISSION-STAGED-DESIGN-20261018.md`.
Target-Linux disabled installation of the admission module, source-bound live
producer/adapter wiring, persistent supervisor/independent recovery,
direct-client admission enforcement for `192.168.70.12:11435`, and an explicit
daytime pilot approval remain outstanding. No host effects, reboot, schedule
change, F2 scan, F3 receipt, full-stop drill, or A1 benchmark was performed.
