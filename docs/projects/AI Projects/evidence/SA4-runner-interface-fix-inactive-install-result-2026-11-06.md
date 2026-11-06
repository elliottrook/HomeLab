# SA4 v5 interface correction inactive install — 2026-11-06

**Result: PASS — installed inactive; no repair authority or effect.**

Fresh preflight found both v5 destinations absent, all three v4 predecessor
files exact, the retained failed transaction inputs and empty evidence boundary
intact, the one-use ledger and runtime controls absent, and the canary still at
`a9831e62…4da0`. The lease was exactly `ready` and production was healthy.

The create-exclusive link step encountered a BusyBox `trap` quoting error after
linking the first exact staged file. Reconciliation found a clean partial state:
the first final path and its staging name were two links to the same reviewed
inode, while the second reviewed staged file remained unlinked. The bounded
installation was completed by create-exclusively linking the second file,
verifying both final hashes, and unlinking only the two staging names. Both
final files are now root-owned, mode 0644, regular one-link files with their
reviewed hashes. No rollback or target change was required.

The installed v5 runner imported its complete dependency graph and rejected one
unexpected argument with exit 1 before opening transaction input. The fixed
owner exposes the exact predecessor `BOUND_TARGET_ID` contract. The retained
failed input hashes are unchanged; the evidence directory remains empty and
root-custodied; the ledger, operation lock, emergency stop and observer exchange
remain absent. The canary is unchanged.

LXC104/110/116, Aster Agent, accepted llama.cpp/SYCL, Speech,
`pvescheduler` and `pvestatd` remained healthy with zero restarts. No signer,
authority, runner attempt, checkpoint, repair, service action, model change,
route or promotion occurred. A later repair requires a new release, fresh
owner and AI-PAM signatures, and a distinct one-use grant.
