# SA4 v3-path postcheck rollback and v2-lineage correction — 2026-11-06

## Measured transaction result

Under Jason's standing Stream A version-test approval, the fresh v3-path
transaction used plan `e708b2f7…647b`, operation
`sa4-canary-v2-second-operation-v1` and one-use grant
`sa4-canary-v2-second-grant-v1-20261106`. Fresh owner and AI-PAM signatures
authenticated successfully. The fixed v6 runner was invoked exactly once.

The atomic repair wrote candidate digest `fae178a1…a0c2`, but the independent
receipt reported all three registered checks as `fail`. The controller obtained
the required second observer proof, restored the checkpoint and reconciled the
grant terminally failed. Terminal-result SHA-256 is `0fafab75…a58`; branch is
`rollback`, two observer signatures were requested and supplied, and automatic
retry is false.

Rollback completed and independently verified:

- final target digest: `a9831e62…4da0`;
- target: root:root, mode 0644, one regular link;
- checkpoint retained and exact;
- runtime observer exchange, operation lock and emergency stop absent;
- v3 ledger state `failed`, `use_count=1`;
- whole-host lease exactly `ready`;
- LXC104/110/116, Aster Agent, accepted llama.cpp/SYCL, Speech,
  `pvescheduler` and `pvestatd` healthy with zero restarts.

The complete v3 input, 13-file evidence set, terminal ledger and four host
bridge artifacts are retained. No retry occurred.

## First failed gate and correction

The observed healthy candidate was internally exact: 85 bytes, digest
`fae178a1…a0c2`, root:root, mode 0644 and one link. The deterministic failure
was registration lineage. `sa4_target_registry_v2.py` registered the original
v1 canary's check programs:

- byte check expected digest `4529dee5…1065`;
- metadata check expected size 82 and that v1 digest;
- consumer check expected adapter `sa4-canary` rather than
  `sa4-canary-v2`.

The source-only correction adds three v2-specific no-effect check programs,
registry v3 with their exact hashes, a bounded observer wrapper that binds and
restores those programs, a complete graph binding, owner v6, and runner v7 on
fresh `*-v4` transaction paths. The full suite passes 309/309. The eight-file
create-exclusive inactive-install plan is `219962e3…52f4`; it includes no
signer, authority, runner attempt, repair, service action, route or promotion.
