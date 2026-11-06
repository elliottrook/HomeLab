# SA4 distinct-canary v3 inactive-install review — 2026-11-06

## Decision

The two-file v3 transaction install is **reviewed and inert**. It is suitable
only for a later reversible inactive installation. It does not authorize a
repair, runner invocation, authority creation, signature, ledger claim,
checkpoint, service action, route or promotion.

The complete SA4 source suite passes **252/252**. Canonical plan SHA-256 is
`7fd29ff4d2d5315a9418aac954980a694e6eded053908eb4e09d0abc7fa8a385`.

## Fresh target facts

Read-only LXC 104 inspection found:

- both v3 destinations absent;
- the seven direct installed dependencies at their exact reviewed hashes;
- the distinct canary still at drifted digest `a9831e62…4da0`;
- v2 input, evidence and ledger paths absent;
- operation lock and emergency stop absent;
- LXC 104/110/116 running;
- Aster Agent, accepted llama.cpp/SYCL, Speech, `pvescheduler` and `pvestatd`
  active.

No secret-bearing file was read.

## Exact inactive change

The plan may create only these absent root-owned mode-0644 files:

1. `sa4_root_transaction_owner_v3.py` at
   `2b2d08249072c52dd5e2f79ff3f525bdb46c647a79225993e964dd6e7dd49fb0`;
2. `sa4_fixed_transaction_runner_v3.py` at
   `9c6bfbbe05dfa6d574988df3a99b79696fcfee1353d24461324806df2ec0cc9f`.

Postcheck is limited to exact metadata/hash checks, isolated imports, v1 target
rejection, v2 target resolution, absent transaction state, unchanged target
and healthy production. Rollback removes only exact after-hash files in reverse
order. Any drift or uncertainty retains state and stops.

## Next gate

The next SA4 operation is the reversible inactive two-file installation and
its independent zero-effect validation. The later one-canary transaction is a
separate effect and remains unauthorized.

