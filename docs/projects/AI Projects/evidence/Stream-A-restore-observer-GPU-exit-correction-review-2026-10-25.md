# Stream A restore-observer GPU-exit correction review — 2026-10-25

## Decision

The platform owner's exact inactive two-file replacement is **accepted for
installation review**. This is a source and clean-archive result only; it does
not install either file or authorize another live exercise.

Platform source commit `10f15bca` matches Stream A source commit `c370cce4`.
The card is platform metadata commit `0ddad44f`, file
`STREAM-A-EVALUATION-LEASE-OBSERVER-GPU-EXIT-INACTIVE-REPLACEMENT-CARD-20261025.md`,
SHA-256 `710086cceff0403a726a42e9cb42222c2ba63f8fdd4a1ce8e2611cc7d5fd494c`.

## Independent clean-archive proof

Stream A extracted the exact platform metadata commit into a fresh directory
and verified:

- observer SHA-256
  `70748eb15c50ff7008cadd85fe9affaf62c9ad3eb388ef962270f9f9389fc1d3`;
- prepare-only runner SHA-256
  `cf51b1d6546e27aebdef9e44ad4751343e38aa388c8eae682f9a476641f390fb`;
- observer-test SHA-256
  `ca63b53302bd423e79d4d60459ef27967fd8d26fb21dd0f0fad1f4746b465460`;
- 46/46 evaluation-lease tests;
- 34/34 Stream A evaluation tests;
- 10/10 lease-watchdog tests;
- Python compilation of the two replacement sources.

The correction ignores only a fully vanished process after render-descriptor
observation. A surviving partial, malformed, unreadable or reused process
still raises; exact-one accepted-holder enforcement remains unchanged. This
preserves fail-closed behavior for a live foreign or additional holder while
removing the measured exited-process race.

## Next gate

The exact card replaces only the installed observer and prepare-only runner,
after matching their two old hashes and capturing root-only rollback copies.
It requires the same 90 tests on target Linux and leaves all wrappers, units,
timers and runtime custody unchanged. No exercise retry is included. An exact
host-change approval is required before that inactive installation.

## Installed result

The first approved transaction under metadata commit `0ddad44f` rolled back
cleanly after 45 passing evaluation tests because its transport archive omitted
the unchanged inert lease wrapper needed by the final wrapper test. Both old
runtime hashes and root:root mode `0644` were restored; F6 remained inactive
and the whole-host lease remained ready. No source assertion failed.

The platform owner corrected only the archive boundary and checkpoint identity
in metadata commit `fed7052d`. Jason explicitly approved that revised card.
Its complete clean archive SHA-256 was
`96c89b41a51dac2fa9ff273a6e2c6ab2c94c07ad278b51d834521a88bc0b1dcb`.

The revised inactive transaction completed with a fresh root-only checkpoint
at `/root/stream-a-evaluation-observer-gpu-exit-replacement-20261025`, all
**90/90** target-Linux tests passing, and the two installed accepted hashes at
root:root mode `0644`.

Four independently invoked five-observation batches then passed **20/20**.
Full `Exercise.prestate()` completed with the expected `consumers`, `f2`, `f6`
and `observation` sections. No lease, lock, identity, intent, heartbeat,
watchdog status or restore intent remained. LXC104/110/116, Aster Agent, the
accepted llama service, Speech, both News timers, `pvescheduler` and `pvestatd`
were healthy. F6 stayed disabled/inactive and the October 26 F2 timers stayed
scheduled for 01:15 and 01:20 PDT.

The inactive correction and static preflight are complete. A new live
prepare-only exercise remains a distinct one-attempt approval under an updated
exact card and must not overlap F2.
