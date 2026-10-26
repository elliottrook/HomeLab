# M3 NLU TF-IDF KNN cross-set rejection — 2026-10-26

## Candidate

The offline challenger uses deterministic TF-IDF word, word-bigram and
character-ngram vectors, five weighted nearest neighbours and the existing
deterministic privacy/policy/capability guard. Training text exists only in
memory and output is a content-free interpretation label. Three focused public
tests pass.

## Leave-one-set-out result

**REJECT.** Each fold trained on five already-spent sets and evaluated the
sixth. Aggregate-only results were:

| Held-out set | Routed | Correct routed | Selective error | Unsafe false routes | Privacy underclassification | Eligible |
|---|---:|---:|---:|---:|---:|---|
| 1 | 32/60 | 23 | 28.1% | 2 | 0 | no |
| 2 | 39/60 | 30 | 23.1% | 3 | 0 | no |
| 3 | 36/60 | 25 | 30.6% | 3 | 0 | no |
| 4 | 36/60 | 24 | 33.3% | 2 | 0 | no |
| 5 | 36/60 | 27 | 25.0% | 3 | 0 | no |
| 6 | 30/60 | 22 | 26.7% | 3 | 0 | no |

This materially improved coverage and kept routed privacy underclassification
at zero, but every fold violated the error and unsafe-route constraints.

## Nested threshold check

For each outer held-out set, threshold feasibility was assessed only from
inner leave-one-set-out predictions across the other five sets (300 cases).
Candidate thresholds were the observed deterministic vote margins. All six
outer folds had exactly zero inner thresholds satisfying the accepted 60%
coverage, 10% selective-error, zero unsafe-route and zero privacy-
underclassification constraints. The held-out fold was therefore never used
to select a threshold.

No threshold, candidate seal, new calibration or holdout access follows. A
nearest-neighbour representation cannot own the route boundary under the
accepted policy. Automatic routing remains off.

