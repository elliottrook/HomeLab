# M3 K2 sealed-evaluation local runner boundary — 2026-11-06

## Outcome

The MacBook-local, one-attempt runner for K2's independently sealed 32-case
evaluation is frozen at source and passes its focused tests. It was not run
against the sealed artifact and made no model request.

## Fixed boundary

- runner: `scripts/aster-adaptive/nlu_k2_sealed_evaluation_runner_v1.py`
- runner SHA-256: `ca802811dd700e164bbd538735e2d0c670b5d1f841a1947e36cde7e3aa221a1a`
- focused test SHA-256: `31f2871839e40e88be6438964484e951a22e563b04642edeab3d9e76b3a7ba88`
- accepted sealed evaluation SHA-256:
  `78f7b8aa7b8f8202e38333be4d497a489c1f36b3c6209839c05ecd3975191cae`
- fixed endpoint: loopback only,
  `http://127.0.0.1:11437/v1/chat/completions`
- maximum effect: exactly 32 requests, zero retry, 45 seconds per request and
  a 1,800-second total deadline
- retained private evidence: create-only mode-0600 journal, records and metrics
- standard output: content-free state, counts, pass/reject status and digests

The runner rejects redirects, direct LAN endpoints, tool calls, reasoning
content, unknown response fields, altered sealed identity, altered shortlist
shape, non-finite scores, duplicates and incomplete result sets. Sealed request
text and expected labels remain in the MacBook process and are not written to
records, metrics, journal events or standard output.

The bearer accepted by this source is a transaction-scoped relay nonce, not a
B60 service credential. The future registered platform effect must create the
loopback relay only for its booked transaction, inject the B60 credential on
the controlled side of that relay, enforce the same bounded request contract,
and close the relay during restoration.

## Verification

- focused runner/scorer/consensus/arbitrator suite: 19/19 passed
- Python syntax compilation: passed with a private temporary cache
- sealed evaluation access: false
- model requests: zero
- B60 use: none
- route effect, tools, deployment and authority: not granted

## Remaining gate

The relay and full cross-host transaction are not yet implemented or
registered. They must not be installed, booked or invoked unless the current
K2 development transaction passes with production restored. The relay effect
will require its own hash-pinned Lab Hours registration, reservation, whole-host
lease, operation lock, recovery proof and platform review.
