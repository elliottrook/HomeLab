# Stream A post-F2-activation offline continuation — 2026-10-26

After the October 27 F2 timers were activated, Stream A continued the wider
Aster programme without waiting for the timed window.

## NLU revalidation

The current formal NLU source passed all 130 tests selected by
`test_nlu*.py` under the workspace Python 3.12 runtime with Pydantic available.
This includes the interpretation scorer, candidate bundle, calibration
custody/runner/journal/score, policy acceptance/registration/selection,
independent holdout and no-effect shadow boundaries.

The host's system Python 3.9 lacks Pydantic and therefore cannot import the
Pydantic benchmark module; this is a test-environment dependency distinction,
not an NLU contract failure. No model request, threshold selection, holdout
access, shadow collection or route activation occurred.

## F6 current-packet gate

The current-packet validator and fixed-Doctor boundary tests passed 15/15.
Applying the validator to the existing platform F6 candidate-H card still
fails exactly as expected: the card omits the installed V3 paths, final M3
runner/scorer/journal/packet identities and LXC104/LXC110 guest bindings, and
contains two superseded digests. It remains invalid authority for F6.

The platform owner was sent the exact validator and requirements artifact for
the replacement source-only card. No watchdog was armed, no lease or receipt
was created, no consumer stopped and no model was called.
