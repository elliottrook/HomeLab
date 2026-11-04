# M3 J2 corpus quality review and candidate-v2 — 2026-11-04

## Decision

**CANDIDATES V1–V3 RETAINED BUT REJECTED; V4 IS THE AI-REVIEWED CORPUS RELEASE CANDIDATE.**

The distinct label reviewer inspected all 960 candidate-v1 rows. Every assigned
label matched the frozen ontology (`accepted=960`, `corrected=0`), but the
review found 26 awkward rows and systematic frame reuse. Candidate-v1 had only
546 unique four-token openings and a maximum opening reuse of 30. Its valid
label review is retained under owner-only custody but is not transferable to a
changed corpus and does not make candidate-v1 release-quality.

The public generator was revised without reading any sealed evaluation or
holdout and without using J1 public-gate failures. Candidate-v2:

- retains 960 rows with the exact 48/12 split for all 16 labels;
- retains zero normalized overlap against all eight pinned references;
- has SHA-256
  `d5f8a1b6be4daa1cd99f66fd8959849b2084c682be462c365ff6c02978544190`;
- has normalized text-set SHA-256
  `cc5930154505bd7972b697b8872fa070097dad6b0f1bf8cc453fdc8d4935bf4c`;
- has 907 unique four-token openings, maximum reuse 4 and request lengths from
  3 through 17 words;
- is retained as one 127,492-byte mode-0600 file in a mode-0700 owner-controlled
  directory.

The generator initially enforced at least 900 unique four-token openings,
maximum reuse 4 and bounded request length before writing a candidate. The
fresh candidate-v2 review again accepted all 960 semantic labels but found 107
awkward rows plus the deeper issue that training and validation reused the same
six frames per label. V2 is therefore retained but rejected; its accepted-label
review cannot transfer.

Candidate-v3 corrects every listed grammar/capitalization issue and gives each
label six validation-only frames disjoint from its training frames. Its
naturalness floor is at least 850 unique four-token openings with maximum reuse
4, now paired with an explicit train/validation frame-disjointness test. V3:

- retains the exact 960-row, 48/12-per-label shape;
- has zero overlap against all eight pinned references;
- has SHA-256
  `9c26cf64eadd09f00414162ce71dd9079a5a0666fcae6040c7a1a385473bde22`;
- has normalized-set SHA-256
  `59118408be95fab84e840d9397cb2e712624cb01135b763e441893b8eaeb3764`;
- has 872 unique four-token openings, maximum reuse 4 and 3–17 words;
- is retained owner-only.

The fresh candidate-v3 review accepted all 960 semantic labels but rejected
promotion on 14 precise naturalness defects: number disagreement in backup and
calendar requests, malformed general-answer questions, and four unidiomatic
physical-task frames. Candidate-v4 changes only those public source frames.
Its real pinned-reference build has:

- corpus SHA-256
  `9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a`;
- normalized text-set SHA-256
  `a53f0bb3c747f82fdacffe9e76853830a0473c55d7d578ca1d1cb9b8358b51d0`;
- zero normalized overlap against the exact eight pinned references;
- 871 unique four-token openings under the source-defined tokenizer, maximum
  reuse 4 and request lengths from 3 through 17 words;
- an exact 768/192 split and 48/12 rows for every one of 16 labels.

A fresh independent AI review inspected all 960 rows, confirmed that all 14
v3 defects were resolved, found no semantic, grammar, naturalness or split-
quality defect, and returned **PROMOTE** with 960 accepted and zero corrected.
The mode-0600 review is bound to the v4 source bytes by artifact SHA-256
`896ff54b31718b7dfbe91b479c4a6fbcfe5b428ca62528f07a2f8993072b0028`
and self-hash
`75c86481cc04394787faf9cc7c6055f74dc5e262167e8491bfe09b1acf7f6bde`.

Because the original label-review schema did not durably record prose quality,
a separate fail-closed quality-review contract was added rather than relying on
chat evidence. Its fresh 960-row artifact records explicit grammar,
naturalness, semantic-label and split-quality passes for every row, has SHA-256
`f934ee6780c3f9a4b87b7c530a4345080dd98ff534e7d5a3093822aed1d3fe3f`
and self-hash
`408e7479e106f614b2a2011da624c10af4ca6919d30d4cccd93dcf242fec4a35`.

The complete J2 source suite passes 50/50.

## Next gate

Candidate-v4 is the first corpus candidate that passes the frozen structural,
overlap, semantic, naturalness and split-quality gates with those judgments
retained in exact-source-bound artifacts. It is ready for the
owner review Jason requested at release-candidate quality. Corpus release still
requires externally controlled custody evidence; a shared-agent identity string
or self-hash cannot manufacture that proof. No training, evaluation access,
model call, authority, routing, service effect or deployment is admitted.
