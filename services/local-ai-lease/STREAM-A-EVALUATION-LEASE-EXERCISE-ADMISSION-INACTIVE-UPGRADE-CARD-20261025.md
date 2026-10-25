# Stream A exercise admission — inactive upgrade card

Status: **SOURCE-ONLY; NOT INSTALLED OR AUTHORIZED**

This card replaces the lease contract, adapter and entrypoint so the bounded
prepare-only exercise cannot use production receipt claims, production-length
deadlines or workload progression. It authorizes no install, lease, identity,
consumer, model, timer, schedule or remote Git operation.

## Exact three-file transaction

| Source | Target | Pre-upgrade SHA-256 | New SHA-256 | Mode |
|---|---|---|---|---:|
| `scripts/local-ai/evaluation_lease.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease.py` | `e79c74035acf22222105b4a8cdcc00f75608bf2289732b4cba9a625252fe45b2` | `5c5aa6c7174d53edb775f9a2640a867634b04a9b098d0742a589a1c2dc692686` | 0644 |
| `scripts/local-ai/evaluation_lease_adapter.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_adapter.py` | `304edaf3c2f247ac874b333331ee0098ac41d2776877c3ee51431152c294c877` | `e116ff6f3ea217cefdc21f3a5e93864ad0ea63c666f7dec143f7525fd6498d5b` | 0644 |
| `scripts/local-ai/evaluation_lease_entrypoint.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/evaluation_lease_entrypoint.py` | `7425ffe9bd6c8b70c41fe3856343a0454d726e54d0f0531cd7ce7225118a332c` | `0dab61905c834c36e3a865f8049c2650712422ddc27c534f1cd402b4e5ad52bb` | 0644 |

Source commit: `7fbbc017630dc7ab87b212fc3a92ba92bb48663b`.

## Required inactive sequence

1. Capture root-owned checkpoints of all three exact prehashes, modes, owners,
   regular-file/no-symlink properties and the containing directory. Refuse on
   any drift.
2. Replace only the three listed files atomically, retaining root custody and
   mode `0644`. Do not change the watchdog, owner/launcher packet, wrappers,
   units, timers, host exclusion or runtime custody.
3. Run 45 evaluation-lease tests plus 23 owner/watchdog/observer/launcher tests
   with Python `-B`; require all 68 tests to pass. Verify the exercise marker,
   receipt-free schema, two-minute hard deadline, five-minute restore deadline,
   absent workload pointer, exact state mode, zero-command PREPARED recovery,
   operation-lock cleanup and fail-closed rejection of quiesce,
   post-quiescence, start, outcome and production resume paths.
4. Run imports, static hash/mode checks and `git diff --check`. Confirm all
   five F6 units/timers remain disabled/inactive and runtime state remains
   absent. Do not invoke `exercise-prepare`, prepare, quiesce, restore,
   heartbeat, start, outcome, watchdog effects or model/backend paths on the
   target.

## Rollback

If replacement or postcheck fails, restore all three checkpointed files
atomically and rehash them. Preserve every other packet and all runtime
custody. If state is uncertain, retain the checkpoint and stop for manual
reconciliation; never retry automatically.

This card is a prerequisite for the prepare-only healthy-lease exercise. It
does not authorize that exercise or any effectful evaluation.
