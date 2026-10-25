# M1 Red and management ceremony — read-only verifier

> Decision: **OFFLINE PASS; LIVE CEREMONY REMAINS APPROVAL-GATED**

The bounded Red/management ceremony now has a deterministic pre/post database
verifier. The verifier opens an existing SQLite database with `mode=ro`; it
does not instantiate `BrokerStore`, migrate a schema, checkpoint WAL, create a
request or write an audit event.

## Frozen candidate

- verifier: `scripts/aster-adaptive/m1_ceremony_db_check.py`
- verifier SHA-256:
  `dcd0b9996cbb98c8cffae4baceb2bf7c775d66f18088b564a204d022ebb2ddbf`
- tests: `scripts/aster-adaptive/test_m1_ceremony_db_check.py`
- tests SHA-256:
  `baf2a17703fceeda6ab2b380c02e146457b1d9a8263ea129c440895fe3d4b69e`
- result: **5/5 passed** with Python's standard `unittest` runner

## Enforced preconditions

The precheck requires SQLite integrity `ok`, zero pending/approved requests,
the global switch enabled, `agent-hermes=operator`, the enabled synthetic
service, the enabled Red `broker.synthetic.network-change` capability and its
single exact agent grant. Its owner-only JSON baseline contains counts and
policy identifiers only; request display text and payload content are never
emitted.

## Enforced postconditions

The postcheck requires exactly one new request and four new audit rows in this
order: `request.create`, `request.approve`, `request.consume`, `agent.state`.
The request must be Red, hash-bound to the supplied payload digest, approved
with an integer passkey `auth_time` no more than 120 seconds old, consumed
before expiry and terminal. Both authenticated actions must have the same
hashed approver actor. The agent, service, capability, grant and global switch
must be byte-for-byte equal to the baseline, and no active request may remain.

The tests prove the exact ceremony passes and that an extra audit event, wrong
payload hash, pre-existing active request and malformed baseline fail closed.
The absence of a fifth audit row also makes a successful duplicate consume
effect observable; the live operator must still issue the duplicate request
and retain its explicit denial.

## Boundary

This verifier is not deployed and has not read the production database. It
does not authorize or perform the live ceremony. A live run still requires
the already-described exact approval because it creates a synthetic request,
consumes it and writes a same-state management audit event.
