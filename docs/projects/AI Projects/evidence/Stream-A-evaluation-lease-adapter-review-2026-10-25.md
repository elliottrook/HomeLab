# Stream A endpoint-retaining evaluation lease — adapter review

**Date:** 2026-10-25 America/Vancouver

**Platform source reviewed:** `6e29f0e8`

**Decision:** **REJECT FOR INSTALLATION; SOURCE CORRECTION REQUIRED**

## Verified scope

The platform packet adds a source-only adapter, disabled watchdog CLI, focused
tests and an inactive-install card for the accepted pure evaluation contract.
It has not been installed, armed or run. The adapter's command builder
allowlists only LXC104 Aster Agent, LXC116 Speech and the two LXC114 News
timers; it refuses the LXC110 llama backend as a command target. Its default
constructor is effect-disabled and the watchdog CLI reports source-only.

## Blocking findings

1. **Running is declared before isolation is observed.** `acquire()` writes
   `RUNNING` immediately after issuing mask/stop commands. The separate
   `post_quiescence()` validator does not change phase and is not required by
   an adapter-enforced workload gate. A caller can therefore treat the lease
   as running before any exact `masked+inactive` observation.
2. **The recovery baseline is not exact.** Admission requires the registered
   target list, but does not require `ProductionBaseline` to contain those
   exact four targets or their complete restorable enabled/active states.
   Empty, incomplete, duplicate or wrong-state baselines can reach the adapter;
   restore then starts only the recorded entries.
3. **The watchdog is not bound to durable lease state.** Its library function
   accepts free caller-supplied identity-independent deadlines and an arbitrary
   callback. A later effectful wrapper could recover against stale or foreign
   values unless the source contract binds lease ID, generation, phase,
   deadlines and heartbeat to strictly validated durable state.

The platform owner received these exact findings and requested tests. No
target or F2 state changed.

## Consequence

The pure lease contract at `024f3c06` remains accepted. This first adapter is
not eligible for target-Linux installation. D4 candidate-G and M3 calibration
remain unspent; the accepted production backend and all consumers remain in
their ordinary state.
