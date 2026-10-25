# Stream A prepare-only exercise runner — source boundary

Status: **INSTALLED INACTIVE AND VERIFIED; EXERCISE NOT AUTHORIZED OR RUN**

The runner is a single bounded transaction for the separately approved
prepare-only exercise. It captures and verifies prestate, creates only a
receipt-free exercise intent, observes the healthy watchdog, stops only the
fixed transient owner, waits for bounded owner loss, invokes watchdog recovery,
and verifies exact cleanup. It never quiesces a consumer, calls a model, arms a
recurring timer, or changes F2/F3/F4/F5 schedules.

## Pinned source

| File | SHA-256 | Mode |
|---|---|---:|
| `scripts/local-ai/stream_a_evaluation_prepare_only_exercise.py` | `df106ae07754a219e69366faffcfe7cdcd5f83630728a002a3327bad23288821` | 0644 |
| `scripts/local-ai/test_stream_a_evaluation_prepare_only_exercise.py` | `17a50b960fc313028598041ecdfa3ff8752dd47537b9bc2740d10d7231cdfbc7` | 0644 |
| `services/local-ai-lease/stream-a-evaluation-prepare-only-exercise` | `87f206b51bbe489a391ec43615644cc411cdc7cfe0666592fdb9ffe622ae300c` | 0755 |

Implementation commit: `f94dd5d46690a5770769390ff8d7a01eb389078d`, integrated
locally as `95cacab0`; command-boundary and real-wrapper review fixes are in
`16608358`, `2c633a68` and `17285d77`. The current focused source suites pass 77 tests
(46 evaluation, 24 owner/watchdog/observer/launcher, 7 runner).

## Safety contract

- Requires root and `--effect-authorized`; the default wrapper invocation is
  inert.
- Pins the installed source hashes before creating any intent and refuses on
  drift, absent custody, unsafe receipt directory or non-ready whole-host
  lease.
- Requires all F6 owner/watchdog units and timers disabled/inactive, exact
  active October 26 F2 timer snapshots, healthy backend/GPU observation and
  the exact four-consumer `enabled+active` baseline.
- Generates a unique `exercise-...` lease ID and owner ID, generation `1`,
  exact exercise marker/mode and fixed two-minute/five-minute deadlines.
- Uses only `exercise-prepare`, the fixed transient owner wrapper, one
  heartbeat, the effectful watchdog wrapper, transient-owner stop/reset-failed,
  and the read-only restore observer. The runner rejects consumer mutations,
  model/backend commands and production systemd mutations.
- Healthy watchdog output must be `not-attempted`; owner-loss recovery must be
  `recovered`, clear lease/lock/operation-lock/identity/intent state and leave
  all four consumers unchanged.
- Any uncertainty stops cleanup expansion, retains evidence and returns
  failed-closed. A success receipt contains only bounded digests/status and is
  written last under the root-owned 0700 exercise receipt directory.

The runner is not authorization to execute the exercise. Live execution still
requires a separate approval after the backup/F2 window and a fresh prestate.

## Verified inactive install result

The runner and wrapper were installed under the approved inactive boundary with
the pinned hashes above: `root:root` modes `0644` and `0755`. The exercise
receipt directory is `root:root` mode `0700` and empty. The exact target-Linux
suite passed 77/77; Python compilation and inert `--run-once` validation also
passed. No exercise ran, no runtime lease/identity/heartbeat/lock/receipt was
created, and all F6 units/timers remained disabled/inactive.
