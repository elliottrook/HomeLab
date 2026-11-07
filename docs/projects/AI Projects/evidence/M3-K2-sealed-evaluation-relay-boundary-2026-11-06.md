# M3 K2 sealed-evaluation relay boundary — 2026-11-06

## Outcome

The source-only, transaction-scoped relay between the MacBook-local evaluator
and the future private K2 model listener is frozen and passes its focused
tests. It was not started, did not access the sealed evaluation and made no
model request.

## Measured network facts

Read-only probes established the topology rather than assuming it:

- Mac mini to MacBook SSH: authenticated and usable through host alias
  `macbook` at `192.168.1.241`;
- Proxmox to MacBook SSH: network connection timed out;
- MacBook to Proxmox TCP/22: reachable, but existing public-key authentication
  is denied;
- MacBook to accepted B60 listener TCP/11435: reachable.

No access grant, key, firewall rule, listener or service was changed by these
probes. Because the only existing authenticated cross-host control path is
Mac mini to MacBook, the source freezes a loopback relay suitable for an
SSH reverse tunnel from that established path. It does not create the tunnel.

## Fixed relay

- source: `scripts/aster-adaptive/nlu_k2_sealed_relay_v1.py`
- source SHA-256: `bd39e387219994611b28e53fdc527de337cce98c01fd08061fe343d7bfeb0c78`
- focused test SHA-256: `0f7a3abec02eb5021abb92a8b51b96e05787a795cf57aacc8ecab681b7cdb573`
- inbound bind: `127.0.0.1:11438` only
- upstream: `127.0.0.1:11439` only
- request path: `/v1/chat/completions` only
- exact request count: 32; retries: zero; hard deadline: 1,800 seconds
- maximum request and response: 65,536 bytes each

The relay re-derives the exact K2 payload from the offered four-label schema
and request text and requires byte equality before forwarding. It rejects
other methods, paths, credentials, fields, model settings, redirects, tools,
reasoning content, oversized bodies and any response outside the frozen
runner envelope. Access logs are disabled. Its standard output contains only
state, request count, retry count, bounded failure code and
`authority=not-granted`.

The relay accepts two distinct transaction-scoped nonces: one authenticates
the MacBook-side request, while the other authenticates the future private
model listener. It does not accept or expose a standing production B60 key.

## Verification

- relay/runner/arbitrator suite: 13/13 passed
- Python syntax compilation: passed with a private temporary cache
- sealed evaluation access: false
- model requests: zero
- B60 use: none
- tunnel, listener, access grant and deployment: absent

## Remaining effect gate

A registered platform transaction must still create the private model
listener and ephemeral upstream nonce under an admissible Lab Hours booking,
whole-host lease and operation lock. A bounded Mac mini coordinator must then
create both loopback-only SSH tunnels, start this exact relay and the exact
MacBook runner, retain content-free evidence, tear down every process and
prove production restoration. That effect remains conditional on a passing,
restored K2 development transaction and requires a separate platform review;
this source boundary is not authority to run it.
