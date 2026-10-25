# M1 broker capability-revocation source promotion card

> Status: **approval-ready candidate; not authorized by this card**
>
> Source checkpoint: `c1d0eb38`

## Purpose

The permanent Yellow-only approval ingress is healthy, but its installed
broker core and approval service predate the repository's capability-
revocation operator method. The measured source delta is exactly two additions:

1. `BrokerStore.revoke_capability()` removes one existing agent-to-capability
   grant, revokes that pair's pending or approved requests and writes a bounded
   audit outcome; and
2. `management.capability-revoke` invokes that store method only after the
   approval service's existing fresh-human check.

The current Companion HTTP management schema does not expose this method, and
the independent ingress still has no production passkey mapping. Installing
the candidate therefore does not add a browser action, enable Red approval or
grant a capability. It aligns the production broker with the already reviewed
repository source and prepares a later, separately gated operator ceremony.

## Exact files

| Source | Target | Current production SHA-256 | Candidate SHA-256 |
|---|---|---|---|
| `ops/credential-broker/broker_core.py` | `/opt/homelab-broker/broker_core.py` | `a7dbf6206e8643ccf3b52260a83f8da07597acd0cca2d74152aaab28418c60d0` | `2fdb80964984fed5cf539f12a62d0058ba9eb9088861425858109fabc7dabf99` |
| `ops/credential-broker/broker_approval_service.py` | `/opt/homelab-broker/broker_approval_service.py` | `eeefdf23fd08602f6d78a8499a81a7db04465ae78fa3ab3806f2d7f8a385f043` | `4a9f8d0de622a06e7dd9fe32279b22d71a3dbe4f220a77891684c34e30756631` |

No unit, environment, ingress, NPM, firewall, identity or database file changes.

## Static and target evidence

- The exact diff contains no database schema or existing-method change.
- Candidate `py_compile` passes on LXC104.
- A candidate `BrokerStore` open/close against a private copy of the post-
  cutover database preserved the schema hash
  `e2dab670470d577a0acf32062154cf77adb17cee0595599f944696ed637a1029`,
  all seven table counts and database integrity.
- The 34 broker-core/approval-service tests pass.
- Six HTTP-to-socket tests pass on target Linux with the candidate bundle,
  including demotion, capability revocation and expiry.
- The installed production modules independently pass the synthetic demotion
  and expiry cases. Capability revocation is absent there by definition.

## Proposed bounded installation

Abort unless the two production predecessors, both release unit hashes, the
NPM/firewall route, zero request counts, service identities and current
database integrity still match the permanent-cutover evidence.

1. Create a fresh owner-only consistent database checkpoint and byte-preserve
   the two predecessor modules.
2. Stage the two candidate bytes, verify their hashes and compile them against
   the target Python environment.
3. Install both files atomically one at a time while the imported old code is
   still running; do not restart either service between the two replacements.
4. Restart only `homelab-broker-approval-independent.service`. Require the
   exact socket identities, ordinary-Aster denial, dedicated-UID status,
   public 401 and signed-in read-only approval view.
5. Restart only `homelab-broker.service`. Require its original socket,
   identity, zero restart count and ordinary Aster health.
6. Run the full broker and HTTP/socket synthetic suites using temporary
   databases. Do not invoke the new live method against a production agent.
7. Confirm the live database still has zero pending and zero approved-
   unconsumed requests and is byte-for-byte unchanged from its pre-install
   consistent checkpoint.

## Rollback

On any failed gate, restore both predecessor modules before restarting either
broker. Restart the independent approval broker, then the execution broker,
and repeat the identity, route and database checks. The database checkpoint is
comparison evidence only unless independent corruption is proven; never
overwrite newer broker state merely because source rollback is required.

## Exclusions

No capability is revoked, granted or exercised. No real request is created,
approved or consumed. No passkey mapping, Red approval, UI management action,
model call, connected tool, automatic routing, B60 change, Authentik change or
OpenBao operation is included.
