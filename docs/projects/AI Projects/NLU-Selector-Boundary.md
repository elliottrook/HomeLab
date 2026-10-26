# Aster NLU and selector boundary

> Status: offline candidate; no live routing or authority
>
> Owner: Jason
>
> First contract: `request-interpretation.v1`

## Purpose

Aster needs an explicit boundary between understanding a request and deciding
where or how it may be handled. The NLU stage describes the request. The selector
uses that description and current policy to propose a route. AI-PAM separately
decides whether a caller may use any connected capability. None of these records
is an authorization token.

```text
request -> deterministic privacy checks -> NLU interpretation
        -> digest-bound route proposal -> authority projection -> execution
```

The existing deterministic household path remains available before model-based
classification. A model or semantic classifier may later implement the NLU stage,
but it must emit the same bounded record and pass the same evaluation gate.

## `request-interpretation.v1`

The offline contract in `scripts/aster-adaptive/contracts.py` records:

- bounded request family;
- public, internal or personal sensitivity;
- zero to eight non-authoritative capability needs;
- clear or ambiguous classification;
- route, clarify, abstain or deny disposition;
- bounded reason code;
- exact NLU engine and policy digests; and
- literal `authorization: not-granted`.

It deliberately excludes prompt text, extracted entity values, reasoning,
credentials, tool arguments, provider choice and uncalibrated confidence. Its
semantic validator rejects contradictory family, ambiguity, disposition and
reason combinations. Duplicate or oversized capability lists fail closed.

`route` means only that a downstream selector may consider the request. It does
not approve cloud egress, select a model, project a capability or grant a tool.
A change request may be understood and routed while still having no permission
to change anything.

`route-proposal.v1` separately records local, Codex, clarify, abstain or deny;
the backend and local/cloud/no-egress class; bounded reason; policy and expiry;
and literal `authorization: not-granted`. It is bound to the canonical
interpretation digest plus the same request, principal and policy. The first
profile cannot route personal content to cloud because it has no consent
artifact. A later consent design requires a new reviewed contract version.

## Separation of responsibility

| Stage | May decide | Must not decide |
|---|---|---|
| Deterministic prefilter | obvious household command, explicit privacy block, fixed local-only rule | general tool authority |
| NLU | family, sensitivity, capability needs, ambiguity | provider, grant, execution |
| Selector/policy | local/Codex/provider candidate, clarify or abstain, egress eligibility | tool permission |
| AI-PAM | caller-bound, expiring capability projection | request meaning or answer quality |
| Executor | use the exact projected capability within budget | broaden scope or reinterpret approval |

## Evaluation and promotion gate

The current 30 exposed development cases are useful regression fixtures but are
not an independent acceptance set. Before live shadow routing, the NLU must have:

1. a human-labelled holdout covering household, general answer, read-only
   investigation, change request, external research and unsupported requests;
2. explicit personal/private, mixed-intent, changed-intent and ambiguity cases;
3. family, sensitivity, capability-need and disposition scores reported
   separately rather than collapsed into one route score;
4. an abstention/clarification threshold selected without tuning against the
   holdout;
5. exact engine/policy/source provenance and bounded latency/resource evidence;
6. shadow comparison with no execution and no provider egress; and
7. an evidence-backed promote-or-reject decision. Promotion never grants tools.

Until those gates pass, automatic routing remains off and the deterministic
baseline remains the operational reference.

## Current qualification checkpoint — 2026-10-25

The NLU boundary is now formalized through an exact accepted evaluation policy,
a sealed local Qwen3.5-9B/SYCL candidate, 60 independently created and reviewed
synthetic calibration cases, a registered content-free scoring contract and a
conditional independent-holdout design. This is evaluation machinery only.
It grants no tool, provider, route or execution authority.

The eleven-file calibration packet is staged inactive in LXC110 without a
model call. Its corrected runner recomputes the remaining 1,200-second budget
immediately before transport and refuses to start after expiry. It also rejects
a timeout, endpoint or transport failure on case 60 instead of relying on the
record count. Both runner corrections are installed inactive and passed 17/17
target-Linux tests. A later downstream review found that a separately supplied
60-row run could still present one of those infrastructure failures to the
scorer with a fabricated complete journal. The scorer and journal validator
now reject that claim while retaining only malformed model output as a
completed zero-score result. The dependency-free suite passes 119 tests. The
staged packet is **NO-GO for execution** until the exact four-file inactive
scorer/journal/manifest replacement passes target-Linux validation.

After replacement, the serial live path remains:

1. complete and independently reconcile F2;
2. derive the separately authorized F3 receipt;
3. produce fresh cycle-bound F4 and F5 evidence;
4. arm the independently recoverable F6 lease under a current exact card;
5. run candidate-H first; and
6. run the 60-case NLU calibration only after candidate-H has a validated
   accepted outcome and the restoration reserve still fits.

Calibration may freeze a threshold or reject the candidate. It cannot enable
shadowing or routing. A passing calibration permits creation and independent
review of the predesigned holdout; a rejection expires that conditional path.

The [development scorer](evidence/M3-NLU-development-scorer-2026-10-24.md)
implements the dimensional reporting boundary against 24 pinned exposed
synthetic cases. It reports privacy underclassification and unsafe false routes
as their own blocking signals, retains invalid attempts in the denominator and
keeps request text out of run and score records. It is regression tooling, not
the independent holdout required above.

