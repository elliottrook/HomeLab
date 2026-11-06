# SA4 terminal reconciliation v2 inactive-install review — 2026-11-06

The correction is packaged as a create-only, four-file inactive installation
for LXC104. It does not overwrite the installed v1 chain, rewrite the spent v6
ledger, invoke a runner or signer, touch the repaired canary, restart a service
or create runtime state. The exact source hashes are pinned in the plan and the
two required installed v1 dependencies are separately pinned.

Every destination must be absent. Installation is root-owned mode 0644 with
one regular link and isolated imports only. Rollback removes only exact
after-hash files in reverse order; uncertainty retains state and stops. The
result validator requires all four exact rows, unchanged v1 dependencies,
no invocation/authority/ledger/target touch, absent runtime state, no service
actions, healthy production and ready rollback.

The complete historical and corrected SA4 suite passes **234/234**. The packet
is inert and effect-ineligible. Its next gate is the explicit inactive
installation; a repair, second target, authority packet, model call, restart,
route or promotion is not included.
