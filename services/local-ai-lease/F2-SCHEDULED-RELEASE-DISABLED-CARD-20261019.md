# F2 scheduled release candidate — disabled card

Status: source-only, disabled, and not installed. This card does not authorize
enabling a timer, running an F2 scan, issuing a lease, changing services, or
pushing to a remote.

## Purpose and boundary

This candidate separates the slow preflight from the short final gate. A
01:07 Vancouver preparation run captures the fixed snapshot. A 01:10 run
rechecks the live boundary and invokes the existing bounded observer once,
with a hard 01:40 deadline. There is no retry, extension, receipt, lease,
service stop, model request, or output capture in this candidate.

The per-cycle state is terminal: `prepared` may advance once to `complete` or
`no_go`; any later invocation for that cycle stops for review. `Persistent=no`
prevents a missed timer from being replayed after downtime. Codex heartbeat
observes state only and reports completion, failure, or required action.

## Pinned source set

Hashes below are for the source tree and must be recomputed immediately before
any future target-Linux staging. The candidate is not installed by this commit.

| Source | SHA-256 |
|---|---|
| `scripts/local-ai/f2_scheduled_release_candidate.py` | `c45831f7b47d21115244060f6d767e2fa862cf7723cddaa022f786b38116e87c` |
| `scripts/local-ai/test_f2_scheduled_release_candidate.py` | `774aa458412e15bc8b6d58d4e2ab59c8a6fd70643d8df720b4e11192b1db4da0` |
| `services/local-ai-lease/systemd/f2-preflight-prepare.service` | `f2257d94ef077cee5bb834f4288ee507f144940dd3cad18496ba9136743694e3` |
| `services/local-ai-lease/systemd/f2-preflight-prepare.timer` | `b3b4678060dd4c2df0014efbe0c8d40ed6a6e97a3798b98f6d7e2b304b1e3423` |
| `services/local-ai-lease/systemd/f2-preflight-final.service` | `6a87414fb23997861a137d88e8a6437750e1b18680e23368e2dc1c922047b32b` |
| `services/local-ai-lease/systemd/f2-preflight-final.timer` | `fd64356e68508b98427338b50b87170adb1e47faa7ea0c2a5a03fcf75b81dfff` |

The release candidate depends on the already pinned fixed wrapper and snapshot
modules recorded in `F2-PREFLIGHT-FIXED-WRAPPER-DISABLED-INSTALL-CARD-20261019.md`.
It must not broaden that dependency map or silently replace the installed
disabled modules.

## Proposed target paths and unit controls

If separately authorized, stage the Python entrypoint at
`/usr/local/libexec/local-ai-lease/f2_scheduled_release_candidate.py` as
root:root 0644. Stage the four units under
`/etc/systemd/system/` as root:root 0644, run `systemd-analyze verify` and the
target-Linux tests, then leave all four units disabled and stopped.

Both services use the exact fixed `ExecStart`, `User=root`,
`NoNewPrivileges=yes`, `ProtectHome=yes`, `ProtectSystem=full`, `PrivateTmp=yes`,
`UMask=0077`, bounded startup time, `Restart=no`, and null stdout/stderr.
The timers have zero randomization, one-second accuracy, and `Persistent=no`.
The state directories are the only declared writable paths. No unit is enabled
or started by this source-only step.

## Evidence required before activation

1. Recompute all six hashes above and revalidate every dependency pin from the
   disabled-install card.
2. On Linux, run `systemd-analyze verify` on all four units and the focused
   scheduled-candidate, fixed-wrapper, and snapshot suites; then run the full
   local suite.
3. Confirm no timer, service, receipt, snapshot, lease, GPU/model request, or
   service state changed during staging.
4. Obtain a fresh explicit authorization for installation/enablement and a
   separate fresh authorization for any remote push.

Until those gates are met, F2 remains OPEN and this is only a reviewable
source candidate.
