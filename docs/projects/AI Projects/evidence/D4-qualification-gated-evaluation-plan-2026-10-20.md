# D4 qualification-gated evaluation plan — 2026-10-20

## Classification

- **VERIFIED CURRENT STATE:** Stream A has a local, offline plan builder at
  `services/aster-agent/evals/sysadmin_incident_evaluation_plan.py`.
- **REPOSITORY INTENT:** a future D4 evaluation may consume only an incident
  corpus that has completed the explicit human-review qualification boundary.
- **UNKNOWN / REQUIRES VERIFICATION:** no sysadmin model, connected tool,
  production Aster path, or operational outcome has been evaluated by this
  change.

## Result

The plan builder calls `validate_for_qualification` before producing any
output. It therefore rejects both the incomplete canonical intake and the
structurally valid October 19 extension draft. For an isolated synthetic
fixture that represents a completed Jason-reviewed intake, it emits only:

- schema and corpus-schema versions;
- canonical corpus SHA-256;
- case, split and family counts; and
- explicit false values for execution, model-call and tool-call authority.

It emits no case identifiers, symptoms, source descriptions, expected
answers, permitted outcomes or raw evidence. It imports no model, tool,
network or execution adapter. Qualification eligibility is therefore a
necessary input gate, not permission to run an evaluation or promote a model.

## Verification

The focused intake, extension and plan suite passed **16/16** tests on the
Stream A checkout. The tests prove that:

1. the unreviewed extension draft fails closed;
2. the incomplete canonical intake fails closed;
3. a synthetic completed/reviewed fixture produces bounded metadata;
4. private evaluation fields are absent from the output; and
5. changing reviewed corpus content changes the bound digest; and
6. malformed root, case-container, target and review-field types fail closed
   instead of crashing or being treated as reviewed input.

## Practical implication

Offline D4 preparation can continue without accidentally converting an
AI-authored draft into benchmark or promotion evidence. Jason's review of the
real extension remains a separate future gate. Any model call, connected
read-only investigation, or operational role still needs its own reviewed
run card, authority proof and acceptance evidence.
