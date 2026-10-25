# M3 NLU threshold-policy boundary — 2026-10-24

## Result

The NLU holdout now requires the exact frozen threshold-policy artifact, not
only a caller-supplied digest. The new validator fixes a disjoint-calibration
selection method: maximize eligible coverage while every accepted safety and
quality constraint passes, then resolve ties deterministically. A frozen
policy must bind the candidate bundle, calibration artifact and calibration
score, record positive total and per-family sample minima, select a threshold
in the closed interval from zero to one, and attest that the independent
holdout was not accessed.

Privacy underclassification and unsafe false routing have a hard zero
tolerance in every frozen policy. The remaining selective-error and minimum-
coverage values must be accepted and frozen before calibration evidence is
used. The committed template deliberately leaves those values, sample minima,
digests and selected threshold empty. It therefore cannot back a sealed
holdout release and makes no claim that calibration has happened.

The release-bundle validator recomputes the policy file's SHA-256 digest,
requires the policy to be structurally valid and frozen, and compares that
digest to the sealed holdout manifest. Changed bytes, an unfilled template,
post-hoc policy substitution, holdout access and any authority claim fail
closed.

Seventeen focused standard-library tests pass. No candidate score, threshold,
calibration set, private case, label, holdout or route was created or read. No
model ran, and no egress, execution, tool or authority was enabled.

## Remaining gate

Before calibration, the owner must accept the selective-error, coverage and
sample-size constraints. A separate calibration custodian must then provide a
disjoint, reviewed artifact and score for one pinned candidate. Only that
evidence can produce a frozen policy. The independent holdout remains sealed
until the frozen policy is bound into its release manifest. Holdout results
must never be used to revise the threshold.
