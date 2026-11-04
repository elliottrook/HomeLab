# M3 J2 pinned corpus construction result — 2026-11-04

## Result

**CORPUS CANDIDATE CONSTRUCTED; INDEPENDENT LABEL REVIEW OPEN.**

The first real run used the exact pinned development-v1, calibration-v1
through calibration-v6 and J1-v3 raw corpora. It failed closed on one exact
normalized overlap at candidate ID `j2-train-l00-case-13` against `j1-v3`.
No corpus was written by that failed validation. The custodian changed that
one public candidate phrase without reading or using any J1 public-gate failure
detail, artifact, weight, sealed holdout or future evaluation case.

The corrected run passed the frozen validator with:

- 960 cases: 768 training and 192 validation;
- 16 labels with exactly 48/12 rows per label;
- 960 unique normalized requests;
- zero normalized overlap against all eight exact pinned references;
- corpus SHA-256
  `cb5f5a546873a13c6993151d3865ed35377a57427866d7108074bdf49bf0224f`;
- normalized text-set SHA-256
  `42044124548ea48e80bfb10190be834e5ac9f7decc04d2d102c75eb6e1a5f96f`;
- frozen ontology SHA-256
  `aa603ab746a1250c8f2089b54e1a3e5b29fc3d01cb3c988bacc198a968bbea44`;
- authority `not-granted` and automatic routing `off`.

The artifact is retained at the owner-controlled private benchmark location in
a mode-0700 directory as one mode-0600 regular file. Its size is 134,358 bytes
and its independently reread digest matches the validator result. No private
reference text or corpus content is recorded in shared evidence.

## Boundary

This is a corpus candidate, not a release or training admission. A distinct
reviewer must validate every text/label pair and produce the exact self-hashed
review. The later release boundary must cross-bind those bytes and authenticated
custody. No evaluation set was opened or created, no model was trained or
called, and no service, route, authority or deployment changed.
