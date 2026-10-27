# M3 NLU dense supervised head v1 run card — 2026-10-26

## Purpose

Test one materially distinct supervised semantic head over the fixed BGE dense
representation. This is the registered successor to the rejected nearest-
neighbour boundary. It is exposed-set development only and grants no authority.

## Frozen source

- regularized kernel-mean head:
  `nlu_encoder_head_v1.py`, SHA-256
  `2d58861c5f2e9c71a7da9ccef80f6f2048bdd86851f7782f07c09e23b230e152`;
- honest nested evaluator:
  `nlu_encoder_head_crossset_v1.py`, SHA-256
  `e3000a277d35c6bbd82efa31f6e35aff2f640e18d795c2a82a50bfe360cb3410`;
- owner-only runtime:
  `nlu_encoder_head_runtime_v1.py`, SHA-256
  `2565131dbc14cdbc15bedb09c548623f6a77ced7f4804589b5f91324113952b1`;
- shared frozen vector loader:
  `nlu_encoder_runtime_v2.py`, SHA-256
  `f1532fcbab4d9c5b4388509a146f22c0b5da31d166b9b9a1278b5afdbdd22789`;
- accepted v2 decision artifact SHA-256:
  `7ed394720af72169d6bff49603ffdd788e417acbae60751b5893c3f8494752a9`;
- dependency-free NLU suite: **375/375**.

For each training partition, the head learns a similarity mean for each
reviewed field value and shrinks it toward the partition-wide mean. It scores
only complete interpretation labels observed in that partition. Shrinkage,
temperature and policy thresholds are selected only from the five-set inner
partition for each untouched outer set. Route confidence remains bounded by
disposition, sensitivity and capability support.

## Runtime boundary

Use the same temporary CPU-only loopback BGE Q4_K_M artifact at SHA-256
`363a0a4855dff6c653e06efe3209157debcf7f74e52d0d7c71e2747cd523043e`.
Do not stop, replace, reconfigure or restart the accepted 9B/SYCL service.
Private cases may reach only the LXC110 loopback encoder and may exist only in
owner-only temporary storage; vectors stay in memory.

Retain only source/label digests, counts, selected aggregate parameters,
thresholds, aggregate fold metrics, elapsed time and terminal-result digest.
Remove all temporary model, source, private inputs and output after bounded
reconciliation, then verify the lease and production services are unchanged.

## Decision

- **PASS:** all six outer folds meet at least 60% decision coverage, at most
  10% accepted-decision error, zero unsafe false routes and zero routed privacy
  underclassification. A pass permits proposing a fresh independent
  calibration; it does not permit creating or opening one automatically.
- **REJECT:** any missing inner threshold or failed outer constraint rejects
  this learned-head family. The next candidate must change encoder family, not
  tune this head against the same spent sets.

No holdout access, routing, deployment, service restart, model replacement,
tool grant, egress or Forgejo push is authorized.
