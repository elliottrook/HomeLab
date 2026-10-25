# M1 Red and management ceremony — live preflight

> Decision: **APPROVAL READY; LIVE MUTATION NOT STARTED**

This read-only preflight applies the existing no-executor ceremony card. It
does not create a request, authenticate a passkey, consume an approval or write
the management audit event.

## Measured state

- Broker database integrity is `ok`; SHA-256 remains
  `db583d652cc2ec152a0f730c136b8168b7e8ecdb4bf1cfb736a828f3f5486d9e`.
- There are zero unexpired pending requests and zero approved-unconsumed
  requests. Audit maximum remains sequence 121.
- `agent-hermes` remains `operator`.
- service `synthetic` is enabled and capability
  `broker.synthetic.network-change` remains enabled, bound to `synthetic` and
  classified Red.
- `aster-agent.service`, `aster-approval-ingress.service`,
  `homelab-broker-approval-independent.service` and `homelab-broker.service`
  are active.
- Aster's correct `192.168.70.10:9120/health` endpoint returns HTTP 200. The
  independent ingress's exact unauthenticated session route on port 9121
  returns HTTP 401 as required.
- Installed passkey configuration and ingress source still match their
  accepted SHA-256 pins `e9912319…b2f` and `6596cdd2…b40a`; both are root-owned
  mode 0644. The broker database remains `hlabroker:hlabroker` mode 0600.

An initial probe used stale port/path assumptions (`8000` and
`/approval/session`) and was discarded. Repeating the read-only checks against
the deployed 9120 health route and full 9121 approvals prefix produced the
expected 200/401 results. No service or database changed during either probe.

## Exact next gate

The existing ceremony card is now ready for one explicit live approval. The
bounded action will create one fictional, no-executor Red request, require one
fresh Companion WebAuthn approval, consume that exact request once through the
synthetic broker, deny duplicate consumption, then apply `operator` to the
already-operator agent once through Management and a second mandatory WebAuthn
flow. Expected retained effects are one terminal synthetic request and two
authenticated audit events. No gateway, infrastructure executor, capability
grant, service state, OpenBao action, model call or network change is included.

Any timeout, stale assurance, payload drift, unexpected row delta or uncertain
UI result is a no-retry stop with the live database preserved for
reconciliation.

## Fresh recheck after operator/verifier freeze

After local commits `5fcaf547` and `6cae53d1`, Stream A repeated the bounded
read-only production checks. SQLite integrity remains `ok`; active requests
remain zero; audit maximum remains 121; `agent-hermes` remains `operator`; the
global switch, exact synthetic service, exact Red capability and its single
grant remain enabled. All four units remain active. Aster health remains HTTP
200 and the unauthenticated exact ingress session route remains HTTP 401. Both
installed passkey source hashes still match the accepted pins exactly.

The fixed operator payload SHA-256 is
`90b1d50533457baa73e6e99bd263198bfca6e08d8e7be0bf1abb179bba74ad06`.
No request, checkpoint, file or audit row was created by this recheck. The one
live ceremony is now the first remaining M1 action and still needs explicit
approval.
