# Stream A exercise-owner binding and launcher — inactive upgrade card

Status: **SOURCE-ONLY; NOT INSTALLED OR AUTHORIZED**

This card replaces only the owner implementation and adds its inert-by-default
launcher so a future bounded exercise can use a fixed transient systemd unit
without weakening the production owner
identity checks. It authorizes no service start, identity creation, lease,
timer, consumer, model, schedule or remote Git operation.

## Exact one-file transaction

| Source | Target | Pre-upgrade SHA-256 | New SHA-256 | Mode |
|---|---|---|---|---:|
| `scripts/local-ai/stream_a_evaluation_owner.py` | `/usr/local/libexec/local-ai-lease/stream-a-evaluation/stream_a_evaluation_owner.py` | `ee530392ca061f3ea20990d6e8f2aa137dd6b1f49b106e7806bbec273ffe1703` | `74c8072793cbbcc68e40d0548065f55031c2b8e5bfeab3d9583069aa4c8a22a1` | 0644 |
| `services/local-ai-lease/stream-a-evaluation-exercise-owner-start` | `/usr/local/sbin/stream-a-evaluation-exercise-owner-start` | `ABSENT` | `0d84d35300202c5d9316cc38a853402f7c252aab0ec5069f0b759dd3f3157d22` | 0755 |

The source commits are `7374a60be071bd9ab6db6b0f9266ec8cd4fb0d30` and
`af803abdeba7f0a4e184d8d94a7bc1b91c9e2e9c` (integrated locally as `b971f2a6`
and `00046b25`). The normal `stream-a-evaluation-owner.service` identity path
remains unchanged.

## Required inactive sequence

1. Capture root-owned checkpoints for the existing owner file and the absence
   of the launcher path, including hashes, modes, owners and
   regular-file/no-symlink properties. Refuse on drift.
2. Replace the owner file atomically and install the launcher atomically,
   retaining root custody and modes `0644`/`0755`. Do not create identity,
   intent, heartbeat, lease, lock, status, unit or timer files.
3. Run the target-local 41 evaluation-lease tests plus 23 owner/watchdog/
   observer/launcher tests with Python `-B`; require all to pass. Verify the
   exercise flag binds only `stream-a-evaluation-exercise-owner.service`, the
   copied wrapper passes every pinned argv element, arbitrary unit names are
   rejected, direct SSH launch fails closed, and normal owner mode remains
   unchanged. Run imports and static hash/mode checks.
4. Confirm all five F6 units/timers remain disabled/inactive and runtime state
   remains absent. Do not invoke `systemd-run`, the owner wrapper, heartbeat,
   watchdog or any model/backend path on the target.

## Rollback

If replacement or postcheck fails, atomically restore the checkpointed owner
file and remove the newly created launcher, then rehash and verify root
custody/mode. Preserve every other packet and all runtime custody. If state is
uncertain, retain the checkpoint and stop for manual reconciliation; never
retry automatically.

This card is a prerequisite for the prepare-only healthy-lease exercise. It
does not authorize that exercise, recurring timers, consumer systemd control,
or any effectful evaluation.
