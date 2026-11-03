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

A separate 12-case `synthetic-public-development` fixture now exercises valid
single/multi-source plans, mixed usable/unavailable observations, empty and
fully unavailable evidence, secret requests, secret/false-completion prose,
invalid extra model fields, null drafts and visible source ordering. Its 8/8
focused tests pass. The fixture uses generic development identities and contains
no `expanded-*` case ID or spent packet identity.

The no-tool prose runner is also source-ready. Its response schema exposes only
`diagnosis` and `verification`; outcome, checks, effects and authority are not
model fields. Deterministic abstentions skip transport entirely. Malformed,
timed-out, secret-bearing and false-completion responses retain the exact
deterministic plan and fall back to safe prose. The combined envelope,
development and runner suite passes 13/13.

The three exact source inputs are now frozen as `candidate-g` in
`sa3-evidence-envelope-candidate-g-v1.json`. The manifest binds the envelope,
runner and fresh development fixture by SHA-256, records every deterministic
control, and explicitly denies model calls, repair, routing and promotion. Its
validator rejects source drift, missing files, symlinks and any attempted
authority/status widening. The combined candidate suite passes 16/16.

A new, separately frozen 20-case synthetic quality packet and answer-key set
now cover all eight production-shaped evidence classes at least twice and six
mandatory abstentions. The keys are derived from the deterministic envelope,
so they cannot silently widen checks or convert an abstention into a plan.
Packet SHA-256 is `a01c6d71…e3ec2a`; keys SHA-256 is
`73ea6880…564118`. The combined freeze/candidate/runner suite passes 20/20.

The exact packet now also has a key-free batch harness. It binds packet SHA,
candidate alias and result schema; skips all six deterministic abstentions;
issues exactly 14 prose requests with no retry; retains bounded error classes;
and preserves deterministic outcome/checks even after a transport failure. Its
focused and inherited batch suite passes 15/15. This is still source-only and
does not authorize a model call.

The model-blind review boundary is now complete. It accepts only a complete,
error-free 20-row result with exactly 14 prose requests and no retries; removes
the actual model identity and all answer keys; exposes only sanitized case data
and candidate answers; emits an unscored six-dimension template; and rejects
pending, duplicate, identity-exposed, drifted or error-bearing reviews. The
focused and inherited boundary suite passes 14/14.

An exact Lab Hours workload proposal is now ready but explicitly
`not-admitted`. It pins the five runtime files, excludes answer keys and review
code from runtime, allows 20 cases but only 14 prose requests, forbids retries,
tools, effects, repair, restart, routing, scheduling, model change and model
promotion, and requires an authoritative window check, exact booking, whole-
host lease, shared operation lock, guardian and production restoration. The
minimum 3600-second booking contains the 2700-second deadline plus 900-second
recovery reserve. Its focused suite passes 11/11.

## Next gate

The new development fixture, no-tool runner, candidate-g source manifest,
quality packet/answer keys, batch result schema and model-blind review boundary
are complete. The exact workload is now registered and its five runtime files
are staged inactive under the [November 3 result](D4-candidate-g-inactive-registration-result-2026-11-03.md).
The effectful runner remains deliberately unavailable. Its separately reviewed
transaction, authoritative window check, exact booking and one bounded run
remain separately gated. Do not reuse the `candidate-f` result or tune the
prose model against its hidden answers.
