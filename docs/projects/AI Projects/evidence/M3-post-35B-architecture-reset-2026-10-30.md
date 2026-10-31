# M3 post-35B architecture reset — 2026-10-30

## Decision

Do not spend another model run on the rejected 35B joint-semantic prompt or
repair it from the exposed public answers. The prompt-only, decomposed-prompt,
nearest-neighbour, generic-encoder, linear-head, ensemble and stronger-model
whole-label families have each failed an honest gate. Further rubric changes
would be development-set tuning, not new evidence.

M3 remains open, but the next admissible challenger must change the learned
representation and training mechanism rather than the prompt or threshold.

## Candidate-family closure

| Family | Observed limitation | Status |
|---|---|---|
| Direct structured prompting | Safe but semantically inaccurate on public and fresh calibration sets | Closed |
| Decomposed semantic microtasks | Independent fields did not compose coherently; 7/24 exact | Closed |
| Fixed whole-label prompting | Coherence improved but plateaued below 23/24 and traded errors | Closed |
| Lexical, TF-IDF and nearest-neighbour | Cross-set generalization failed | Closed |
| Generic BGE/E5 encoders and linear heads | Fresh-set safety/accuracy policy had no eligible threshold | Closed |
| Ensembles of the above | Did not remove privacy and unsafe-route failures | Closed |
| 35B joint-semantic prompting | Structurally complete 24/24 run failed at least one mandatory public safety counter | Rejected |

The installed result-retention correction is diagnostic only. It does not
reopen any closed family or justify rerunning the same candidate.

## Next admissible architecture: J1

The next candidate may be a compact, locally trained **joint-label classifier**
with these fixed boundaries:

1. It predicts exactly one coherent label identifier from the existing public
   ontology; it cannot synthesize capabilities, authority or a route.
2. Its training corpus is newly generated synthetic data, frozen before model
   training and independently checked for normalized overlap against every
   exposed development, calibration and holdout corpus.
3. Training and selection use only that training corpus. The existing 24-case
   public gate is touched once after the artifact, tokenizer, label map,
   preprocessing and decision rule are digest-bound.
4. Deterministic code still owns privacy floors, deny/abstain rules,
   capability allowlisting and the final no-authority/no-routing envelope.
5. Any confidence or margin is calibrated only on a separately frozen
   synthetic validation partition. No threshold may be selected from the
   public gate result.
6. Admission remains 24/24 structurally valid, at least 23/24 exact, zero
   unsafe false routes and zero routed privacy underclassifications. A failure
   rejects J1 without prompt repair or holdout access.

This is materially different because the semantic representation is learned
for the fixed joint task from a preregistered local corpus; it is not a prompt,
an off-the-shelf embedding distance or a head fitted to an exposed evaluation.

## Offline work order

1. Define the synthetic training/validation schema and frozen label ontology.
2. Implement deterministic normalization and cross-corpus non-overlap checks.
3. Define a reproducible CPU/SYCL-capable training recipe and artifact manifest.
4. Prove source-only parser, custody, no-authority and deterministic-guard
   invariants with synthetic fixtures.
5. Only then decide whether the resulting training workload merits a Lab Hours
   registration and booking.

No AI-stack booking, model change, service restart, calibration creation,
holdout access, route effect or deployment is authorized by this reset.

## First offline boundary completed

`nlu_joint_training_corpus_v1.py` now implements steps 1 and 2 without
creating a corpus. It requires exactly 400 synthetic cases: 20 training and
five validation cases for each of the 16 frozen coherent labels. It rejects
duplicate normalized requests, any overlap with every explicitly supplied
evaluation corpus, label imbalance, metadata drift, duplicate-key JSON and
any authority other than `not-granted`. Its output is content-free digests,
counts and reference bindings only.

- validator SHA-256:
  `8d84e33665057c381051871968de932a88b6e1a6a38989a0ecd8ecf71527f4c4`;
- test SHA-256:
  `ee820c30fa6d5c3a494b4f89791cbce1364550b88a08b1b558eedd98d0a5fac4`;
- focused plus inherited ontology/guard/policy result: 31/31 tests pass.

The validator deliberately accepts reference bytes as inputs rather than
silently using a hard-coded subset. The eventual corpus release must enumerate
and bind every exposed corpus before training begins.

The follow-on `nlu_joint_training_nonoverlap_receipt_v1.py` closes the private
reference boundary without exposing any prior calibration text. It requires
one independently signed, self-hashed zero-overlap receipt for the public
development fixture and calibration v1 through v6. All seven receipts must
bind the same 400-case J1 source and normalized-text-set digests. Missing,
extra, duplicate-key, mismatched-subject, authority-bearing or nonzero-overlap
receipts fail closed. The sealed holdout is deliberately not a reference and
must remain unopened.

- receipt validator SHA-256:
  `466a0fcca7e4f7b18fd77fe031c5d6e3fa79b8fb960861695e6b01e375569a9c`;
- receipt test SHA-256:
  `7d9255f923075d7875f1f4f5ed2e377e628e2bd8cc1a306d4e25a33c75fe62a3`;
- combined J1 corpus/receipt and inherited boundary result: 40/40 tests pass.

This makes the next gate precise: a corpus custodian may create the 400-case
draft, but training cannot begin until a distinct reviewer produces all seven
valid receipts and the labels themselves receive independent review.
