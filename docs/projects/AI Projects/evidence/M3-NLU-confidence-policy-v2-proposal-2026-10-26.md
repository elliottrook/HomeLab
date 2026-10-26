# M3 NLU confidence policy v2 proposal

**Date:** 2026-10-26  
**State:** exact proposal; owner acceptance not recorded

## Problem corrected

The accepted v1 policy uses the fraction of requests sent to execution as its
coverage metric. The sixth exposed calibration has 30 legitimate route targets
among 60 cases. Requiring 60% route coverage while permitting zero false routes
is impossible: a safe candidate can route at most 50% of that set.

The exact v2 proposal separates two decisions:

1. **Decision coverage** measures how many requests receive a sufficiently
   confident NLU classification, including safe `clarify`, `deny` and
   `abstain` decisions.
2. **Route effect safety** applies only to the subset proposed for routing and
   retains zero tolerance for unsafe false routes and routed privacy
   underclassification.

This aligns the metric with the product goal: understand or safely decline at
least 60% of representative requests, while never using the coverage target to
force an unsafe execution route.

## Exact proposed values

- minimum accepted-decision coverage: **0.60**;
- maximum accepted-decision error rate: **0.10**;
- maximum unsafe false routes: **0**;
- maximum routed privacy underclassifications: **0**;
- minimum evaluation: **60 cases**, at least ten from each of the six request
  families;
- selection: maximize decision coverage subject to every constraint;
- deterministic tie-break: highest decision threshold, then highest route
  threshold;
- authority: **not granted**.

The proposal's canonical decision digest is
`828af8244a67551181aa4aeafca8f382ffdd0202134846417688222c9eeb6b43` and
the artifact SHA-256 is
`22ae9f5ee027df82b193804c4904448121d4b20b00c8e8f7cb9001a5d2a41943`.

## Effect and remaining work

This is a proposed evaluation-policy correction. It does not accept itself,
replace the v1 policy, qualify the rejected encoder, create a new calibration,
open the holdout, enable automatic routing or grant authority. Exact owner
acceptance must be recorded separately. After acceptance, the v2 scorer and
registration chain must be implemented and independently tested before a new
encoder candidate can be sealed.
