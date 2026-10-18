# Cooperative daytime B60 lab-hours reservation

**Status: offline candidate / not installed / not approved for live effects.**
This is separate from the full-stop fault-injection drill, F2 archive timing,
F3 receipt release and the A1 benchmark. It performs no reboot, fault
injection, model benchmark, lease acquisition or schedule change by itself.

## Smallest viable pilot

The earliest reviewable pilot is a **60-minute daytime reservation**:

- up to **45 minutes** of exclusive B60 lab work;
- a **15-minute minimum restoration reserve**;
- a hard session deadline supplied by the host-owned preflight;
- one operator present for the entire reservation;
- no automatic extension, retry or handoff.

The accepted Qwen3.5-9B/SYCL backend remains running and exclusively reserved
for the lab. The session plan quiesces only these allowlisted competing
consumers:

| Guest | Unit/timer | Lab action |
|---|---|---|
| 104 | `aster-agent.service` | stop, then verify restored |
| 116 | `aster-speech.service` | stop, then verify restored |
| 114 | `news-aggregator-ingest.timer` | stop, then verify restored |
| 114 | `news-aggregator-digest.timer` | stop, then verify restored |

No command targets LXC110 `aster-llama.service`; no network policy, key,
model, schedule definition or unrelated guest is changed.

## Required host-owned preflight

Before a live pilot, the fixed source-bound producer must obtain—not receive
from caller JSON—the current backup/cycle, TrueNAS schedule/task state, Mac
subset state, exact backend/model/SYCL/GPU/auth state, consumer/timer state,
and a fresh host lock/lease identity. It must bind a unique lease ID and
generation to the 45-minute work window and 15-minute restoration reserve.

The preflight must reject stale, fabricated, partial or future evidence,
existing whole-host/application leases, competing jobs, backend drift,
unverified GPU/authentication, News timer drift, and any window that cannot
finish before its hard deadline. The source-only producer and fixed-file host
adapter are documented in commits `e34b3297` and `d74b58b9`; neither is wired
to the live entrypoint.

## Cooperative sequence

1. Record fresh source-bound preflight and operator identity; acquire the host
   lock without stopping anything.
2. Verify backend, GPU, auth and all four competing consumer/timer states.
3. Stop only the four allowlisted Aster/Speech/News entries and verify each
   stop; preserve the backend.
4. Perform bounded lab work. No reboot, fault injection, benchmark batch or
   arbitrary model call is part of this pilot.
5. Stop lab work before the restoration reserve, restore the four entries,
   and verify exact service/timer state, backend/model/SYCL/GPU/auth and
   schedule state.
6. Release the lock only after every postcheck passes. On any uncertain stop,
   start, timer or runtime observation, retain the lock and require operator
   reconciliation.

## Disabled staging and rollback gate

Before a live pilot, stage the planner, its tests and the source-bound adapter
in a new root-owned mode-0700 private directory on target Linux. Run imports
and synthetic tests only; do not create a lease, call a service, start a
timer, or run a model. Preserve exact old bytes if any host helper is later
replaced. A mismatch or failed test aborts before host effects. If a reviewed
disabled installation is later approved, replace only the named candidate
files atomically, verify hashes/modes/owners and confirm all timers/effects
remain disabled. Roll back only those files on a known-good checkpoint; if a
write or runtime state is uncertain, retain it for reconciliation and stop.

## Current evidence and remaining gates

`scripts/local-ai/cooperative_lab_session.py` is source-only and generates a
fixed plan without executing commands. Its focused tests pass 3/3; the full
`scripts/local-ai` suite passes 222 tests with 4 expected macOS root-custody
skips. The installed F2 diagnostic guard is unrelated read-only infrastructure
and does not provide this lab lease.

Live pilot approval must separately cover the named daytime window, target
host, exact source-bound producer/adapter pins, service/timer allowlist,
outage budget, operator, rollback and postchecks. No F2 scan, F3 receipt,
full-stop drill or A1 benchmark may be inferred from a successful lab session.
