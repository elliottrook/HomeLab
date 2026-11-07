# M3 K2 sealed session contract — source review 2026-11-06

Status: source-only, non-authorizing. Nothing in this review registers a
workload, creates a reservation, acquires a lease, starts a listener or changes
production.

## Exact source

| File | SHA-256 |
|---|---|
| `scripts/local-ai/m3_k2_sealed_session_contract.py` | `42f54b08c9e95857181e1d01eee641813a2ffcb45fad901e05d8edacb9009a58` |
| `scripts/local-ai/test_m3_k2_sealed_session_contract.py` | `d75919a6fa231caa92b3c3943bd724477ac801081c08bc75bbf784e97dc11bcf` |

The contract pins the refreshed twelve-pin Stream A preregistration digest
`4e7754585aeeef597c66eb2d3f2c6bf673f140f35c2f06d1856274429580adb1`
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
