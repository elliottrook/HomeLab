# SA4 v5 install and v6 fresh-path review — 2026-11-06

## Inactive installation

Jason approved the exact two-file v5 interface correction. The
[canonical result](SA4-runner-interface-fix-inactive-install-result-2026-11-06.json)
passes its strict source validator. Both files are exact root-owned, mode 0644,
one-link regular files. The installed runner rejected an unexpected argument
before input, the prior failed attempt remained byte-identical, the canary
remained `a9831e62…4da0`, the lease stayed `ready`, and production remained
healthy with zero restarts. No authority, repair or service action occurred.

## Fresh-path correction

Post-install release review found one further deterministic boundary: the v5
runner still names the fixed `transaction-input-v2`, `transaction-evidence-v2`
and `one-use-ledger-v2` paths. The first two now hold the retained v4 NO-GO.
Reusing them would either overwrite evidence or fail the fresh-absence gate.
Neither is acceptable.

The source-only v6 runner therefore binds the real v3 predecessor temporarily
to three disjoint fresh paths:

- `/var/lib/aster/sa4/transaction-input-v3`;
- `/var/lib/aster/sa4/transaction-evidence-v3`;
- `/var/lib/aster/sa4/one-use-ledger-v3`.

It also uses operation identity `sa4-canary-v2-second-operation-v1`, preserves
the v5 owner target interface, validates the exact predecessor constants before
binding, and restores every predecessor global afterward. The runner SHA-256 is
`a91d6a34…a397`. Tests exercise the binding inside the real predecessor call
boundary and prove restoration after return.

A new unsigned authority source uses grant identity
`sa4-canary-v2-second-grant-v1-20261106`; it contains no signature and confers
no effect. The failed first grant is not reusable.

The complete SA4 suite passes 294/294. The one-file create-exclusive inactive
install plan is `02565c96…f49f`. It preserves the entire failed v2 attempt and
does not invoke a runner, signer, authority, checkpoint, repair, service action,
route or promotion. Installing this one absent v6 runner is the next operational
gate. A fresh release and new exact live approval remain later gates.
