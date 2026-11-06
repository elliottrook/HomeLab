# M5 K2 route-selector source boundary — 2026-11-06

## Gap closed

K2's consensus policy produces a content-free request interpretation but does
not itself select a backend. M5 therefore could not honestly claim a shadow
comparison of automatic handover from the K2 result alone.

A separate deterministic selector now converts only an accepted K2
interpretation into the existing digest-bound `route-proposal.v1` contract.
It remains proposal-only and grants no authority:

- ambiguous, unsupported and policy-denied interpretations remain
  clarify/abstain/deny with no backend or egress;
- personal requests always remain local;
- public/internal read-only investigation and external research may propose
  only the bounded `codex-subscription-readonly` backend;
- other understood families remain local;
- every proposal expires within five minutes and binds the exact
  interpretation, candidate and selector-policy digests.

The focused selector suite passes 5/5. This is source-only preparation for a
later no-effect shadow. It does not open the sealed evaluation, call K2 or
Codex, execute a route, grant a capability, deploy a selector, enable automatic
routing or promote a candidate.
