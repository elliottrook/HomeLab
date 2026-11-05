# D4 candidate-i blind-review and decision boundary — 2026-11-04

## Result

Candidate-i's post-run path is source-complete before its first booked result
exists. The new schema-v2 boundary accepts only the exact untouched packet and
a complete candidate-i result containing 20 rows, exactly 14 model requests,
six deterministic no-transport abstentions, no errors, no retries, no effects,
no authority and automatic routing off.

The blind packet removes the model identity, per-row model identity, transport
flag, finish reason, latency, answer keys and runtime metadata. It exposes only
the synthetic prompt, observations, registered capabilities and candidate
answer. Every review is bound to the canonical packet digest and must score all
six frozen dimensions for all 20 rows.

The decision path requires exactly three distinct model-blind reviewers and
uses their conservative intersection. It passes only at 18/20 or better when
all six deterministic abstentions pass and there are zero false-completion
failures. Even a pass leaves authority `none`, automatic routing `off` and
promotion `not-authorized`.

## Frozen source

- blind packet and response validator:
  `6c3cd5a1a35f19cbb1e321bcd84f26346996430bbbd8f41651991ff6e3fc8c43`
- terminal reconciliation:
  `3d9530f790246d3c5b87f1021b1eec09515ca89a3f9d48b1227e7cd2819bdb2b`
- three-reviewer decision:
  `6b1794ee97015764496e7bcd5cb8d48d7c51b526249398e930103ab9076357b7`

The focused candidate-i suite passes 33/33, including packet/result drift,
transport-on-abstention, wrong request counts, runtime errors, incomplete or
identity-exposed reviews, duplicate reviewers, conservative threshold,
mandatory-abstention and false-completion failures. The reconciliation CLI
writes the blind packet exclusively at mode 0600 and emits only a content-free
summary.

## Boundary

This milestone does not inspect the untouched packet's answer keys during
runtime, invoke a model, read the scheduled result, pre-score a case, authorize
a retry, disclose model identity or promote a route. Candidate-i R1 remains a
single dispatcher-owned attempt. These frozen modules may be applied only if
the terminal transaction and independent production postchecks are complete.
