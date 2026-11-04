# M3 J2 corpus-v4 owner review card — 2026-11-04

## Decision requested

Candidate-v4 is the first J2 corpus candidate that passes the complete frozen
structural, disjointness, semantic-label, grammar, naturalness and split-quality
standard. The owner decision is **ACCEPT FOR CORPUS RELEASE** or **REVISE**.

Acceptance concerns only the synthetic corpus release candidate. It does not
authorize training, access to a sealed evaluation set, a model call, deployment,
automatic routing, tools or any production effect.

## Exact review object

- owner-only corpus:
  `/Users/jelliott/lab/private-benchmarks/aster-stream-a/j2-corpus-candidate-v4-20261104/corpus.json`
- corpus SHA-256:
  `9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a`
- normalized text-set SHA-256:
  `a53f0bb3c747f82fdacffe9e76853830a0473c55d7d578ca1d1cb9b8358b51d0`
- owner-only independent-AI review:
  `/Users/jelliott/lab/private-benchmarks/aster-stream-a/j2-corpus-candidate-v4-20261104/label-review-independent-ai.json`
- review artifact SHA-256:
  `896ff54b31718b7dfbe91b479c4a6fbcfe5b428ca62528f07a2f8993072b0028`
- review self-hash:
  `75c86481cc04394787faf9cc7c6055f74dc5e262167e8491bfe09b1acf7f6bde`
- owner-only independent-AI quality review:
  `/Users/jelliott/lab/private-benchmarks/aster-stream-a/j2-corpus-candidate-v4-20261104/quality-review-independent-ai.json`
- quality-review artifact SHA-256:
  `f934ee6780c3f9a4b87b7c530a4345080dd98ff534e7d5a3093822aed1d3fe3f`
- quality-review self-hash:
  `408e7479e106f614b2a2011da624c10af4ca6919d30d4cccd93dcf242fec4a35`

All three artifacts are regular mode-0600 files in a mode-0700 owner-controlled
directory. The label review covers all 960 rows, accepts all 960 labels and
records zero corrections. The separately validated quality review records an
explicit pass for grammar, naturalness, semantic-label quality and split quality
on every row, confirms all 14 v3 defects resolved and finds no new defect.

## Frozen quality facts

- 768 training and 192 validation rows;
- exactly 48/12 rows for each of 16 coherent joint labels;
- 960 normalized-unique texts;
- zero normalized overlap against the exact eight pinned exposed references;
- zero train/validation exact-text overlap;
- zero within-label train/validation four-token-prefix intersection;
- 871 unique four-token openings under the source-defined tokenizer;
- maximum four-token-opening reuse 4;
- request length 3–17 words;
- validation subjects and frames held out from training;
- authority `not-granted`; automatic routing `off`.

## Fail-closed owner response

An acceptance should name all three exact artifact hashes and say they are accepted
for **corpus release only**. Any requested wording, label, naturalness or split
change produces new corpus bytes and requires a fresh complete review. Silence,
an ambiguous response or a hash mismatch is not acceptance.

Owner acceptance is necessary but does not manufacture the separately required
external custody proof. Before the release validator can return an eligible
summary, an independently controlled signer or equivalent separate-account
record must bind the exact corpus, normalized-set and both review artifact hashes.
