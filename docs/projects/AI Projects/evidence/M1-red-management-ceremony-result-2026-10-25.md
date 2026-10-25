# M1 Red and management ceremony — live result

> Decision: **PASS — SYNTHETIC RED AND SAME-STATE MANAGEMENT GATES CLOSED**

Jason approved the one bounded ceremony. Stream A created one fictional Red
request through the main broker socket, Jason approved it through Companion
WebAuthn, the exact payload was consumed once through the synthetic boundary,
duplicate consumption was denied, and Jason then applied `operator` to the
already-operator `agent-hermes` through the Management WebAuthn flow.

## Frozen identities

- request: `3b17a66e-31bc-4cd7-81d9-23694d41698e`
- capability: `broker.synthetic.network-change`
- payload SHA-256:
  `90b1d50533457baa73e6e99bd263198bfca6e08d8e7be0bf1abb179bba74ad06`
- operator SHA-256:
  `c25e9b52fc392636b7018f90dcf3144a48858be760aa7bc8679f51b922789cfb`
- verifier SHA-256:
  `dcd0b9996cbb98c8cffae4baceb2bf7c775d66f18088b564a204d022ebb2ddbf`

## Result

- Precheck: SQLite integrity `ok`, zero active requests, audit maximum 121,
  enabled global switch, `agent-hermes=operator`, enabled synthetic service,
  enabled Red capability and exactly one matching grant.
- WebAuthn: stored assurance `passkey`; authentication age at approval was one
  second.
- Consume: terminal `consumed`, `synthetic=true`; the deliberate duplicate was
  denied because the request was no longer approved.
- Management: the same passkey-bound approver applied
  `agent-hermes=operator`; the state did not change.
- Exact database delta: one request and four audit events, sequences 122–125,
  ordered `request.create`, `request.approve`, `request.consume`,
  `agent.state`.
- Postcheck: zero active requests; agent, service, capability, grant and global
  switch exactly matched the baseline; SQLite integrity remained `ok`.
- Services: Aster Agent, approval ingress, independent approval broker and main
  broker all remained active. Aster health returned HTTP 200 and the
  unauthenticated ingress session route remained HTTP 401.
- No gateway request, infrastructure executor, model call, OpenBao action,
  network change, capability grant, service change or F2 change occurred.

The root-only recovery checkpoint is retained at
`/var/lib/homelab-broker/rollback/m1-red-management-20261025/`. Its database
integrity is `ok` and SHA-256 is
`8c5da28339d15f87d62f2960f852f0f5d0aa7cef51971379ad45c4c8b183fd85`.
The terminal live database integrity is `ok` and SHA-256 is
`284ebbcdadf0781d064077856d3a03194ed6ec2cb6f5d462d8afddb8fa77566a`.
Temporary guest and Proxmox staging files were removed after verification.

## Interpretation

This closes the previously unmeasured fresh-passkey Red approval and
management-mutation evidence, including exact-once consumption and the
same-state audit boundary. It does not release arbitrary Red actions,
management changes or connected capabilities for routine use. Each real
capability still needs its own least-privilege registration, deployment and
effect approval gate.
