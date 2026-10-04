# SA3 incident-corpus custody readiness

Date: 2026-10-03
Status: **LOCAL TEMPLATE ONLY; COLLECTION AND EVALUATION BLOCKED**

## Purpose

This record turns the SA3 corpus boundary into an inspectable local template. It
does not collect, derive, label, review or evaluate an incident. It does not
choose a model or provider.

## Verified current state

The SA3 preregistration requires twelve sanitized development incidents and at
least twenty independently reviewed holdout variants. The separate empty intake
contract now lists the required case fields, but it does not itself define who
holds answer labels, how a holdout stays out of retrieval/tuning, or what must
be decided before collecting an incident.

No populated SA3 incident corpus, custodian, answer-key location or approved
retention arrangement exists in this repository. Jason is the sole operator, so
the programme must not claim independent review.

## Local readiness improvement

[`sysadmin-incident-corpus-custody-template-v1.json`](../../../../services/aster-agent/evals/sysadmin-incident-corpus-custody-template-v1.json)
is intentionally empty and records the preconditions for future collection:

- development and holdout uses are distinct;
- holdout labels are prohibited from model retrieval and implementation tuning;
- a named custodian, local storage location, temporal answer-key separation
  method, sanitization check, retention rule and digest/freeze procedure are
  required before collection;
- credentials, raw logs, private content, live output and model output are
  excluded; and
- single-operator evidence may support within-lab comparisons only; it cannot
  claim independent evaluation or generalized model quality.

The companion unit test checks that the template stays empty, retains the
holdout prohibitions, has no configured answer-key location or identities, and
uses precisely the case fields of the SA3 intake contract.

## Limits and next gate

This is a proposed custody boundary, not authorization to collect content or a
claim that any future storage method is secure. Before incident collection,
Jason must approve a bounded collection/custody plan that names the custodian,
local storage and temporal answer-key separation method. A later, separate
authorization is still required before any Qwen or provider comparison.

## Activated empty custody

Jason approved the local single-operator custody location on 2026-10-03. The
empty activation record is
[`SA3-single-operator-custody-activation-2026-10-03.md`](SA3-single-operator-custody-activation-2026-10-03.md).
It does not authorize incident collection or evaluation.

No model, provider, network, credential, production system or remote service was
accessed for this record.
