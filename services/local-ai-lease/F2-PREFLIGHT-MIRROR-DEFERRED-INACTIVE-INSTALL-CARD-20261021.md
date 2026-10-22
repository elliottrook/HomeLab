# F2 preflight mirror-deferred correction — inactive-install card

Status: source-only correction; HOLD. This card is not authorization to
install, retry October 21, reschedule timers, run a scan, create a receipt,
acquire a lease, stop production, clear failed units/state, or push.

## Retained evidence and practical cause

The approved October 21 prepare failed at 01:15 with bounded state:

`schema=aster-f2-scheduled.v1`, `state=no_go`,
`first_failure_phase=prepare`, `failure_class=PREFLIGHT_FAILED`; no prepared
snapshot or result rows were written. Proxmox has current 00:30 artifacts for
104/110/116 and TrueNAS task 1 completed successfully. The current-cycle
LXC110 mirror is absent because its fixed job is scheduled for 02:00. The F2
prepare implementation incorrectly required that future mirror before 02:00,
so it could never succeed at the approved 01:15 window.

No retry or reschedule is authorized. The October 21 terminal state, failed
services, and absent snapshot remain historical evidence.

## Smallest source correction

Replace only the installed snapshot collector:

| Source | Installed target | Old installed SHA-256 | Required new SHA-256 |
|---|---|---|---|
| `scripts/local-ai/f2_preflight_snapshot.py` | `/usr/local/libexec/local-ai-lease/f2_preflight_snapshot.py` | `a2324d6a5ba4869778713319a511acc207f1d8332dd1af7e4520be382cfe02fa` | `a199e369b2a3843a911a3978b410b525db7f1c67a9a8a7878f86f4a829cf57d7` |

The correction removes only the pre-02:00 LXC110 mirror requirement and leaves
the field empty as an explicit deferred value. F5 remains responsible for
validating the completed 02:00 mirror. Proxmox artifacts, task-1 completion,
fixed schedule identity, lease readiness, custody, and final guards remain
unchanged.

## Bounded installation and rollback

If separately approved, checkpoint the old target as
`/root/aster-f2-preflight-snapshot-rollback-22c2d86f/f2_preflight_snapshot.py`
with root-only custody, verify its old hash, install only the corrected file
as `root:root 0644`, and run target-Linux compile/import plus the focused F2
snapshot and coordinator tests. Restore only the checkpoint if any hash,
custody, import, or test check fails.

Do not install or enable any timer, alter the October 21 timer state, clear
the failed prepare/final services, delete the terminal state, invoke the F2
coordinator, query zstd, create a receipt, acquire a lease, stop a service,
call a model, or change backup schedules. A later exact-cycle timer card must
be separately prepared and approved after this correction is reviewed.

## Offline pins and tests

The source correction was tested with the existing F2 coordinator contract:

| Source | SHA-256 |
|---|---|
| `scripts/local-ai/f2_preflight_snapshot.py` | `a199e369b2a3843a911a3978b410b525db7f1c67a9a8a7878f86f4a829cf57d7` |
| `scripts/local-ai/test_f2_preflight_snapshot.py` | `7502d7df0872850cb4f4f315ecc6ea5bfd2b49de1a241b47fdb5a5c8748f14c2` |
| `scripts/local-ai/f2_scheduled_release_candidate.py` | `98b26e88fc17418f0f48dbf24aafb3b44b06069de5fec2d244b55e58d7adb425` |

The new test proves a future LXC110 mirror is not required by F2 prepare and
that the deferred field is explicit. No live source was invoked during this
preparation.
