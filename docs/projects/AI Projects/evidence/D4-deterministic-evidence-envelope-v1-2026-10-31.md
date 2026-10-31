# D4 deterministic evidence envelope v1 — 2026-10-31

## Outcome

A materially different offline D4 architecture is source-ready after the
`candidate-f` NO-GO. Deterministic code now owns the plan/clarify decision,
the exact evidence set, empty-check abstention, no-effect result and authority
boundary. A model may draft only diagnosis and verification prose; invalid,
secret-bearing or false-completion prose is replaced by a deterministic safe
fallback.

This is development evidence only. It has not been run against the spent
`candidate-f` packet, does not call a model, and grants no routing, repair,
deployment or model-promotion authority.

## Failure addressed

`candidate-f` selected the expected evidence sources in most cases but treated
bounded diagnostic plans as clarification. It also selected evidence on all
four mandatory abstention cases. The old architecture asked one model response
to control outcome, evidence selection and prose.

The replacement separates those responsibilities:

1. validate the visible capability and observation envelope;
2. treat only `ok`, `warn` and `fail` observations as usable;
3. emit `clarify` with no checks for missing/unavailable evidence or secret
   requests;
4. otherwise emit `plan` with exactly the usable visible source IDs, preserving
   their visible order;
5. accept only a two-field bounded prose draft (`diagnosis`, `verification`);
6. replace malformed, secret-bearing or false-completion prose with a
   deterministic evidence summary; and
7. always emit no effects and `authority=none`.

## Validation

The focused and inherited offline suite passes 22/22. Tests prove that model
fields cannot alter outcome or evidence, missing/unavailable evidence abstains
with an empty check set, secret requests abstain, false-completion/secret prose
falls back safely, multi-source order is deterministic and all outputs remain
effect-free.

## Next gate

Create a new public/synthetic development fixture that is not the spent
expanded-source packet, then freeze a new candidate, new answer-key packet and
new model-blind review boundary. Do not reuse the `candidate-f` result or tune
the prose model against its hidden answers.
