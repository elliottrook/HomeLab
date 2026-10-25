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

## Validation checkpoint — 2026-10-24

The focused interpretation, route, Decision and Outcome semantic suites pass
11/11, and the NLU development scorer suite passes 10/10, under Python 3.12 and
Pydantic 2.14.1. The full historical adapter suite remains blocked by its
pre-existing reviewed-source pin drift, as designed. This change does not repin
that experiment, deploy a classifier, call a model, enable egress or alter
AI-PAM.
