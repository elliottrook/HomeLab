# Stream A restore observer GPU-exit correction — inactive replacement card

Status: **INSTALLED AND VERIFIED; LIVE RETRY NOT AUTHORIZED**

The latest prepare-only exercise failed closed when `/proc` churn made the
restore observer intermittent. This exact two-file replacement tolerates only
a PID that fully vanishes after its expected `renderD128` fd was observed;
surviving malformed, reused or unreadable entries still fail closed. It
authorizes no install, live retry, consumer action, model call, timer change or
push.

The prior installation attempt matched both source prehashes and was rolled
back automatically because the transport archive omitted the inert wrapper
`services/local-ai-lease/stream-a-evaluation-lease` required by the clean
wrapper test. No source assertion failed. Exact rollback restored observer
`9ecf6476...` and runner `cdac8693...` as `root:root` `0644`; F6 remained
inactive and the whole-host lease remained ready. No retry is authorized.

## Verified install result

The complete clean archive SHA-256 is
`96c89b41a51dac2fa9ff273a6e2c6ab2c94c07ad278b51d834521a88bc0b1dcb` and the
fresh checkpoint is `/root/stream-a-evaluation-observer-gpu-exit-replacement-20261025`.
Installed observer `70748eb1...` and runner `cf51b1d6...` are `root:root`
`0644`. Target suites passed 90/90; four independent five-call observer
batches passed 20/20; full `Exercise.prestate()` passed; and final no-state
checks passed. Guests, Aster, llama, Speech, News timers, Proxmox daemons,
F6 state and October 26 F2 timers remained healthy/unchanged. No live exercise
retry occurred or is authorized.

## Exact two-file runtime transaction with complete test archive

| Source | Target | Pre-upgrade SHA-256 | New SHA-256 | Mode |
|---|---|---|---|---:|
| `scripts/local-ai/stream_a_evaluation_restore_observer.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_restore_observer.py` | `9ecf64767e1c7acf402540d2701883241b1d94c6b8ec1b46248f20de6591f22b` | `70748eb15c50ff7008cadd85fe9affaf62c9ad3eb388ef962270f9f9389fc1d3` | 0644 |
| `scripts/local-ai/stream_a_evaluation_prepare_only_exercise.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_prepare_only_exercise.py` | `cdac8693c41fe1eb47cb0be626da46db2bc51bf4b91478e80b64eae6961b7ab1` | `cf51b1d6546e27aebdef9e44ad4751343e38aa388c8eae682f9a476641f390fb` | 0644 |

Source commit: `c370cce4`. Observer test hash:
`ca63b53302bd423e79d4d60459ef27967fd8d26fb21dd0f0fad1f4746b465460`.
The clean test archive must also include the unchanged inert wrapper
`services/local-ai-lease/stream-a-evaluation-lease`, SHA-256
`15f3de1ebb5294878d5f0ce0c6a0b7c03a64b42a71c081fda6d036b0c1ef71af`.

## Required inactive sequence

1. Create fresh root-only checkpoint
   `/root/stream-a-evaluation-observer-gpu-exit-replacement-20261025` and
   capture both exact prehashes, modes, owners and regular-file/no-symlink
   properties. Refuse on drift.
2. Replace only the two files atomically, retaining root custody and mode
   `0644`. Do not alter wrappers, helper, owner, watchdog, units, timers,
   runtime state or receipt custody.
3. Use a complete clean commit archive containing the two replacements and
   the unchanged wrapper dependency. Run the clean target-Linux suites: 46 evaluation-lease tests, 34 Stream A
   evaluation tests and 10 lease-watchdog tests; require 90/90. Run imports,
   static hash/mode checks and `git diff --check`.
4. Verify the GPU observer regression: a fully vanished PID after fd
   observation is ignored, while surviving partial/malformed/reused entries
   fail closed and exact-one accepted-holder enforcement remains unchanged.
   Keep all F6 units/timers disabled/inactive and do not retry the consumed
   live approval.

## Rollback

On any failure, restore both checkpointed files atomically and rehash them.
Preserve all runtime custody. If state is uncertain, retain evidence and stop
for manual reconciliation; never retry automatically.

This card is a prerequisite for a future separately approved exercise retry.
