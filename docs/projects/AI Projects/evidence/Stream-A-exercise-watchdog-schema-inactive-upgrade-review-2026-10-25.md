# Stream A exercise-watchdog schema inactive upgrade review — 2026-10-25

> Decision: **REVISED CANDIDATE READY; INSTALL RETRY NOT YET AUTHORIZED**

## Scope

The installed evaluation watchdog accepted only the production lease's
75-minute effect and 90-minute restore deadlines.  It therefore could not read
the already reviewed receipt-free prepare-only exercise state, whose fixed
deadlines are two and five minutes.  No live exercise could safely proceed.

The platform owner integrated the source correction as `daf8b05c`.  It binds
the watchdog to the exact lease mode, exercise marker, lease identity,
generation, phase and corresponding deadline pair.  Production semantics are
unchanged.  The new watchdog SHA-256 is
`19606f6b398dd6f43a461704081e66f09e292c434f73f4aaee46327f9cc02f53`.

## First inactive attempt and rollback

Jason approved the one-file inactive transaction pinned by platform card
`3acd23b7`.  The installed prehash
`68f261c65f48443a7d7c2115ad0017a5de6f5866f9693143a53375e10d7a585f`
was checkpointed under root-only custody and replaced atomically.  The required
69-test target-Linux suite then exposed a nondeterministic pre-existing test
assumption in
`test_heartbeat_and_outcome_cannot_lose_inflight_or_completion`: the adapter's
operation guard is deliberately nonblocking, but the test required the outcome
writer to win every heartbeat/outcome lock race.  The same test failed once in
20 isolated Linux reruns.

The card required rollback on any test failure.  The exact prehash was restored
and independently re-read.  No unit or timer was enabled or started; no lease,
lock, identity, heartbeat, recovery observation, consumer command, model call
or schedule change occurred.

## Revised candidate

The isolated test-only correction is `046c6721eceeb30f30d28fa9703be2a5dcb07c0e`;
the platform-integrated commit is `6386fa5a`.  The corrected test records which
operation lost the expected nonblocking race and retries the outcome after the
heartbeat releases the guard.  Its SHA-256 is
`a51f7a8991508f369eea1b39cdd83e704f5267a38b66df55d2985622b0088f96`.

The revised card is platform commit `c2838763`, with SHA-256
`ac2314bb4ad503a492040f241780ee8c37f2891ba0257759df3bc6e7305fc212`.
Independent validation from its clean archive passed:

- 69/69 focused tests on target Linux;
- 100/100 isolated target-Linux stress reruns of the corrected race test;
- watchdog import/compile validation;
- exact watchdog and test-source hashes; and
- current installed prehash, root custody, inactive units, absent runtime state,
  healthy core guests/Proxmox daemons and unchanged October 26 F2 timers.

This is static and source-only evidence.  A new explicit approval is required
to retry the one-file inactive installation.  The later prepare-only live
exercise remains a separate effectful decision.
