---
name: b60-lab-hours
description: Assess, register, reserve, execute, or verify workloads that use or compete for the HomeLab B60 local-AI stack on Proxmox. Use for B60 Lab Hours bookings, readiness audits, missed reservations, dispatcher/lease checks, and B60-backed schedules; do not apply to independent Mac-local MLX, Metal, or CPU inference unless it also calls or competes with B60.
metadata:
  contract-version: "2"
---

# B60 Lab Hours V2

Use Proxmox's existing Lab Hours ledger, registered-workload registry, dispatcher,
whole-host lease, shared operation lock and recovery guardian as the authority.
Do not replace these controls with an autonomous booking agent or an arbitrary
command runner.

## Route the request

- For a read-only availability or booking audit, inspect live state and report;
  do not reserve or alter services.
- For a new workload, establish a fixed hash-pinned workload identity and its
  runner/recovery path before booking it.
- For an already registered workload, verify its registration and exact
  execution window before reserving.
- For any recurring schedule that can use or compete with B60, verify the whole
  proposed execution and recovery window before creating or enabling it. The
  runtime must recheck immediately before effects and fail closed.
- Independent Mac-local inference uses reviewed Mac host controls instead. It
  needs Lab Hours only when it calls, drains, schedules against or competes with
  B60.

## Non-negotiable admission rules

1. A B60 workload requiring exclusive use must have its own booking naming a
   registered, hash-pinned workload. Never place an arbitrary command in a
   booking and never substitute an exclusive-capacity record for workload
   registration.
2. A reservation supplements rather than replaces the whole-host lease and
   shared operation lock.
3. Include recovery time in availability checks. Use offset-qualified ISO 8601
   timestamps in `America/Vancouver`; never infer availability from clock time.
4. If the ledger, registry, release manifest, dispatcher, lease or lock state is
   unavailable or cannot be verified, fail closed.
5. Respect the active repository authorization stream. A user may define a
   bounded Lab Hours booking as a Stream A authorization envelope: once the
   booking, purpose, affected systems, allowed change classes, rollback and
   stop conditions are approved and recorded, the admitted owner may diagnose,
   repin implementation files, retry and release autonomously inside that
   interval. Do not treat each retry as a new project or ask again for actions
   already inside that envelope. Work outside it still follows the repository's
   ordinary authorization rules.
6. Do not overlap another owner's claimed booking, lock or incomplete recovery.
   A failed booking is reusable capacity only after its record proves restoration
   and live locks/services agree.
7. Before a V2 retryable session begins, send the activated registration and
   exact booking to an independent read-only agent for evaluation. The evaluator
   must not claim the booking or initialize the backend. Require concrete
   blockers and a `WILL RUN`, `LIKELY RUN`, or `WILL NOT RUN` verdict. Do not
   proceed on `WILL NOT RUN`; resolve deterministic blockers and re-evaluate.

## Assess before proposing a booking

Read the applicable repository `AGENTS.md` and project standard. Inspect, using
standalone read-only BatchMode SSH commands:

- the authoritative booking ledger and candidate full window;
- the workload registry entry, owner, runner kind, minimum duration, deadline
  and recovery reserve;
- the dispatcher timer and claim window;
- whole-host lease, shared/drain locks and any current claimant;
- accepted production service identity and health;
- runtime, model, source and input pins plus available storage/memory;
- recovery guardian, receipt validation and accepted-service postcheck;
- hardware/backend compatibility and all required dynamic libraries;
- whether stated network, memory, swap and fault-abort controls are actually
  enforced rather than merely reported.

For new or materially changed GPU runtimes, perform an inert readiness test that
does not initialize or use the B60: load required shared libraries, validate
transient-unit sandbox/cgroup properties and verify hashes. Do not test GPU
enumeration outside a valid booking.

Read [references/readiness.md](references/readiness.md) for the detailed gate.
Use `scripts/check_booking.py` for the standard read-only control-plane check.

## Register and reserve

Keep the workload deterministic and bounded:

- fixed source/model/input/runtime hashes;
- fixed request or artifact count, timeout and output-size limit;
- fail-closed guest/host adapter with no arbitrary arguments;
- explicit cleanup/absence proof;
- durable recovery guardian and accepted-service restoration check;
- content-minimized receipt with hashes and measurements;
- rollback checkpoint for controller/registry files.

For a V2 retryable session, the registry must additionally declare:

- `retryable_session=True`, a bounded per-attempt deadline, and whether any
  additional attempt-count ceiling applies;
- a time-budgeted retry policy that admits another attempt only when its full
  deadline fits before booked end;
- attempt-unique evidence/output paths; and
- restoration as a prerequisite for every later attempt or early release.

Before `reserve`, run the authoritative complete-window check:

