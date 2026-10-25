# Stream A prepare-only exercise live result — 2026-10-25

## Result

The approved receipt-free prepare-only exercise remains **NO-GO**. The latest
attempt reached a healthy durable `PREPARED` lease with its fixed transient
owner, then failed closed when the recovery observer returned an uncertain
result. No consumer command, model request, production receipt or F6 arming
occurred.

The exact lease `exercise-20261025-1792968241-f519cae9` was recovered before
its deadline with the installed prepared-state callback, which returned
`cancelled-prepared`. The retained uncertain watchdog state had SHA-256
`14ef89e12412d76623f2318f7ed0e70f73364fc0d388748aec0fa373be3cae6d`.
After bounded cleanup there was no lease, lock, identity, intent, heartbeat,
watchdog status, restore intent or exercise receipt. All F6 units remained
disabled/inactive, the four production consumers remained healthy and the
October 26 F2 timers were unchanged.

## Measured cause

Ten repeated read-only observer calls passed eight times and failed twice.
Separating the observer phases showed backend activity, metadata-only
authentication and endpoint-idle checks passing ten of ten; GPU-holder
enumeration passed nine of ten and raised one `RuntimeError`. The intermittent
boundary is therefore the global `/proc` GPU-holder scan, not the backend,
authentication or endpoint-idle checks.

The scan treated a process that exited between render-descriptor discovery and
identity collection as an unsafe live-holder change. That is conservative but
unstable: a fully exited process cannot retain the render device. A surviving
partial entry, rapid PID reuse, unreadable identity, foreign holder or second
live holder must still fail closed.

## Source-only correction

Stream A commit `c370cce4` implements that narrow distinction. It ignores only
a process whose `/proc/<pid>` entry has fully vanished, completes the scan and
still requires exactly one accepted live holder. The existing surviving-
partial-entry test continues to fail closed; a new regression removes the
process after descriptor observation and proves that enumeration continues.
The prepare-only runner pin was advanced with the observer source.

Source hashes are:

- observer: `70748eb15c50ff7008cadd85fe9affaf62c9ad3eb388ef962270f9f9389fc1d3`;
- prepare-only runner: `cf51b1d6546e27aebdef9e44ad4751343e38aa388c8eae682f9a476641f390fb`;
- observer test: `ca63b53302bd423e79d4d60459ef27967fd8d26fb21dd0f0fad1f4746b465460`.

The clean dependency-free suites pass 46 evaluation-lease tests, 34 Stream A
evaluation tests and 10 lease-watchdog tests: **90/90** total. Python compile
and diff checks pass. The platform owner has been asked to integrate the exact
source, independently test it on target Linux and issue a hash-pinned inactive
two-file observer/runner replacement card.

No host installation or exercise retry is authorized by this source result.
After an approved inactive replacement, the next static proof is repeated
read-only observer stability plus full exercise prestate. Only a separate
fresh one-attempt approval may run the live exercise again.
