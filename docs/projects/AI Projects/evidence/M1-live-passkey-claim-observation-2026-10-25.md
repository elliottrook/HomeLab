# M1 live passkey-claim observation — 2026-10-25

> Result: **PASS FOR CLAIM TRANSPORT; FRESHNESS DISPLAY UNMEASURED**

## Observation

Jason completed the ordinary Aster WebAuthn ceremony in the existing web
Companion. The signed-in AI-PAM Management view then displayed:

> Passkey verified. Changes require a fresh passkey confirmation.

That text is rendered only from the independent approval ingress session
response and therefore proves that the production ingress accepted the exact
configured `urn:homelab:aster:webauthn:1` ACR as `passkey_verified=true`.
The page was opened read-only. No approval, management button, capability
grant, model request or OpenBao action was used.

## Independent no-effect checks

- `aster-agent.service`, `aster-approval-ingress.service` and
  `homelab-broker-approval-independent.service` were all active.
- The broker database SHA-256 remained
  `db583d652cc2ec152a0f730c136b8168b7e8ecdb4bf1cfb736a828f3f5486d9e`.
- Live unexpired pending requests: `0`.
- Live approved-but-unconsumed requests: `0`.
- The audit maximum remained sequence `121`, matching the pre-observation UI.
- The Management view reported no active session or request.

## Deliberate evidence limit

The installed page renders `passkey_verified` but discards the separate
server-derived `fresh` boolean. The ingress runs Uvicorn with access logging
disabled, and its INFO-level content-free session line was not retained by the
current logging configuration. Freshness is therefore recorded as
**unmeasured**, even though the view followed the interactive ceremony.

The passkey claim-transport gate is closed. Red approval and management remain
closed because this observation grants no authority and did not exercise their
freshness enforcement. The reviewed effect-free web session candidate may
still improve operator visibility by displaying both booleans, but it is no
longer required to prove ACR transport and remains undeployed.
