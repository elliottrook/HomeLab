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

## Corrected candidate

The platform owner corrected the rejected adapter through commits `792a3312`,
`7a9e1d0f`, `41d3430a`, `e02655bb`, `760f3496`, `c039572c` and final commit
`0e633337`. Stream A reviewed each replacement and required the following
additional boundaries before acceptance:

- exact `quiescing` to observed `running` transition and complete restorable
  production baseline;
- one strict owner/mode/symlink-safe durable state reader shared with the
  independent watchdog;
- fixed deadline, heartbeat and per-workload remaining-budget checks;
- idempotent recovery from `quiescing`, `running` and `restoring`;
- durable D4-before-M3 progression with an in-flight marker written before a
  first request and terminal outcome validation through the pure contract;
- rejection of impossible, foreign, uncertain, duplicate and replayed state;
  and
- descriptor-bound advisory locking for every read-modify-write transition,
  with no-follow, close-on-exec, regular-file, owner and exact-mode custody.

## Independent final verification

Stream A exported exact commit `0e633337` into a clean temporary directory.
The full evaluation-lease suite passed **28/28**, all five Python files
compiled, `git diff --check` passed and the observed hashes matched the final
card:

| Path | SHA-256 |
|---|---|
| `evaluation_lease.py` | `38a986e9d868d04c7ee7814ae0fbd2f1a1709e7a464916195d594ca2bf286312` |
| `evaluation_lease_adapter.py` | `8fac397f96b88be5ccb042a2e3b3da6cbbccdc89e91e4afeacf029a13769c6a1` |
| `evaluation_lease_watchdog.py` | `b6409e9f29d954033ebd2098fdbd983862d0d32eb5de04471f7b06f9aaf74725` |
| `test_evaluation_lease.py` | `d81112eded8d24ded5fde9643b61501f87883936480aa4321f486f13c6cbb6fc` |
| `test_evaluation_lease_adapter.py` | `ce328723dc62d753ec7ab16aeb1bdc254eff6bc7ab851a851f2c77e13fc2e35d` |
| inactive-install card | `4ef9dea4ae4920d3fc7e3c8ecb09da0c35a14ae94c7b04654ef853aaa6738619` |

**Final decision:** **SOURCE ACCEPTED; LIVE EFFECTS REMAIN DISABLED.** The next
adapter gate is a separately reviewed target-Linux inactive installation and
synthetic validation. Fresh F2 and F3 evidence, a production deployment card
and a separate live-run/recovery approval remain mandatory before any consumer
is stopped or either model workload runs.

## Inactive-install packet review

The platform owner prepared the effect-free target packet at commit
`dd886601`. Stream A verified manifest SHA-256
`f14f2e8860c0e783fd9777374393e46b02123ff15125e78f5e43594ea670e83d`
and card SHA-256
`81c9201c41f748c551592bbc9d4a7b797fac913d6f487c7b40af72baafdea14e`.
The manifest contains only the four accepted root-owned mode-`0644` library
sources in a new directory. It declares no entry point, service or timer, and
the source hashes match the accepted review above.

A read-only Proxmox preflight found the destination, evaluation lease state,
lease lock and operation lock absent. `pvescheduler`, `pvestatd`, Aster Agent,
the accepted llama backend, Speech and both News timers were active. The
October 26 F2 one-shot timers remained enabled and active for 01:15 and 01:20
PDT with no current-cycle result or lease. This is an approval-ready inactive
copy, not authorization to perform it and not evidence that F2/F3 or the live
evaluation lease has passed.
