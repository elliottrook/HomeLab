# M1 Red and management ceremony — exact operator candidate

> Decision: **OFFLINE PASS; INERT AND NOT DEPLOYED**

The broker-side portion of the approved-shape M1 ceremony now has a fixed
operator candidate instead of freehand JSON. It performs only two explicit
phases and refuses to run without the exact authorization phrase
`M1-RED-MANAGEMENT-CEREMONY-2026-10-25`.

## Frozen candidate

- operator: `scripts/aster-adaptive/m1_ceremony_operator.py`
- SHA-256:
  `c25e9b52fc392636b7018f90dcf3144a48858be760aa7bc8679f51b922789cfb`
- tests: `scripts/aster-adaptive/test_m1_ceremony_operator.py`
- SHA-256:
  `6551a1667d5e807b814772d07b2515980d62b263767cd18cac28650f920309fb`
- exact payload SHA-256:
  `90b1d50533457baa73e6e99bd263198bfca6e08d8e7be0bf1abb179bba74ad06`
- focused result: **5/5 passed**
- combined broker core, approval service, read-only verifier and operator
  result: **45/45 passed**

## Transaction boundary

`create` sends one fixed 300-second request for
`broker.synthetic.network-change` with a fictional `effect=none` payload and
an allowlisted display. It requires the broker to return the exact frozen
payload hash, Red risk and pending state.

After the user approves that request through Companion WebAuthn, `consume`
sends the same fixed payload once. It requires an affirmative `consumed` and
`synthetic=true` response before making the deliberate duplicate attempt. The
duplicate must fail because the request is no longer approved. An absent,
malformed or uncertain first response stops immediately and is never retried;
the read-only database verifier must reconcile it.

The operator candidate cannot approve the request and cannot perform the
management mutation. The same-state `agent-hermes=operator` action remains a
separate Companion WebAuthn step. The candidate has no gateway, executor,
OpenBao, model, network or capability-grant code.

## Boundary

The candidate is local source only. Installing or invoking it against the live
broker, creating the synthetic request, consuming it, or applying the
management action remains inside the one exact live ceremony approval. No live
request or audit event was created by this work.
