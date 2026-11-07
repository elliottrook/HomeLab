# M3 K2 sealed session contract — source review 2026-11-06

Status: source-only, non-authorizing. Nothing in this review registers a
workload, creates a reservation, acquires a lease, starts a listener or changes
production.

## Exact source

| File | SHA-256 |
|---|---|
| `scripts/local-ai/m3_k2_sealed_session_contract.py` | `580c2d34b81ef80e3cdb8699f7b33a3859d255e5c5b439414c8ab7b54322683a` |
| `scripts/local-ai/test_m3_k2_sealed_session_contract.py` | `d75919a6fa231caa92b3c3943bd724477ac801081c08bc75bbf784e97dc11bcf` |

The contract pins Stream A preregistration digest
`9485b276e3fac0eb16854209c74b3d4723719f094595801a5128bcd1d437d772`
and future workload ID `m3-k2-sealed-evaluation-v1`.

## Ready session

A ready session is content-free and must bind one admissible bounded booking,
one lease ID and generation, one 1,800-second interval, exactly 32 requests,
zero retries, two distinct nonce digests, private listener port 11436 and one
bounded scope unit. Production must already be masked, the operation lock must
be held and authority remains not granted. Raw nonces are deliberately absent
from this evidence object.

## Terminal evidence

Complete requires exactly 32 requests, zero retries/errors and regular 64-hex
records and metrics digests. Both complete and no-go require production
restored, lease ready, locks absent, and the private listener, relay, runner and
tunnels absent. A no-go carries only a bounded uppercase failure code and may
not infer success from partial digests.

## Verification

- focused tests: 5/5 passed;
- syntax compilation: passed;
- effects: none;
- next gate: a restored passing K2 development result, followed by platform
  transaction implementation, release-manifest review, inactive installation
  and a distinct Lab Hours booking.
