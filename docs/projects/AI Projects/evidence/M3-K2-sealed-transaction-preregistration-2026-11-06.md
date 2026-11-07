# M3 K2 sealed-transaction preregistration — 2026-11-06

## Outcome

The complete non-authorizing contract for one future K2 sealed-evaluation
transaction is frozen before any effect. It binds the private inputs, ten
runtime source pins, existing control direction, tunnel topology, request
budget, development prerequisite and full restoration proof.

## Frozen identity

- preregistration source:
  `scripts/aster-adaptive/nlu_k2_sealed_transaction_preregistration_v1.py`
- source SHA-256: `ef38c74a3b620845ed9cfc8f303c73ebd3bea6e6e15aab948a81c340b82ecbe4`
- focused test SHA-256: `78c054a15346074e7a18a5681641ded64b392847613935de7ee92154915f2a4d`
- canonical preregistration SHA-256:
  `9485b276e3fac0eb16854209c74b3d4723719f094595801a5128bcd1d437d772`
- future workload ID: `m3-k2-sealed-evaluation-v1`
- exact effect: 32 cases, 32 requests, zero retries, 45-second per-request
  timeout, 1,800-second deadline, 900-second recovery reserve

## Admitted topology

The contract permits only the already authenticated Mac mini-to-MacBook SSH
direction. Both exposed tunnel ends and the relay bind are loopback-only. It
forbids direct MacBook-to-B60 use, a new access grant and a standing B60
credential on the MacBook. Two distinct transaction nonces separate the
MacBook-side relay from the private model listener.

The MacBook paths and bytes are fixed to the independently custodied R5
directory. Metadata-only verification confirmed that it already contains:

- accepted corpus SHA-256
  `9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a`;
- sealed evaluation SHA-256
  `78f7b8aa7b8f8202e38333be4d497a489c1f36b3c6209839c05ecd3975191cae`.

No additional corpus or evaluation custody transfer is required.

## Mandatory prerequisite and terminal proof

The contract is invalid unless booking
`aster-stream-a-m3-k2-20261106-2000-r1` produces a complete development pass
with production restored. A later effect must have its own bounded booking ID,
registered hash-pinned workload, lease and operation lock.

Success additionally requires 32 private shortlists and results, content-free
metrics, production restored, lease ready, locks absent, and every tunnel,
relay, runner and private listener absent. The preregistration explicitly sets
effect authorization false, authority not granted, deployment false and
automatic routing off.

## Verification

- preregistration/relay/runner suite: 13/13 passed
- Python syntax compilation: passed
- platform session/terminal contract: commit `ae4585e2`, 5/5 focused tests
- sealed input access: metadata/hash only; content not read
- model requests: zero
- B60 use: none
- booking or effect created: no
