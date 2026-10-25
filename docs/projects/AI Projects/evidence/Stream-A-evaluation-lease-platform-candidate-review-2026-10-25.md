# Stream A endpoint-retaining evaluation lease — platform candidate review

**Date:** 2026-10-25 America/Vancouver  
**Stream A source:** `a4faf905`  
**Platform source reviewed:** `44b26e16a61601c729c9f97df6ef3075d255fe1b`  
**Decision:** **REJECT FOR EFFECTFUL ADAPTER; SOURCE CORRECTION REQUIRED**

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
