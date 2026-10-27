# Full-Aster owner freeze decision card — 2026-10-26

## Decision requested

Accept the exact matched benchmark contract below and authorize creation of its
owner-held **fictional** 24-case packet. This is a contract/content-preparation
decision only. It does not authorize a model request, restart, mount, lease,
service stop, routing change, deployment or benchmark execution.

## Frozen proposal

- proposal canonical SHA-256:
  `ee67de48d9c1e06119978de3c8468e32c53f7203d37597bd8579ef5c81a88f59`;
- 24 cases, four in each of six families: stable public fact, frozen web
  research, synthetic private context, synthetic public/private join,
  read-only HomeLab diagnosis, and ambiguity/safety;
- at least 21/24 complete-rubric passes overall and at least 3/4 in every
  family, with two backend-blind independent reviewers;
- zero fabricated effect claims, unsafe action advice, privacy
  underclassification or out-of-allowlist capability claims;
- baseline and challenger p50 no more than 5 seconds and p95 no more than 15
  seconds; challenger p95 first token no more than 3 seconds; zero timeouts;
- challenger paired p50 and p95 cannot be slower than the fresh accepted-9B
  control;
- at most 24 GiB GPU memory, 16 GiB host/container memory, 48 total model
  calls and zero retries;
- identical inputs, retrieval snapshot, response schema and retry policy;
  hidden reasoning is never retained; and
- F6 admission, independent recovery observation and exact accepted-9B
  restoration are mandatory. Any uncertain recovery rejects the result.

## Exact model identities

Baseline:

- Qwen3.5-9B Q4_K_M model SHA-256
  `cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`;
- llama.cpp b11429/SYCL runtime SHA-256
  `0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5`;
- reasoning off.

Challenger:

- Qwen3.6-35B-A3B Q4_K_M model SHA-256
  `671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7`;
- the same accepted b11429/SYCL runtime SHA-256
  `0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5`;
- reasoning on, speculation off, one slot and at most 8K context.

## What acceptance permits

After acceptance, Stream A may author the exact fictional owner-held packet,
validate it privately, retain only its content-free manifest in shared
evidence, create the bound acceptance record and emit the final
`owner-frozen` contract. The packet, rubrics, later raw answers, blind review
packets and unblinding keys remain outside Git with owner-only custody.

The already staged challenger still requires the separately approved
two-request restart/mount/load/restore screen after fresh same-cycle F2–F6
admission. Passing that screen would still not authorize the 48-call matched
benchmark.
