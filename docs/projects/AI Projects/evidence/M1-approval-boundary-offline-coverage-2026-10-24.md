# M1 independent approval plane — additional boundary coverage

Date: 2026-10-24 PDT  
Result: **offline candidate PASS; production lineage difference retained**

## Added coverage

The current repository candidate now has explicit regression tests for five
post-request boundary changes:

- two consumers racing the same approved request produce exactly one
  `consumed` terminal result;
- an approved request is rejected if its bound authorization policy changes
  before consumption;
- agent demotion closes an existing pending request before HTTP approval;
- capability revocation closes an existing pending request before HTTP
  approval; and
- expiry closes an existing pending request before HTTP approval.

These use synthetic agents, capabilities, tokens, payloads and temporary
SQLite databases. They do not contact the live broker database, create a real
approval or call a model.

## Verification

- 34 broker-core and approval-service tests passed on the Mac dependency
  runtime.
- Six HTTP-to-Unix-socket approval tests passed on LXC104 using an isolated
  bundle of the current repository modules and the target's existing Python
  dependencies.
- The demotion and expiry HTTP tests also passed against the currently
  installed production modules, again with a temporary database and synthetic
  socket.

The current candidate bundle used for the target-dependency run had SHA-256
`538c85039f283a5aa172b7becb6f070ec3500c19d3928eb8f6272eb12f2e881f`.
The only runtime warning was the existing Starlette `TestClient` deprecation;
it did not affect results.

## Production/source distinction

The permanent approval ingress and HTTP adapter match the repository exactly:

| Module | SHA-256 |
|---|---|
| `approval_ingress.py` | `797d492e66748e103e8bbff67b9fb714d11a7229c5fb6fcb9b74d2e8d7772744` |
| `broker_approvals.py` | `cf37fb1782c875622155b50d7b69f31b7c9acc2c30f7881f5da9b4a6538dd324` |

The installed broker core and approval service are the earlier reviewed
production lineage, not the current repository candidate:

| Module | Production SHA-256 | Current repository SHA-256 |
|---|---|---|
| `broker_core.py` | `a7dbf6206e8643ccf3b52260a83f8da07597acd0cca2d74152aaab28418c60d0` | `2fdb80964984fed5cf539f12a62d0058ba9eb9088861425858109fabc7dabf99` |
| `broker_approval_service.py` | `eeefdf23fd08602f6d78a8499a81a7db04465ae78fa3ab3806f2d7f8a385f043` | `4a9f8d0de622a06e7dd9fe32279b22d71a3dbe4f220a77891684c34e30756631` |

The production core has demotion, approval, consumption and expiry paths, and
the synthetic demotion/expiry checks pass. It does not contain the newer
`revoke_capability` method or the approval-service method that exposes that
operator action. This does not weaken the new Yellow-only route: the HTTP
management adapter does not expose capability revocation and all management
mutations remain closed by the empty passkey mapping. It does mean the new
capability-revocation test is candidate evidence, not a claim about the
installed production broker.

## Next gate

Before any broker-source promotion, freeze an exact two-module release,
compare its database migration and management surface with production, run the
full broker and ingress suite on target Linux, prepare byte-exact rollback and
obtain a distinct installation approval. No source promotion is implied by
this test milestone.
