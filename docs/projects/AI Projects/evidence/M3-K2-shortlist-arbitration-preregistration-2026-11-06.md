# M3 K2 shortlist/arbitration preregistration — 2026-11-06

**State: source-only design; no runtime authority or effect.**

K2 changes both the representation and error-control path. A fixed Apple
NaturalLanguage embedding shortlister, fitted only on the accepted 768-row
training split, may nominate four coherent joint labels. It cannot make the
final decision. The accepted 9B/SYCL model receives the request plus only those
four content-free label definitions and must select one ID under a strict JSON
schema. Deterministic policy then either accepts the guarded consensus or
abstains.

This is not another prompt-only whole-label run: the model cannot inspect or
choose among the full ontology, the shortlist is produced by an independently
pinned local representation, and deterministic consensus—not model-reported
confidence—controls acceptance. It is also not another fixed-embedding final
classifier because the embedding output is candidate generation only.

Before the single development attempt, Stream A must freeze and test the
shortlister source/runtime hashes, prompt, response parser, consensus policy,
runner and content-free scorer. A later B60 call additionally requires a
registered hash-pinned workload, an exact Lab Hours booking, whole-host lease,
shared operation lock and accepted-service restoration. The 32-case sealed
evaluation remains inaccessible until the 192-case development gate passes.

The development floor is at least 116 accepted decisions, at most 10% error
among accepted decisions, zero unsafe false routes and zero routed privacy
underclassification. Shortlist recall and raw exact are reported diagnostics;
they are not permitted as post-result tuning signals. There is one request per
case, zero retries and no prompt or threshold repair.

This source step authorizes no model call, booking, deployment, route, tool,
service restart, model/backend change or promotion.

Frozen source evidence:

- canonical manifest SHA-256:
  `782cc18f363baede4b1ed5e2b684e489c37a917123a17c9c42d9b55c5985f97a`
- validator SHA-256:
  `a50c68b489fab397332ccc41dc5dd334bdcbf6869c2ddb36a6d1e65e11372938`
- test SHA-256:
  `98036f2b663329f39596b4407ea68175d0b69066c06934e6468671df91933bf6`
- focused K1/K2 tests: `11/11` passed
- K2 syntax compilation: passed with an isolated bytecode cache
