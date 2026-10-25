# M3 NLU holdout candidate binding — 2026-10-25

> Status: offline qualification-boundary correction; no holdout access

## Finding and correction

The independent holdout release pinned exact frozen-policy, contract, scorer
and development non-overlap bytes. The frozen policy carried the candidate
digest, but the holdout gate did not receive the candidate manifest itself.
That left candidate validity and exact byte identity outside the final
qualification boundary.

Holdout bundle validation now requires the exact sealed candidate bytes,
validates their content-free manifest and canonical digest, and verifies that
their SHA-256 is the candidate named by the frozen threshold policy. Candidate
identity is therefore continuous from calibration through threshold selection,
S0 shadow evidence and independent holdout custody.

## Verification and effect

The focused NLU suite passed **63/63** tests with the bundled workspace Python
runtime on 2026-10-25. Exact candidate drift fails closed. The test used only
synthetic fixtures; it did not open a holdout, call a model, route a request,
attempt provider egress or grant authority.

The qualification gate remains unopened. No candidate is selected or sealed,
and no holdout cases or labels have been created under this boundary.
