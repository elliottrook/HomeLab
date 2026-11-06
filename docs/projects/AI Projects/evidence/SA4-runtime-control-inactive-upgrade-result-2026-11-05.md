# SA4 runtime-control inactive-upgrade result — 2026-11-05

The explicitly approved, rollback-guarded two-file inactive upgrade completed
on LXC 104 and independently validated. The canonical result is retained in
`SA4-runtime-control-inactive-upgrade-result-2026-11-05.json` with SHA-256
`10895012375e346b9fb633f287e44d00953ce1ad8e26c3af867540098e02332b`.

The installed regular files are root-owned, mode `0644`, single-link files:

- `sa4_root_transaction_owner_v1.py` —
  `e250bb2cf8bddf86634c973e968a787196ff0ae3fa7eaac10b2cd2d488404e3e`;
- `sa4_runtime_control_owner_v1.py` —
  `6d6e89d22829395373089c50eece2ffcdcc042c70c85a25a2f38867f2b330daa`.

The exact predecessor remains root-custodied under
`/var/lib/aster/sa4/source-checkpoints/runtime-control-rc1`. The installer did
not invoke either owner. The operation lock and emergency-stop state remain
absent, the ledger remains absent, and the canary remains unchanged at
`19b4e02d7f4edd9b38d9a0c3e9e3b49c4209473694fab39db0494c5fe523df1a`.
The whole-host lease is exactly ready; LXC 104/110/116 and the bounded
production checks are healthy. No authority, signature, claim, checkpoint,
target effect, service action, restart, routing or promotion occurred.

The independent verifier accepts the result, and the complete SA4 source suite
passes 158/158. The corrected runtime-control composition is installed but
inert. The next work is a fresh post-install release candidate. The prior
repair approval was spent by the pre-effect NO-GO and is not reusable.
