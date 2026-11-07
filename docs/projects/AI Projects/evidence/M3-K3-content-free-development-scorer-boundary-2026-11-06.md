# M3 K3 content-free development scorer boundary — 2026-11-06

## Result

The K3 development scorer and retained-result contract are frozen at Stream A
commit `b81ba688`. The scorer independently recomputes every K3 decision from
the retained K2 arbitration record and independent hierarchical safety verdict;
it does not trust a producer-supplied final label, acceptance bit or route
disposition.

The frozen transaction requires exactly 192 public/development cases, 384
model requests, zero retries and zero response errors. It accepts K3 only with:

- at least 116 accepted decisions;
- at most 10% accepted-decision error;
- zero unsafe false routes; and
- zero routed privacy underclassifications.

The result is content-free and cannot open sealed evaluation data, grant
authority, execute a route or enable automatic routing.

## Fail-closed corrections

The safety module now validates its complete retained decision schema as well
as its model verdict. Acceptance and final disposition are recomputed from the
frozen ontology and exact semantic agreement. Retained scorer rows contain only
the raw arbitration record and safety verdict; added fields, missing fields,
substituted final decisions, duplicate case identities, count drift, retries,
response errors and incomplete case sets fail closed.

## Verification

- safety source SHA-256:
  `3cf4b0a531596760e6ad811c090fded4434fdd55143663c470104abdeba41bff`;
- safety test SHA-256:
  `f11777af3f7fceb7e25a9d2af302ca1671df142537b2cc3eba8ebc0439d97360`;
- scorer source SHA-256:
  `61dce93dc94ec76725e5d1048ab099a383a9e418245629e9631e98e834a8a353`;
- scorer test SHA-256:
  `5e90cb74acceceb8108cb24b14343bc774f8d501f5b10cfbe0b79a1163693ff5`;
- focused K3 tests: 16/16 pass; and
- complete `test_nlu_k*.py` discovery: 137/137 pass.

## Boundary and next action

No model request, sealed-data access, workload registration, booking, lease,
installation, service action, route, tool or promotion occurred. The next
offline milestone is the one-attempt K3 development runner: compose exactly one
arbitration and one independent safety request per case, durably retain the raw
inputs needed for scorer recomputation, stop on the first invalid response, and
preserve the existing deadline, recovery and no-authority controls. B60 use
remains separately subject to workload registration and Lab Hours booking.
