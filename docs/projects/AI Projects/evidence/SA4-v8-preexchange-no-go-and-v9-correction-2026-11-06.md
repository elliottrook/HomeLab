# SA4 v8 pre-exchange NO-GO and v9 correction — 2026-11-06

**Result: NO-GO for v8; v9 source correction PASS. No effect occurred.**

v8 initialized fresh v5 evidence and ledger state, then stopped before creating
the transaction owner because `/run/aster-sa4-observer-exchange` already
existed as an empty root-owned mode-0700 directory. The ledger remains
`ready`/`use_count=0`; evidence is empty; the new checkpoint, runtime controls
and observer requests are absent; the target remains `a9831e62…4da0`. v8 is
spent and will not be retried.

The correction adds a narrow reconciler that accepts only this exact no-effect
state, removes only the exact empty exchange directory and writes a durable
content-free receipt. v9 uses fresh v6 paths, a third unique plan/checkpoint
identity and a fifth fresh authority identity. The complete SA4 suite passes
327/327. No service, model, route or promotion change is included.
