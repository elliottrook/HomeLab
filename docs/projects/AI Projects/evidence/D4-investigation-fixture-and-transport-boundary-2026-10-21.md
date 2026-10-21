# D4 investigation fixture and transport boundary — 2026-10-21

## Decision

Keep the synthetic D4 investigation engine offline. Harden its fixture and
transport boundaries before using it for any future paired model evaluation.
This change grants no model, tool, network, execution or promotion authority.

## Finding

The engine already rejected tool output, effect claims, unseen citations and
invalid answer shapes after a model call. Two earlier malformed inputs could
instead raise uncontrolled Python exceptions or retain incorrectly typed
transport metadata:

- malformed private fixture evidence was only partially checked before the
  transport could be called; and
- a non-object transport response, non-finite latency or malformed bounded
  metadata could reach dictionary operations or the evidence envelope.

These are evaluation-integrity defects. They are not evidence that the local
model or Codex can perform the D4 role.

## Correction

`sa3_investigation.py` now:

- validates and deep-copies the exact private fixture shape before the first
  transport call;
- requires a complete one-to-one capability/response catalogue;
- requires typed, non-empty observations with unique evidence identities;
- converts malformed transport containers into a terminal
  `invalid_transport_response` result; and
- accepts only bounded, typed metadata, rejecting booleans as integer counts
  and non-finite or negative measurements.

Raw transport fields and reasoning content remain excluded from retained
results.

## Verification

- Focused investigation, fair-scorer, evaluation-plan and intake suite:
  **36/36 passed**.
- Complete `services/aster-agent/evals` unit-test discovery: **110/110 passed**.
- Tests prove that malformed fixtures fail before transport invocation and
  malformed transport metadata leaves no retained step.

## Limit

This closes an offline evidence-capture boundary only. It does not review the
incident corpus, call a model, establish diagnostic usefulness, satisfy M1,
connect a tool, authorize a repair or promote a route.
