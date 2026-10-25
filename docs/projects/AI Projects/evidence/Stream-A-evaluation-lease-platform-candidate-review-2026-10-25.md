# Stream A endpoint-retaining evaluation lease — platform candidate review

**Date:** 2026-10-25 America/Vancouver  
**Stream A source:** `a4faf905`  
**Platform source reviewed:** `44b26e16a61601c729c9f97df6ef3075d255fe1b`  
**Initial decision:** **REJECTED BEFORE EFFECT**
**Corrected decision:** **PURE CONTRACT ACCEPTED; ADAPTER/INSTALLATION STILL OPEN**

## Scope

This review covers the platform owner's pure Python contract and inactive
install card for an evaluation lease that would keep the accepted LXC110
llama.cpp/SYCL endpoint active while quiescing the registered Aster, Speech
and News consumers. It does not install or run the contract, acquire a lease,
stop a service, call a model, or advance F2/F3.

The exact commit archive passed its seven focused tests. Read-only live checks
also confirmed the production names used by the candidate:

- `lxc110:aster-llama.service` is active/running and its `llama-server`
  process remains present while the endpoint is idle;
- `news-aggregator-ingest.timer` and `news-aggregator-digest.timer` are the
  current LXC114 timer names.

These facts validate the candidate's topology, but the seven tests encode
three unsafe contract assumptions and one ambiguous state boundary.

## Required corrections

1. **Restoration contradicts endpoint retention.** Admission requires the
   exact GPU holder `lxc110:aster-llama.service`, but restoration accepts only
   an empty holder set. The accepted backend remains running at idle in the
   live topology. Restoration must require the exact accepted holder and a
   separate idle/no-inference observation.
2. **The 90-minute window is not actually bound.** The validator checks only
   that restore follows the effect deadline by 15 minutes. It does not bind
   the overall 90-minute window, the resulting 75-minute effect deadline, or
   the 10 + 36 + 20 minute workload budgets. Arbitrary deadline pairs can
   therefore pass.
3. **Lease identity validation is tautological.** `next_workload` validates an
   outcome against the same lease ID and generation supplied by that outcome.
   A stale or foreign outcome can satisfy that comparison. The current lease
   identity must be supplied independently, and the completed-workload list
   must agree with the terminal outcome before M3 can start.
4. **Admission and post-quiescence state are conflated.** The
   `quiesced_targets` field is required before the plan performs quiescence.
   The contract needs separate registered-target and observed-quiescence
   states, with the latter checked after the stop/mask actions and before D4.

The platform owner received these exact corrections in the existing
coordination thread. The requested replacement remains pure and source-only;
installation, arming, F2 changes and workload execution were explicitly
excluded.

## Consequence

The proposed endpoint-retaining lease is not ready for an effectful adapter or
inactive host installation. D4 candidate-G and M3 calibration remain
unspent. Their local fixtures, run cards and inert staging path can continue
independently. A corrected platform commit must pass independent review before
any adapter, watchdog, installation or live-run decision is prepared. Fresh
successful F2 and F3 evidence remains a separate prerequisite.

## Corrected source review

The platform owner first returned `02c60a6d`, which corrected the backend
holder, fixed-window and independent lease-identity defects. Stream A rejected
two remaining fail-open paths: its post-quiescence check compared names without
requiring stopped/masked states, and its completed sequence did not require a
terminal M3 outcome.

Platform commit `024f3c06` closes both remaining paths:

- the exact four registered consumers must each be `masked+inactive` before D4;
- the accepted llama backend must remain the only holder and be authenticated
  and idle after quiescence and after restoration;
- D4 and M3 terminal outcomes must each match the active lease ID, generation,
  frozen packet digest and workload bounds;
- the 90-minute total window, 75-minute effect deadline and 15-minute restore
  reserve are fixed, and the 10 + 36 + 20 minute budgets fit inside the effect
  period.

Stream A reproduced **10/10** tests from the exact commit archive and compiled
both Python files with an isolated bytecode cache. The reviewed hashes match
the platform owner's report:

| File | SHA-256 |
| --- | --- |
| `evaluation_lease.py` | `c521ff753e92d290efe2a2cc6d8d78e8b10b1be86e2a1703f7304783cd3522ca` |
| `test_evaluation_lease.py` | `b29da400849834651679dba114e3d3f26ccea045cce47a7fdafe078100b8b1f9` |
| inactive card | `157f3d0ef40ce3990e4fa0f8393c6e8f99d7658d14d79d6bac10ffd0c24bbb9a` |

This accepts the **pure contract only**. It has no live entry point. The
effectful adapter, independent watchdog integration, target-Linux proof,
inactive installation and later live-run decision remain separate steps. No
platform state or F2 timer changed during this review.
