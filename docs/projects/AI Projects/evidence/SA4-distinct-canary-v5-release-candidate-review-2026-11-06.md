# SA4 distinct-canary v5 release candidate review — 2026-11-06

**Result: PASS — fresh v8 release candidate; no effect yet.**

The packet binds the unique plan/checkpoint identity
`sa4-canary-v2-second-repair-v1`, v8's fresh v5 input/evidence/ledger paths,
operation `sa4-canary-v2-fourth-operation-v1`, and new unsigned grant identity
`sa4-canary-v2-fourth-grant-v1-20261106`. It binds the exact inertly installed
v8 and pre-claim reconciler hashes plus the completed zero-effect v7
reconciliation result.

The target must still be `a9831e62…4da0`, the new checkpoint and all v5 paths
must be absent, the lease must be ready, the exact production health checks
must pass, and fresh owner/AI-PAM proofs must validate before a single repair.
At most one repair and one rollback are possible; there is no automatic retry,
service restart, model change, route or promotion.

The focused release tests pass 2/2 and the complete SA4 suite passes 324/324.
Under Jason's standing Stream A version-test authorization, one fresh v8
transaction may run when every runtime gate passes. Any failure or uncertainty
retains evidence and stops that version without retry.
