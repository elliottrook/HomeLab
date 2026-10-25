# M3 NLU policy registration gate — 2026-10-25

> Status: offline registration gate; current proposal deliberately rejected

## Result

A deterministic registration gate now constructs
`aster-nlu-threshold-policy.v1` only from three exact inputs:

1. a valid `accepted` policy-decision artifact with an exact acceptance record;
2. a valid sealed candidate bundle; and
3. a valid sealed calibration release bound to that candidate and meeting every
   accepted total and per-family sample minimum.

The registration receipt retains exact decision, candidate and calibration
digests. Its embedded policy copies the accepted constraints without alteration,
binds the exact candidate and calibration release, attests that the holdout was
not accessed, contains no selected threshold or calibration score, and grants
no authority.

The current proposal at `2e0def84…64a3d` is intentionally rejected because its
status remains `proposed` and it has no acceptance record. Candidate byte drift,
candidate/release mismatch and weaker calibration minima also fail closed.

## Verification and effect

The focused NLU suite passed **72/72** tests with the bundled workspace Python
runtime on 2026-10-25. Only synthetic fixtures were used. No real acceptance was
recorded, no policy was registered, no candidate or calibration release was
created, and no routing, model call, egress, tool use or authority followed.

This makes the remaining order explicit: owner acceptance, exact candidate
selection/sealing, independent calibration custody, then deterministic
registration before any calibration score is inspected.
