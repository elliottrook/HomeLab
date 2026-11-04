# D4 candidate-g r8 independent blind quality NO-GO — 2026-11-04

## Decision

Candidate-g is **NO-GO** on the preregistered quality screen. The R8
transaction completed and restored production exactly, but three distinct
model-identity-blind reviews produced only 10/20 full consensus passes against
the frozen 18/20 requirement. None of the six mandatory deterministic
abstentions passed every dimension. `quality_gate_met=false`.

The decision was produced by the source-frozen three-reviewer rule at mirrored
commit `7182a10f`. That rule was committed before review judgments were read.
It requires the conservative intersection of all three reviewers on all six
dimensions, every abstention, and zero false-completion failures.

## Exact content-free bindings

- result SHA-256:
  `c108cca3b29b3523bc9d23341ed55f767e8c5bbf973d11cfd4f652798dd8809b`;
- blind packet SHA-256:
  `9fe494b93a0595714fe5f6e27b9ff4a3a5fbac08bfc0ea064eaa0436557aedac`;
- canonical review response SHA-256 values:
  `57bff89e84c6fd80fc58093efe84d681d3dccff5453efbb1e5e204cadc129c3e`,
  `f801dcb7d0b173e5ec78bc823a99da05871aeaaada3157df15cb4c3ccfbaea4e`,
  `27c980d117ed18ca6fac783ed4931b94d48986bd9959c2af4b8187f76bc8f63f`;
- content-free decision SHA-256:
  `3b496d0ce2eb226c2f5aafe1ab7291e41631cba11767c48e9a17deb5e2d2f1e9`.

## Aggregate interpretation

Deterministic outcome/check selection was exact 20/20 and all 20 cases passed
the no-false-completion dimension. Consensus dimension pass counts were:
diagnosis 17, evidence 17, freshness 19, scope 17, verification 12 and
no-false-completion 20. Across the six abstentions, every dimension except
verification passed 6/6; verification passed 0/6. The result contained 14
bounded-model drafts and six deterministic fallbacks.

This is a useful safety result but not sufficient investigation quality. The
evaluation packet and reviews are now spent. Do not retry R8, tune candidate-g
against case-level failures, disclose model identity to reviewers, route,
deploy or promote. A successor requires a materially new preregistered design
and untouched quality boundary; other Stream A lanes continue independently.
