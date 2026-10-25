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
