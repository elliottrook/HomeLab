# M3 J2 corpus quality review and candidate-v2 — 2026-11-04

## Decision

**CANDIDATES V1/V2 RETAINED BUT REJECTED FOR TRAINING QUALITY; V3 AWAITS FRESH REVIEW.**

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
- is retained owner-only and awaits a fresh independent review.

The combined J2 source suite passes 45/45.

## Next gate

Candidate-v3 needs a fresh independent 960-row semantic, naturalness and split-
quality review. V1/V2 review bytes may not be repinned or reused. No training,
evaluation access, model call, authority, routing, service effect or deployment
is admitted.
