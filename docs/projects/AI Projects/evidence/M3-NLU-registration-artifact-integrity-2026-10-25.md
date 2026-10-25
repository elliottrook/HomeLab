# M3 NLU registration artifact integrity — 2026-10-25

Status: offline boundary complete. No policy decision has been accepted, no
candidate or calibration set has been sealed, and no routing authority is
granted.

## Purpose

The registration gate could build a content-free registered policy from exact
accepted inputs, but its returned envelope had no independent validator or
safe persistence primitive. A later stage could therefore consume a mutated,
duplicate-key or partially rebound envelope without first proving that its
policy still matched the candidate and calibration digests at the envelope
boundary.

## Change

`nlu_policy_registration.py` now:

- fixes the exact registration-envelope schema;
- validates all three artifact digests and the embedded registered policy;
- checks candidate, calibration and authority bindings across the envelope;
- rejects duplicate JSON object keys and unknown fields;
- emits deterministic canonical JSON; and
- creates owner-only evidence without overwriting an existing artifact.

The registration builder validates its own result before returning it. The
current proposed decision at digest `2e0def84…64a3d` still fails closed because
its status is `proposed`.

## Verification

The focused NLU suite passes 74/74. Added tests prove canonical round-trip,
candidate-binding drift rejection, unknown-field rejection, duplicate-key
rejection, mode `0600`, and no-overwrite behavior.

## Effect boundary

This change creates no accepted decision, registration artifact, selected
threshold, holdout access, route, model call, egress, tool access or execution
authority. Owner acceptance of the exact policy proposal remains a separate
gate.
