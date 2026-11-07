# M3 K3 one-attempt development runner boundary — 2026-11-06

## Result

The K3 development runner is frozen at Stream A commit `cac0fcd7`. It composes
the accepted 9B/SYCL endpoint into exactly two ordered, tool-free calls per
case: K2 four-label arbitration followed by an independent label-blind safety
verdict. A case is retained only after both responses pass their strict schemas
and K3 can independently recompute the non-effect decision.

The complete 192-case synthetic composition makes exactly 384 requests, retains
no request text or credential, and passes the frozen content-free scorer. There
is no retry path. An invalid arbitration response prevents its safety call; an
invalid safety response stops the whole transaction before the next case.

## Evidence and failure controls

- each request start and validated response stage is synchronously journalled;
- a journal write failure is a nonordinary stop before another request;
- the wall deadline is shared by all 384 requests;
- the endpoint remains restricted to the accepted production endpoint or the
  fixed private Lab Hours loopback endpoint;
- output and journal files use exclusive, no-follow, mode-0600 creation;
- retained records contain the raw arbitration record and safety verdict needed
  for independent scorer recomputation; and
- every result keeps authority `not-granted`, effects absent and automatic
  routing `off`.

## Verification

- runner SHA-256:
  `2ac71e79990b58b76ec2bacb46639e341eb554d0abf25fef1680c04a9d1d91b5`;
- runner test SHA-256:
  `5f6c26226a4f399467acc06a658871f116a3b559c1c46f4050179cdb6a7c2d66`;
- focused K3 suite: 21/21 pass; and
- complete `test_nlu_k*.py` discovery: 142/142 pass.

The tests cover exact two-stage ordering, no text/token retention, first- and
second-stage invalid-response stops, zero retries, durable-journal failure and
full 192-case runner-to-independent-scorer composition.

## Boundary and next action

No model request, sealed-data access, workload registration, booking, lease,
installation, service action, route, tool or promotion occurred. The remaining
offline admission step is an exact K3 release/registry manifest binding every
source dependency, corpus, shortlist, endpoint, request budget and recovery
condition. Only a separately installed registered workload and authoritative
Lab Hours booking may admit a B60 development transaction.
