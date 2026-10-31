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
  `72074dfc7701a2175e7ee4e3a9334833a976d47c108b8ead5ac82098c7db0026`;
- test SHA-256:
  `099139c3caa39fc26601cda830c620a180524c2fa8011acf53c529d36883b49d`;
- the exact corpus includes the fixed custodian role and uses the same NFKC,
  case-fold and whitespace normalization as every prior calibration receipt.

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

## Custodian draft completed

The corpus custodian has now created the exact deterministic 400-case draft:

- draft SHA-256:
  `b736f0a94125e3b05238d9a54d2d6bdf107005f047c4b120cc43cbf1bf8fcefa`;
- normalized text-set SHA-256:
  `4cd89f296e1c2c5bd5484a6978f9de59b28f8befd407e84405a9e9a9339c1b6e`;
- ontology SHA-256:
  `aa603ab746a1250c8f2089b54e1a3e5b29fc3d01cb3c988bacc198a968bbea44`;
- 320 training and 80 validation cases, exactly 20/5 per coherent label;
- zero normalized overlap with the 24-case public development fixture;
- authority remains `not-granted`.

The generator SHA-256 is
`8743f13078c6c3d4b1a46db60b475188c767168767d21b7f69b7525f9758fd98`
and its test SHA-256 is
`4fdeb394c261133849e7b1500406d58a96c045bd93715387e1f1a86709130351`.
The combined corpus, draft, receipt, ontology, guard and policy suite passes
39/39 tests.

This remains a draft. The custodian cannot self-review its labels or issue the
seven independent private-corpus non-overlap receipts. No training recipe or
model artifact may be frozen until both independent checks pass.
