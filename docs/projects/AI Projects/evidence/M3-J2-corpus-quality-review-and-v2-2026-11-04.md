# M3 J2 corpus quality review and candidate-v2 — 2026-11-04

## Decision

**CANDIDATE-V1 RETAINED BUT REJECTED FOR TRAINING QUALITY; V2 AWAITS FRESH REVIEW.**

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

The generator now enforces at least 900 unique four-token openings, maximum
reuse 4 and bounded request length before writing a candidate. The full J2
source suite passes 36/36.

## Next gate

Candidate-v2 needs a fresh independent 960-row semantic and naturalness review.
Candidate-v1's review bytes may not be repinned or reused. No training,
evaluation access, model call, authority, routing, service effect or deployment
is admitted.
