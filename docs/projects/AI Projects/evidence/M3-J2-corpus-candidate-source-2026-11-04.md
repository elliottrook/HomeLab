# M3 J2 corpus candidate source — 2026-11-04

## Decision

**DETERMINISTIC CANDIDATE SOURCE READY; PRODUCTION REFERENCE VALIDATION AND
INDEPENDENT LABEL REVIEW STILL REQUIRED.**

The independent J2 corpus custodian added an offline natural-language builder
and focused tests. The builder deterministically creates 960 unique requests:
48 training and 12 validation requests for each of the 16 frozen coherent
labels, for totals of 768 and 192. Validation uses two held-out request subjects
per label; those subjects do not occur in that label's training rows.

The builder accepts exactly these eight named raw JSON inputs:
`development-v1`, `calibration-v1` through `calibration-v6`, and `j1-v3`.
It passes their bytes and the generated corpus directly to
`nlu_j2_corpus_v1.validate_corpus`. The production path neither substitutes
release receipts nor discovers references implicitly. The frozen validator
therefore remains responsible for exact artifact digests, normalized text-set
digests, case counts, zero overlap, the preregistration manifest, and the
frozen ontology digest.

## Boundary and construction

- The corpus is assembled from explicit, label-specific natural-language
  subjects and request forms. No model, endpoint, network, pretrained weight,
  prior candidate artifact, or public failure detail is an input.
- The existing sealed holdout and the future sealed J2 evaluation boundary are
  not read or named by the builder.
- The generated metadata keeps authority at `not-granted`; the validator's
  content-free summary keeps automatic routing off.
- The command-line interface creates one new owner-only mode-0600 canonical
  corpus path with no overwrite or symlink following, and writes only the
  content-free validation summary to standard output. It has no training,
  booking, tool, service, route, or deployment behavior.
- No corpus fixture is frozen by this source milestone. Production emission
  remains fail-closed until the custodian is given the exact eight pinned raw
  reference files, including the private request-source calibration corpora.

## Verification

Focused tests patch only the validator's expected reference inventory to the
digests of test-local synthetic fixtures. The production inventory is never
changed. This exercises construction and the frozen validation path without
pretending that calibration release receipts contain request text.

The combined candidate and frozen-validator suite passes 13/13 tests. It
checks deterministic bytes, 960 normalized-unique rows, exact per-label split
balance, held-out validation subjects, the exact eight reference names,
missing/extra/renamed-reference rejection, overlap rejection, required CLI
arguments, no-authority metadata, and the inherited validator failures.

- candidate builder SHA-256:
  `0c7a21c7a2397845ff44243c3f4582aa00ccc627f21ee6971b5ebb345ada5284`;
- focused test SHA-256:
  `b01c9e4f4a62228bb5fec04e6dd471fcbdc4b9b2ea18e1df7f961278ba6eb5a6`;
- generated candidate source SHA-256:
  `9c26cf64eadd09f00414162ce71dd9079a5a0666fcae6040c7a1a385473bde22`;
- generated normalized text-set SHA-256:
  `59118408be95fab84e840d9397cb2e712624cb01135b763e441893b8eaeb3764`;
- preregistration manifest SHA-256:
  `2abcd02371b087ebc6db95b04dd271b518624cd063ffeb4612341bcb4c1b97ee`;
- frozen ontology catalogue SHA-256:
  `aa603ab746a1250c8f2089b54e1a3e5b29fc3d01cb3c988bacc198a968bbea44`.

These results authorize no training, corpus promotion, evaluation access,
runtime effect, routing, deployment, commit, or push. A distinct reviewer must
still inspect every generated text/label pair after exact pinned-reference
validation succeeds.
