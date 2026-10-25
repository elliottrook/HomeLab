# M3 NLU shadow candidate binding — 2026-10-25

> Status: offline no-effect boundary correction; no shadow run or authority

## Finding and correction

The S0 shadow validator bound its rows to exact interpretation and proposal
artifacts and bound the release to exact frozen-policy bytes. It still accepted
the candidate identity through matching digest fields alone. That left the
same exact-candidate custody gap already closed for calibration.

Shadow bundle validation now also requires the exact sealed candidate manifest.
It validates that manifest and proves that its byte digest is the candidate
named by the frozen threshold policy. The release's existing candidate field
must in turn match that policy, preserving candidate identity across
calibration, threshold selection and no-effect shadow comparison.

## Verification and effect

The focused NLU suite passed **62/62** tests with the bundled workspace Python
runtime on 2026-10-25. Candidate-byte drift fails closed. No shadow cases were
collected, no request was routed, no provider egress or tool execution occurred,
and no authority was granted.

Automatic routing remains off. A selected sealed candidate, calibration
custody, accepted registered policy and frozen threshold are still prerequisites
for any separately controlled S0 comparison.
