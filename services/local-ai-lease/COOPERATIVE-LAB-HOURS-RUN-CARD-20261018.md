# Cooperative daytime B60 lab-hours reservation

**Status: offline candidate / not installed / not approved for live effects.**
This is separate from the full-stop fault-injection drill, F2 archive timing,
F3 receipt release and the A1 benchmark. It performs no reboot, fault
injection, model benchmark, lease acquisition or schedule change by itself.

Jason's approved daytime Aster/voice outage ceiling is up to 90 minutes and
the reservation must end at least 45 minutes before the 17:15 News run. The
first pilot intentionally uses the stricter 45-minute reservation below;
expanding it requires measured evidence and a revised approval.

## Smallest viable pilot

The earliest reviewable pilot is a **45-minute daytime reservation**:

- **30 minutes** of exclusive B60 lab work;
- a **15-minute minimum restoration reserve**;
- a fresh next-News-ingest timestamp plus a five-minute margin;
- a hard session deadline supplied by the host-owned preflight;
- one operator present for the entire reservation;
- no automatic extension, retry or handoff.

The accepted `llama.cpp b11429 SYCL/Level Zero` backend (Qwen3.5-9B) remains
running and exclusively reserved for the lab. The session plan quiesces only these allowlisted competing
consumers:

| Guest | Unit/timer | Lab action |
|---|---|---|
| 104 | `aster-agent.service` | runtime-mask and stop, then unmask/start/verify |
| 116 | `aster-speech.service` | runtime-mask and stop, then unmask/start/verify |
| 114 | `news-aggregator-ingest.timer` | runtime-mask and stop, then unmask/start/verify |
| 114 | `news-aggregator-digest.timer` | runtime-mask and stop, then unmask/start/verify |

The runtime masks are the deny-new-start boundary for the fixed inventory;
they are reversible and journaled. No command targets LXC110
`aster-llama.service`; no network policy, key,
model, schedule definition or unrelated guest is changed.

The first pilot is an isolation-and-recovery proof. It keeps the backend
available, but the candidate controller does not grant arbitrary B60 requests
or a benchmark batch. A later usable-lab release must name one reviewed
workload and prove an actual admission-enforcement boundary for direct clients
to `192.168.70.12:11435`; an instant `ss` observation, a single allowed peer,
or zero connections is not enforcement. Until an existing gateway/ACL or a
separately reviewed temporary source restriction is verified, usable MacBook
B60 work remains NO-GO. This distinction prevents a successful drain test from
being mistaken for a production workload authorization.

## Required host-owned preflight

Before a live pilot, the fixed source-bound producer must obtain—not receive
from caller JSON—the current backup/cycle, TrueNAS schedule/task state, Mac
subset state, exact backend/model/SYCL/GPU/auth state, consumer/timer state,
and a fresh host lock/lease identity. It must bind a unique lease ID and
generation to the 30-minute first-pilot work window and 15-minute restoration
reserve (45 minutes remains the later measured maximum).

Volatile runtime and next-ingest observations must be no more than 30 seconds
old at effect admission; backup, TrueNAS and Mac-subset observations must be
no more than 15 minutes old. Re-observe the volatile state immediately before
the first mask and treat any mismatch as NO-GO.

The preflight must reject stale, fabricated, partial or future evidence,
existing whole-host/application leases, competing jobs, backend drift,
unverified GPU/authentication, News timer drift, and any window that cannot
finish before its hard deadline and before the next hourly News ingest with a
five-minute margin. Stopping the hourly ingest is not a free pause: unless a
future run explicitly supplies a reviewed catch-up, the bounded first pilot
must fit before that next fire. The offline producer and fixed Linux observer
are `scripts/local-ai/cooperative_lab_sources.py` and
`scripts/local-ai/cooperative_lab_host_adapter.py`; neither is wired to the
live entrypoint. The observer's direct-client exclusivity check is a blocking
gate: no configured allowed client or any unknown established peer is NO-GO.

## Cooperative sequence

1. Record fresh source-bound preflight and operator identity; acquire the host
   lock without stopping anything.
2. Verify backend, GPU, auth and all four competing consumer/timer states.
3. Acquire the host-wide exclusion, persist the lease state, apply the four
   fixed runtime masks (which deny new starts), then verify each effect;
   preserve the backend.
4. The trusted owner wrapper must enforce the source-bound lab-end cutoff with
   its monotonic timer. Perform bounded lab work for at most 30 minutes. No reboot, fault
   injection, benchmark batch or arbitrary model call is part of this pilot.
5. Stop lab work before the restoration reserve, restore the four entries,
   and verify exact service/timer state, backend/model/SYCL/GPU/auth and
   schedule state.
6. Release the lock only after every postcheck passes. On any uncertain stop,
   start, timer or runtime observation, retain the lock and require operator
   reconciliation.

## Disabled staging and rollback gate

Before a live pilot, stage exactly the session controller, source producer,
Linux observer and their three focused tests in a new root-owned mode-0700
private directory on target Linux. Run imports
and synthetic tests only; do not create a lease, call a service, start a
timer, or run a model. Preserve exact old bytes if any host helper is later
replaced. A mismatch or failed test aborts before host effects. If a reviewed
disabled installation is later approved, replace only the named candidate
files atomically, verify hashes/modes/owners and confirm all timers/effects
remain disabled. Roll back only those files on a known-good checkpoint; if a
write or runtime state is uncertain, retain it for reconciliation and stop.

## Current evidence and remaining gates

The session controller, source producer and Linux observer are source-only and
disabled by default. Their focused tests pass 9/9; the full `scripts/local-ai`
suite passes 228 tests with 4 expected macOS root-custody skips. The installed
F2 diagnostic guard is unrelated read-only infrastructure and does not provide
this lab lease.

Live pilot approval must separately cover the named daytime window, target
host, exact source-bound producer/adapter pins, service/timer allowlist,
outage budget, operator, rollback and postchecks. No F2 scan, F3 receipt,
full-stop drill or A1 benchmark may be inferred from a successful lab session.