The [holdout custody boundary](evidence/M3-NLU-holdout-custody-boundary-2026-10-24.md)
now fixes a content-free 36-case release shape with six opaque cases per family,
four distinct custody/review roles, frozen contract/scorer/threshold provenance
and development-set non-overlap evidence. The empty template and validator do
not create or claim the holdout. Independent case creation, human labels,
calibration, sealing, evaluation and review remain open.

The [threshold-policy boundary](evidence/M3-NLU-threshold-policy-boundary-2026-10-24.md)
now also requires the sealed release to carry the exact frozen policy bytes.
It preregisters disjoint calibration, implements deterministic selection, zero tolerance
for privacy underclassification and unsafe false routing, and digest binding
to one candidate and calibration result. Its committed template intentionally
contains no numeric quality/coverage acceptance values, sample minima,
evidence digest or selected threshold. Those values must be accepted in a
registered policy before calibration; they cannot be inferred from the
independent holdout. The selector then freezes the exact calibration-score
digest and selected threshold or fails when no threshold meets every constraint.
The [calibration custody boundary](evidence/M3-NLU-calibration-custody-boundary-2026-10-24.md)
now adds an empty content-free template and a validator whose sealed form takes
its sample minima only from the registered policy, binds the same candidate and
uses three distinct custody roles. It creates no cases or labels and does not
resolve the still-open numeric policy decision.
The [no-effect shadow boundary](evidence/M3-NLU-no-effect-shadow-boundary-2026-10-24.md)
also fixes an initial S0-only, content-free comparison manifest. It records only
opaque interpretation/proposal digests and baseline/candidate route names, while
requiring no execution and no provider egress. Its empty template is preparation,
not collected evidence or permission to route.
The [non-vacuous policy boundary](evidence/M3-NLU-nonvacuous-policy-boundary-2026-10-24.md)
now also rejects zero minimum coverage and a 100% selective-error allowance.
This prevents an empty or unconstrained calibration result from becoming a
valid frozen policy while leaving every actual numeric acceptance value open
for preregistration.
The [holdout artifact-binding boundary](evidence/M3-NLU-holdout-artifact-binding-boundary-2026-10-25.md)
now requires the validator to receive and hash the exact contract, scorer,
threshold-policy and development non-overlap receipt bytes named by a sealed
holdout manifest. A digest-shaped but unrelated artifact can no longer pass
bundle validation.
The [calibration exact-release binding](evidence/M3-NLU-calibration-exact-release-binding-2026-10-25.md)
additionally proves that the release bytes registered by policy decode to the
same calibration manifest being validated. A valid manifest can no longer be
paired with different policy-bound release bytes.
The [duplicate-key JSON boundary](evidence/M3-NLU-duplicate-key-boundary-2026-10-25.md)
now gives threshold policies, calibration scores and exact calibration releases
one unambiguous parse for each hashed byte sequence. Repeated object keys fail
closed instead of taking parser-dependent meaning.
The [shadow artifact-binding boundary](evidence/M3-NLU-shadow-artifact-binding-boundary-2026-10-25.md)
now also requires every opaque shadow row's interpretation and route-proposal
digests to match supplied content-free artifacts. Missing, extra or drifted
case artifacts fail closed.
An [initial numeric policy decision draft](evidence/M3-NLU-initial-threshold-policy-decision-draft-2026-10-25.md)
now makes the remaining owner choice reviewable: zero privacy and unsafe-route
failures, at most 10% selective error, at least 60% coverage and 60 calibration
cases balanced ten per family. These are proposed values only; no registered
policy exists. The later
[candidate-bundle boundary](evidence/M3-NLU-candidate-bundle-boundary-2026-10-25.md)
defines the previously implicit artifact behind `candidate_bundle_sha256` and
requires exact engine, policy, contract, adapter and runtime-profile provenance,
consistent egress, disabled tools, no case data and no authority. Its template
does not select or seal a candidate.
The subsequent
[calibration candidate-binding correction](evidence/M3-NLU-calibration-candidate-binding-2026-10-25.md)
requires calibration admission to receive those exact candidate bytes, validate
the sealed manifest and prove its hash is the digest named by the registered
policy. Matching digest-shaped claims alone no longer admit calibration.
The same
[exact-candidate binding now applies to S0 shadow evidence](evidence/M3-NLU-shadow-candidate-binding-2026-10-25.md),
preventing candidate drift between calibration, threshold selection and the
later no-effect comparison.
The final
[holdout candidate-binding correction](evidence/M3-NLU-holdout-candidate-binding-2026-10-25.md)
extends that exact byte identity into the independent qualification release
without opening or creating holdout data.
The numeric draft is now also an exact
[machine-readable policy proposal](evidence/M3-NLU-machine-readable-policy-proposal-2026-10-25.md)
at digest `2e0def84…64a3d`. It remains `proposed`: acceptance requires a separate
exact record, and the proposal grants no authority.
A new
[policy registration gate](evidence/M3-NLU-policy-registration-gate-2026-10-25.md)
then requires an accepted exact decision, one sealed candidate and one matching
sealed calibration release before it can construct a registered policy. It
deliberately rejects the current `proposed` artifact.

## Validation checkpoint — 2026-10-24

The focused interpretation, route, Decision and Outcome semantic suites pass
11/11, and the NLU development scorer suite passes 10/10, under Python 3.12 and
Pydantic 2.14.1. The full historical adapter suite remains blocked by its
pre-existing reviewed-source pin drift, as designed. This change does not repin
that experiment, deploy a classifier, call a model, enable egress or alter
AI-PAM.
