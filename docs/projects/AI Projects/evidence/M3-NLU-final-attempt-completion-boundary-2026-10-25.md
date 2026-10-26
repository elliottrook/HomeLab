# M3 NLU final-attempt completion boundary — 2026-10-25

Status: **SOURCE FIX PASSED; INSTALLED PACKET SUPERSEDED AND INERT**

## Finding

The calibration runner previously defined completion only as having the frozen
number of records. A transport timeout, unavailable engine or uncertain network
failure normally stops the run early, but the same failure on case 60 still
produces record 60. The command could therefore report `complete: true` and exit
zero despite the run card requiring every transport-uncertain outcome to fail
closed without replay.

No live run or evidence artifact exists, so this defect did not misclassify an
actual calibration result.

## Correction

Completion now requires all frozen records and permits only:

- a valid interpretation record; or
- a completed invalid model response retained as `invalid_response` /
  `response_invalid` for the scorer denominator.

Engine unavailability, transport uncertainty and deadline exhaustion are
incomplete regardless of their position. New regressions cover transport and
HTTP engine failures on the final case; the existing invalid-response case
proves that a fully attempted invalid output still completes.

## Source identities and validation

| Artifact | SHA-256 |
|---|---|
| corrected runner | `88af8eb7f196c03563a31ed2c2fe513d054d491c4903ba4c29dfd765dba36ca0` |
| runner tests | `c9bdc21bafd9bfcdc263c56addd12c29fa88a5bd3ef23ab4c85d04d18c3b555d` |
| corrected stage manifest | `835bcb55ba93d25427b322c6cf93aee06cba1b5e7221af7fb63dbd41d1aab114` |
| corrected manifest validator | `215e221165fafcacb43ccae7230c0cad13a6e19ca9e41ccab9e019f815dc42e5` |

- focused runner and manifest tests: 24/24 passed;
- complete dependency-free NLU suite: 118/118 passed; and
- manifest self-validation: passed with eleven declared inputs and no live
  custody claim.

## Gate impact

The LXC110 packet still contains the prior runner
`a8cca4da…5a0f`. It remains owner-only, output-free and unexecuted, but must not
be used for calibration. A bounded inactive one-file runner replacement using
the corrected manifest and validator, followed by target-Linux tests, is the
next gate. This source correction authorizes no lease, model request, output,
threshold selection, holdout access, route or service change.