```text
/usr/local/sbin/aster-lab-hours check-window --start <offset-ISO> --end <offset-ISO-including-recovery>
```

Only after a clear result and required approval, create the workload booking:

```text
/usr/local/sbin/aster-lab-hours reserve --booking-id <id> --owner <registered-owner> --workload <registered-workload> --start <offset-ISO> --end <execution-end>
```

Add `--promotable` only when the owner is prepared to run earlier. Promotion is
opt-in, preserves the original duration, records the original times, and must
fit after the prior recovery boundary and before every later protected window.

Re-read the resulting record. Confirm that its state is `scheduled`, its owner
and workload match exactly, and its execution duration satisfies both the
registry and ledger maximum. Never report a rejected reservation as booked.

## Prove that it will run

A scheduled record alone is insufficient. Run the readiness checker, then trace
the actual path:

`dispatcher due()` → booking claim → registered runner kind → full-drain owner
scope → workload adapter → guest/runtime → bounded receipt → cleanup → guardian
and accepted-production postcheck → terminal ledger result.

Check every hash at the custody boundary and resolve dynamic-library locations
under the exact service environment. Validate that transient service properties
implement claimed isolation and resource limits. Treat an untested assumption
in this chain as a blocker or clearly labelled residual risk.

V2 retryable sessions require an independent read-only audit after the final
controller/registry activation and booking, even when the workload was audited
earlier. New runner kinds and materially changed GPU backends also require this
audit. Ask for concrete blockers and a `WILL RUN`, `LIKELY RUN`, or
`WILL NOT RUN` verdict; do not let the auditor mutate live state, claim the
booking, or initialize the backend. Record the verdict with the booking
evidence. A `LIKELY RUN` verdict is acceptable only when the remaining risk is
irreducible first-use behavior confined by the booked session and recovery
controls.

## Observe and close

After execution, verify the terminal booking record, artifact hash/decode,
kernel fault/reset evidence, measured resource use, cleanup absence, lease/lock
release, accepted service identity/health and affected timers. Preserve the
result and update project evidence. A workload failure with successful recovery
is not a successful test.

## V2 session operations

For a workload explicitly registered as a retryable session, the booking grants
the owner the booked interval rather than one execution. Success or a restored
failure leaves the booking `claimed` until booked end or guarded release. Each
attempt has an attempt number, start/finish times, result code, restoration
proof, and attempt-specific candidate pins.

A retry may use that same claimed booking without a new window check only when:

- the previous attempt is `failed_restored` and `retry_available` is true;
- any optional registry attempt-count ceiling has not been reached;
- the complete bounded attempt deadline fits before booked end;
- the whole-host lease is ready and operation/drain locks are absent;
- the workload remains registered and release-manifest validation passes; and
- the retry is within the booking's recorded authorization envelope.

Dispatch the fixed registered workload only:

```text
/usr/local/sbin/aster-lab-hours retry <booking-id>
```

Do not retry blindly or supply an arbitrary command. An unrestored failure is
terminal. Inside an approved autonomous booking envelope, diagnosis may revise
and activate code, runtime, model or input pins without another conversational
approval when the owner, runner kind, workload purpose, affected systems and
bounded request shape remain unchanged. Validate and retain every revision's
pins and attempt evidence. A material change to those boundaries requires a new
authorization decision and, where applicable, a new workload identity/booking.

Permit early release before claim, or after a claimed attempt is idle and
restoration is proven:

```text
/usr/local/sbin/aster-lab-hours release <booking-id>
```

Never release a running or unrestored session. A release after effects retains
the recovery buffer and preserves whether the session succeeded or failed. A
waiting booking may move earlier only when it opted into promotion and its
entire original duration fits after the recovery boundary without colliding
with any other protected window. Preserve its owner, workload, pins and
original times in the ledger. Promotion is admission only; it does not itself
start effects.

For an uncertain first-use backend, prefer a bounded heartbeat during the
session. When the booking is an approved autonomous envelope, make that
heartbeat the acting owner: on `failed_restored` with `retry_available=true`,
it must immediately diagnose, repin, validate, obtain any required independent
re-audit and explicitly dispatch the fixed workload itself. A notification is
informational and must not pause action for user acknowledgement. Do not use a
read-only observer as the only continuation mechanism unless the user asked for
observation only or a separately proven wake path starts an acting owner without
user intervention. Never describe a passive reporter as autonomous execution.

Never implement an unexamined retry loop. Stop on unrestored failure, a new
material risk, an out-of-envelope change, or insufficient time for the full
bounded attempt. If time is exhausted after restoration, release early and,
when the approved objective remains active, check and reserve the next clear
window rather than silently stopping. Remove the heartbeat at terminal state or
replace its booking identity and cutoff when work legitimately moves to a new
reservation.
