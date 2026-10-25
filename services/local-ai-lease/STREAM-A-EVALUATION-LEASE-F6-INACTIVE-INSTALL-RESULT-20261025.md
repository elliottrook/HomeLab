# Stream A F6 inactive installation result

Date: 2026-10-25 America/Vancouver  
Status: **PASS — INSTALLED INACTIVE; NOT ACTIVATED**

This records the platform-side result for the accepted 13-artifact F6 packet.
It is evidence of inactive installation only and does not authorize identity
creation, owner start, timer enablement, lease acquisition, consumer stop/start,
recovery, model calls, schedule changes, or push.

## Transaction result

- The first transaction attempt rolled back exactly because the local harness
  invoked inert wrappers with the wrong argument shape.
- The harness was corrected only: owner uses `--run`; heartbeat and watchdog
  use `--once`; `--effect-authorized` remains omitted.
- The same 13 pinned artifacts then installed successfully.
- Target-Linux focused suite: **51/51**.
- Installed imports, three inert wrapper responses, `systemd-analyze` checks and
  independent rehash all passed.
- All five candidate units/timers are disabled and inactive.

## Absence and health postcheck

The following remain absent: lease, operation lock, owner identity, owner
intent, heartbeat, watchdog status, restore intent, observer output and Python
bytecode. `local-ai-lease` is ready. LXC104/110/116, Aster, accepted
llama/SYCL, Speech, `pvescheduler` and `pvestatd` are healthy. The Oct 26 F2
timers remain enabled/active and unchanged.

No activation or effect phase ran.

## Rollback evidence

The failed first attempt removed only its newly created candidate files and
retained the checkpoint. The successful transaction's checkpoint and exact
rehash evidence remain platform-owned for later reconciliation. No existing
dependency file, production service, schedule, backend, GPU holder or
credential was modified.
