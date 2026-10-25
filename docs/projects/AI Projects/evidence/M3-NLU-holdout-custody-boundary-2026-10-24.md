# M3 NLU holdout custody boundary — 2026-10-24

## Result

The NLU work now has a content-free sealed-release contract for its independent
holdout. It fixes 36 opaque cases, six for each `request-interpretation.v1`
family, and requires separate case custody, label review, non-overlap review,
evaluation and score-review roles. The manifest pins the interpretation
contract, scorer, threshold policy and separate development/calibration
non-overlap receipts before evaluation.

The validator permits only case identifiers, family names and SHA-256 digests.
It rejects request text, labels, entities, notes, reasoning, answers and other
case fields. It also rejects shared custody roles, duplicate IDs, family drift,
missing provenance, changed manifests and any authority value other than
`not-granted`. The empty template cannot claim evidence or name role sessions.

Eight focused tests pass. The template contains no cases or labels. No private
artifact was created, read or backed up; no human label is claimed; no engine
was run; no route, egress, tool or authority was enabled.

The later [threshold-policy boundary](M3-NLU-threshold-policy-boundary-2026-10-24.md)
closes a structural gap in this first contract: a sealed release must now be
validated with the exact frozen policy bytes whose digest appears here. An
empty policy template or a changed policy cannot satisfy that bundle check.

## Remaining gate

Before a sealed holdout exists, an independent custodian must create the 36
private cases and an independent reviewer must label them under an accepted
protocol. The abstention threshold policy must be frozen from development or
separate calibration evidence before the holdout is opened. The sealed manifest
must then pass this validator and a non-overlap review. Evaluation and scoring
must use the distinct recorded roles. Those future actions need their own data
custody and execution review; this source-only boundary authorizes none of them.
