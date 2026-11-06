# SA4 inactive atomic repair owner source — 2026-11-05

## Result

The previously missing single-effect operation owner is now implemented as
`sa4_atomic_repair_owner_v1.py`. It accepts no command, path, registry or retry
option. The only possible target comes from the compiled registry, while the
committed `LOCAL_HOST_ID` remains `unconfigured`, so the source cannot touch
LXC 104.

Before one atomic replacement it requires exact cross-binding of the plan,
fresh effect admission, exclusive checkpoint evidence, already-claimed one-use
ledger record, candidate digest, target registration and operation identity.
The effect admission must carry a separate owner-effect approval digest, expire
within five minutes, authorize exactly one effect and retain automatic retry
false and routing off.

The owner rereads both the mode-0600 checkpoint and mode-0644 target through
no-follow descriptors, requires their bytes to match the exact precondition,
refuses an existing temporary path, writes only the compiled same-filesystem
temporary path, fsyncs it, atomically replaces the compiled target and fsyncs
the parent. Its terminal record fixes `effect_count=1`, `retry_count=0` and
`effect-attempted-awaiting-observer`; it does not accept its own outcome.

Four disposable-filesystem tests prove one atomic replacement, preserved
checkpoint, inactive committed host binding, changed candidate/expired
admission rejection, and temporary/checkpoint-drift rejection. The full SA4
suite passes **103/103**.

## Boundary

This is source-only rehearsal code. It is not installed, not host-bound and no
live checkpoint, grant claim or repair ran. Next is independent observer and
rollback-owner production-target completion, followed by a complete disposable
transaction rehearsal. Only after that release candidate passes is the first
live canary repair eligible for Jason's exact immediate approval.

