# M3 NLU dense encoder v1 — exposed cross-set result

**Date:** 2026-10-26  
**Decision:** **NO-GO — do not create another calibration**

## Candidate

This is the first Stream A NLU candidate using a dedicated sentence encoder
rather than a chat prompt, literal recognizer, sparse lexical vector or larger
generative model. The temporary runtime used BGE small English v1.5 Q4_K_M on
the retained llama.cpp embedding binary, CPU-only, while the accepted 9B/SYCL
service remained active.

- upstream model revision:
  `d32f8c040ea3b516330eeb75b72bcc2d3a780ab7`;
- temporary GGUF SHA-256:
  `363a0a4855dff6c653e06efe3209157debcf7f74e52d0d7c71e2747cd523043e`;
- vector shape: **384 cases × 384 dimensions**;
- inputs: the 24 public development cases plus all six already-spent,
  exposed 60-case calibration sets;
- private text and vectors remained owner-only and are not retained in Git.

Five cosine neighbours with eighth-power weighting propose the six semantic
fields. A separate deterministic envelope accepts a decision only when the
minimum per-field support is at least 0.60, and accepts a proposed route only
when route support is at least 0.70. The output carries no authority and
automatic routing remains off.

## Result

A direct post-hoc application of those two thresholds across the six exposed
leave-one-set-out folds looks compliant: accepted decisions were
`36, 51, 41, 52, 50, 37` out of 60, accepted error rates were at most 10%, and
there were zero unsafe false routes and zero routed privacy
underclassifications. That result cannot qualify the candidate because the
thresholds were observed against all six exposed folds.

The nested check selected thresholds only from each outer fold's other five
sets. It failed:

- two of six outer folds had no threshold satisfying the inner constraints;
- one selected outer result produced **one unsafe false route**;
- another selected outer result had **18.6% accepted-decision error**;
- only two outer folds met all four constraints.

The representation is materially better than the rejected TF-IDF neighbour
and semantic-prompt candidates, but its safe boundary is not stable enough for
a new independent calibration. Do not seal, promote, open the holdout or enable
automatic routing.

## Policy discrepancy found

The accepted v1 threshold scorer defines `coverage` as the fraction of all
requests whose proposed disposition is `route`. Calibration v6 has only 30/60
legitimate route targets. The accepted policy simultaneously requires at least
60% coverage and zero unsafe false routes. Those conditions are mathematically
incompatible for that set: zero false routes caps route coverage at 50%.

This experiment therefore keeps the accepted policy unchanged but separates
**decision coverage** from the later **route effect** in source. A revised
owner decision is required before that meaning can become an acceptance rule.
The proposed interpretation is: confidence coverage measures all accepted NLU
decisions, while unsafe-route and privacy constraints independently govern the
subset that would direct work.

## Production postcheck

The accepted `aster-llama.service` stayed active with zero restarts. No model,
service, route, grant, policy, timer or schedule changed. Temporary encoder
weights, request text and vectors are removed after evidence capture.
