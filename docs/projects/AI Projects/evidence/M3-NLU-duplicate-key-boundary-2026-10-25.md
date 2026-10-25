# M3 NLU duplicate-key JSON boundary — 2026-10-25

## Problem

NLU threshold-policy, calibration-score and exact calibration-release artifacts
are hash-bound evidence. The standard JSON decoder accepts repeated object keys
and keeps the last value. Another verifier could reject the same bytes or keep
a different value, creating parser-dependent meaning for one digest.

## Correction

The shared NLU JSON decoder now rejects a repeated key at any object depth.
Threshold-policy loading, threshold-selection score loading and exact
calibration-release byte validation use this decoder. The threshold-selection
CLI also validates policy bytes through the same policy loader rather than a
separate permissive parse.

## Validation

The focused NLU suite passes **51/51** under the bundled Python environment.
New tests reject duplicate policy and calibration-score keys; the existing
exact-release, artifact-drift, privacy, safety and no-effect boundaries remain
passing.

This is an offline evidence-parser correction. It reads no private cases,
selects no threshold, enables no routing or egress, and grants no authority.
