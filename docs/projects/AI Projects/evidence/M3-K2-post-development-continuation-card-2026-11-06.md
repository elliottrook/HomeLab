# M3 K2 post-development continuation card — 2026-11-06

## Purpose

This card prevents another pause after the booked 20:00 K2 development
transaction. It distinguishes work Stream A may continue autonomously from the
one next platform effect that still needs its own deployment gate.

## Automatic continuation

At 21:05 the existing observation-only heartbeat will read the authoritative
reservation, retained result and production state. It will not invoke or retry
the workload. It may autonomously:

1. accept only exactly 192 requests, zero retries/errors, the frozen score,
   `production_restored=true`, no remaining K2 process/listener, lease ready,
   locks absent and all named production services/schedules healthy;
2. record the exact pass, reject or first failure and retain evidence;
3. diagnose deterministic source defects offline without retrying;
4. update the delivery map and make scoped local commits; and
5. on a passing restored result, generate the existing content-free two-host
   inactive-install plan from the exact bundle and installer.

None of those steps needs another conversational approval.

## Next genuine deployment gate

The plan deliberately returns `ready-for-separate-approval`. The first new
effect after a pass is the fixed-root, reversible inactive installation on the
MacBook followed by the Mac mini. It starts no service, grants no access,
changes no model and has reverse-order rollback, but it is still a deployment.
The exact approval request should cover only:

- installing the pinned 14-file sealed runtime bundle inactive on those two
  hosts in the frozen order;
- validating both installed trees and retained absent-state checkpoints; and
- rolling back in reverse order on any mismatch.

It must exclude service restart, listener start, sealed-content access, B60
model calls, route activation, tools and promotion. After that inactive install
passes, registration and booking of the distinct 32-request sealed transaction
will be presented as the next bounded platform/schedule gate rather than as a
series of per-test approvals.

## Failure branch

A reject, failed restoration or uncertain result authorizes no install, sealed
evaluation, retry or reschedule. Stream A will record the exact first failure,
confirm production recovery and continue only independent offline milestone
work until a corrected candidate exists.
