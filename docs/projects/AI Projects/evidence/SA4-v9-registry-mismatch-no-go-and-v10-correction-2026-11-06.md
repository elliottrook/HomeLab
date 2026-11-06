# SA4 v9 registry mismatch NO-GO and v10 correction — 2026-11-06

**Result: NO-GO for v9; v10 source correction PASS. No repair occurred.**

v9 created an exact checkpoint and retained runtime controls, then failed live
preflight before claiming its grant. Measurement/checkpoint registration was
registry v3 (`0f4eda2e…13e1`), while the ledger registration was registry v2
(`8e724aa0…b717`). The fixed runner's own registry alias was omitted from the
otherwise complete v3 binding context. The ledger remains ready/use-zero, the
target and checkpoint are `a9831e62…4da0`, and no observer request or repair
occurred.

The exact reconciler retains the checkpoint and evidence, records the mismatch,
and releases only matching controls plus the empty runtime exchange. v10 binds
the core runner registry alias to registry v3 for the transaction and restores
it afterward; it uses fresh v7 paths, a fourth unique checkpoint identity and
a sixth fresh authority identity. The complete SA4 suite passes 330/330.
