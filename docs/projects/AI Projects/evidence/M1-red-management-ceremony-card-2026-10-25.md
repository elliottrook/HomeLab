# M1 Red and management ceremony — no-executor candidate

> State: **OFFLINE CARD; NO REQUEST OR MANAGEMENT MUTATION CREATED**

## Purpose

The live WebAuthn observation proves that the independent ingress accepts the
exact Aster passkey ACR. It does not prove the separate 120-second freshness
enforcement on a Red approval or a management mutation. This card defines the
smallest live ceremony that can close those two gates without touching a real
infrastructure executor.

## Measured live prerequisites

The production broker currently has no pending or approved-unconsumed request.
Its existing synthetic registry includes:

- active operator `agent-hermes`;
- enabled service `synthetic`;
- Red capability `broker.synthetic.network-change`; and
- a broker consumer that returns `synthetic: true` for this capability instead
  of calling a gateway or external tool.

The current `agent-hermes` state is already `operator`. The broker changes no
agent, capability or request state when an operator is set to the same
nonterminal state; it writes only the authenticated audit event. The new
focused regression test preserves a pending Red request across that exact
same-state operation. The dependency-free broker-core suite passes **22/22**.
The socket-level broker suite also creates a Red synthetic request, applies a
fresh passkey-assurance fixture, consumes it through the broker socket and
proves the result is `synthetic: true` while all read, write and lab gateway
request lists remain empty. The combined broker core and transport suites pass
**32/32**.
The separate 13-test approval-service suite also passes. Four HTTP/ingress
modules remain target-environment checks because the bare Mac Python lacks
FastAPI and PyJWT; no test failure occurred inside those modules.

## Proposed bounded ceremony

This is a later, separately approved action:

1. Re-read the exact installed source hashes, database integrity/hash, zero
   live-request count, `agent-hermes=operator`, enabled synthetic service and
   passkey ingress health. Preserve a root-only consistent database checkpoint.
2. Through the kernel-identified main broker socket, create one Red request for
   `agent-hermes` and `broker.synthetic.network-change` with a fixed fictional
   no-executor payload, a 300-second TTL and an explicit synthetic display.
3. Jason reviews that one request in Companion and approves it through the
   mandatory WebAuthn flow. One click only; uncertainty means stop and inspect,
   never resubmit.
4. Confirm the exact request is approved with passkey assurance and an integer
   authentication time no older than 120 seconds. Consume it once through the
   same local synthetic broker boundary; require `synthetic: true`, terminal
   `consumed`, and duplicate-consume denial. No gateway or tool may be called.
5. With no live request remaining, Jason applies `operator` to the already
   operator `agent-hermes` once through Management and the mandatory WebAuthn
   flow. Require exactly one `agent.state` audit event, unchanged agent state,
   unchanged grants/services/global switch and no revocation.
6. Verify database integrity, bounded row deltas, all service health and the
   ordinary Aster path. Retain the terminal synthetic request and two audit
   events as evidence; do not restore an older database over newer terminal
   history.

The offline [read-only verifier](M1-red-management-read-only-verifier-2026-10-25.md)
now freezes the database checks around this sequence. It requires exactly one
new terminal request and four ordered audit rows (`request.create`,
`request.approve`, `request.consume`, `agent.state`), including exactly two
human-authenticated rows. It rejects any policy, grant, service, agent or
global-switch drift. The verifier itself does not create a checkpoint or
request and is not deployed.

The broker-side [exact operator candidate](M1-red-management-operator-candidate-2026-10-25.md)
also removes freehand request JSON from the ceremony. It binds the fictional
payload to SHA-256 `90b1d505…ad06`, requires the exact pending Red response,
stops without retry on an uncertain consume, and performs the duplicate check
only after an affirmative synthetic consume. It cannot approve a request or
apply the Management action. The combined broker/verifier/operator suite
passes 45/45; neither candidate is installed.

Any timeout, stale/absent assurance, changed payload hash, duplicate effect,
unexpected row delta or service degradation is **NO-GO**. Preserve the live
database for reconciliation and do not retry in the same ceremony.

## Explicit exclusions

This card does not release Red or management for routine use. It does not
change global enablement, agent lifecycle, service enablement, capability
grants, network configuration, OpenBao, tools, model routing or external
services. It does not deploy the optional session-check UI. Creating the
synthetic request and writing the same-state audit event are live database
mutations and require their own exact approval.
