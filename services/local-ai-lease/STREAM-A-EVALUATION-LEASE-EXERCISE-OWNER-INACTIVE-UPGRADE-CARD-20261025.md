# Stream A exercise-owner binding — inactive upgrade card

Status: **SOURCE-ONLY; NOT INSTALLED OR AUTHORIZED**

This card replaces only the owner implementation so a future bounded exercise
can use a fixed transient systemd unit without weakening the production owner
identity checks. It authorizes no service start, identity creation, lease,
timer, consumer, model, schedule or remote Git operation.

## Exact one-file transaction

| Source | Target | Pre-upgrade SHA-256 | New SHA-256 | Mode |
|---|---|---|---|---:|
| `scripts/local-ai/stream_a_evaluation_owner.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_owner.py` | `ee530392ca061f3ea20990d6e8f2aa137dd6b1f49b106e7806bbec273ffe1703` | `74c8072793cbbcc68e40d0548065f55031c2b8e5bfeab3d9583069aa4c8a22a1` | 0644 |

The source commit is `7374a60be071bd9ab6db6b0f9266ec8cd4fb0d30` (integrated
locally as `b971f2a6`). The normal `stream-a-evaluation-owner.service`
identity path remains unchanged.

## Required inactive sequence

1. Capture a root-owned checkpoint of the exact prehash, mode, owner,
   regular-file/no-symlink property and containing directory. Refuse on drift.
2. Replace only the one listed owner file atomically, retaining root custody
   and mode `0644`. Do not create identity, intent, heartbeat, lease, lock,
   status, unit or timer files.
3. Run the target-local 41 evaluation-lease tests plus the 21 owner/watchdog/
   observer tests with Python `-B`; require all to pass. Verify the exercise
   flag binds only `stream-a-evaluation-exercise-owner.service`, arbitrary unit
   names are rejected, direct SSH launch fails closed, and normal owner mode
   remains unchanged. Run imports and static hash/mode checks.
4. Confirm all five F6 units/timers remain disabled/inactive and runtime state
   remains absent. Do not invoke `systemd-run`, the owner wrapper, heartbeat,
   watchdog or any model/backend path on the target.

## Rollback

If replacement or postcheck fails, atomically restore only the checkpointed
owner file, rehash it and verify root custody/mode. Preserve every other
packet and all runtime custody. If state is uncertain, retain the checkpoint
and stop for manual reconciliation; never retry automatically.

This card is a prerequisite for the prepare-only healthy-lease exercise. It
does not authorize that exercise, recurring timers, consumer systemd control,
or any effectful evaluation.
