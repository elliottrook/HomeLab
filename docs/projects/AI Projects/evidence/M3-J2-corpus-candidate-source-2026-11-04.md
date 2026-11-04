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
  `4310df60d21c0b02874525c4ed5dedb249be91ae17d771842dcab060e0822374`;
- focused test SHA-256:
  `1cb351ef585668ca21687757d68d3afa9c5919fe54a21a223d0bad22c8200ccb`;
- generated candidate source SHA-256:
  `cb5f5a546873a13c6993151d3865ed35377a57427866d7108074bdf49bf0224f`;
- generated normalized text-set SHA-256:
  `42044124548ea48e80bfb10190be834e5ac9f7decc04d2d102c75eb6e1a5f96f`;
- preregistration manifest SHA-256:
  `2abcd02371b087ebc6db95b04dd271b518624cd063ffeb4612341bcb4c1b97ee`;
- frozen ontology catalogue SHA-256:
  `aa603ab746a1250c8f2089b54e1a3e5b29fc3d01cb3c988bacc198a968bbea44`.

These results authorize no training, corpus promotion, evaluation access,
runtime effect, routing, deployment, commit, or push. A distinct reviewer must
still inspect every generated text/label pair after exact pinned-reference
validation succeeds.
