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
The socket-level broker suite also proves that a synthetic request returns
`synthetic: true` while all read, write and lab gateway request lists remain
empty. The combined broker core and transport suites pass **31/31**.
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
