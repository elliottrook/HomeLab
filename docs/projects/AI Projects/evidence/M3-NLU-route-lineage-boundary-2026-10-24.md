# M3 NLU-to-route lineage boundary — 2026-10-24

The first NLU contract made request interpretation explicit but did not yet bind
that result to a downstream selector proposal. `RouteProposal` now provides that
separate record and binds it to the exact canonical interpretation digest,
request, principal and policy.

The route schema requires consistent status, backend, egress and reason fields.
Clarify, abstain and deny have no backend or egress. Local routes have local
egress; Codex routes have cloud egress. The initial profile rejects a cloud route
for personal data because no consent artifact exists in this version. Every route
expires and carries literal `authorization: not-granted`.

The expanded focused NLU, route, Decision and Outcome semantic suite passes
**11/11**. It covers digest, identity, policy, expiry and disposition mismatch;
route-shape contradictions; personal-data cloud denial; and non-route outcomes.

This is an offline contract boundary. It deploys no selector, sends no content,
grants no tool and does not promote automatic routing.
