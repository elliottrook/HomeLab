# M3 NLU calibration journal-to-score binding — 2026-10-25

> Result: **PASS — OFFLINE LINEAGE CORRECTION ONLY**

## Finding

The runner's durable journal made an interrupted or uncertain request visible,
but the calibration scorer did not consume that journal. A final run artifact
could therefore reach threshold selection without proving that every result had
a matching durable `attempt_started` and `attempt_recorded` boundary.

## Correction

Local commit `8253cadf737f6f3209f68c615c31b70da5e62382` adds a strict journal
validator and makes the scorer require it. The validator requires:

- one exact run-start row bound to the sealed candidate and calibration
  artifact;
- exactly one ordered start/result pair for every final run record;
- identical opaque case ID, validity and allowlisted error type;
- no duplicate, missing, extra or ambiguous JSON keys; and
- one complete 60-attempt terminal row.

The resulting score binds `attempt_journal_sha256`, and the threshold selector
requires that digest to be a lowercase SHA-256 value. This carries the exact
custody proof into the frozen policy's already-pinned score bytes.

Pinned corrected digests:

- journal validator: `992960fe76540941fe9adf7b75ddaf82541c55039782bf4cf360ad6c5279a744`;
- scorer: `ec4f4e44ff595617f1fe8e337b587bbab049204d001dd2ba050ee1fb146022fd`;
- threshold selector: `9edc0317fe655bfc49b888d755155393cdc468e11bccc27dbe4881b886922cbb`.

## Verification

The dependency-free NLU suite passes **106/106**. New regressions reject a
journal whose attempt ID differs from the final run and confirm that the exact
journal digest is present in the score. Existing threshold selection, strict
JSON, privacy and unsafe-route tests remain green.

No model request, lease, deployment, holdout access, shadow collection, route,
tool grant or production change occurred. The compatible-lease and bounded
model-call gates remain open.
