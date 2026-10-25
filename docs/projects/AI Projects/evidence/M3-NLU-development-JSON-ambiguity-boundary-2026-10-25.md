# M3 NLU development JSON ambiguity boundary — 2026-10-25

> Status: offline development-scorer correction; no routing authority

## Finding and correction

The original NLU development scorer used the standard JSON decoder for its
fixture, run and command-line manifest. Repeated object keys could therefore be
silently resolved by decoder order. The calibration and release validators
already rejected that ambiguity, but the earlier development boundary did not.

The scorer now uses one duplicate-key rejecting decoder at all three file
boundaries. Exact fixture and run digests remain mandatory, so the correction
does not repin or reinterpret any existing evidence. Regression coverage
checks both fixture and run ambiguity.

## Verification and effect

The focused NLU suite passed **54/54** tests with the bundled workspace Python
runtime on 2026-10-25. No private case, model, provider, live route or B60
resource was used.

This change prevents ambiguous development evidence from entering the scorer.
It does not turn development data into qualification evidence, register a
threshold policy or enable automatic routing.
