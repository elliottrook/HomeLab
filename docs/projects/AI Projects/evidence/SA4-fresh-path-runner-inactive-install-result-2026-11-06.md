# SA4 v6 fresh-path runner inactive install — 2026-11-06

**Result: PASS — installed inactive; no repair authority or effect.**

Fresh preflight found the v6 destination and all three fresh v3 transaction
paths absent, both installed v5 files exact, the failed v2 attempt intact, the
canary still at `a9831e62…4da0`, the lease exactly `ready`, and production
healthy. The reviewed v6 runner was installed create-exclusive and now exists
as a root-owned mode-0644 one-link regular file with SHA-256
`a91d6a34…a397`.

The final-path runner imported its dependency graph and rejected one unexpected
argument with exit 1 before reading input. The v3 input, evidence and ledger
paths remained absent. All six retained v2 input hashes are unchanged; its
empty root-custodied evidence directory remains intact. The target and runtime
control paths are unchanged and absent respectively.

LXC104/110/116, Aster Agent, accepted llama.cpp/SYCL, Speech,
`pvescheduler` and `pvestatd` remained healthy with zero restarts. No signer,
authority, live runner attempt, checkpoint, repair, service action, model
change, route or promotion occurred. The next work is an unsigned release
freeze bound to this exact install result and the distinct fresh paths.
