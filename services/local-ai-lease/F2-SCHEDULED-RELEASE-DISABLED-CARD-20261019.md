# F2 scheduled release candidate — disabled card

Status: disabled-stage installed and verified; F2 remains OPEN. This card does
not authorize enabling a timer, running an F2 scan, issuing a lease, changing
services, or pushing to a remote.

## Purpose and boundary

This candidate separates the slow preflight from the short final gate. A
01:09 Vancouver preparation run captures the fixed snapshot. A 01:10 run
rechecks the live boundary and invokes the existing bounded observer once,
with a hard 01:40 deadline. There is no retry, extension, receipt, lease,
service stop, model request, or output capture in this candidate.

The per-cycle state is terminal: `prepared` may advance once to `complete` or
`no_go`; any later invocation for that cycle stops for review. `Persistent=no`
prevents a missed timer from being replayed after downtime. Codex heartbeat
observes state only and reports completion, failure, or required action.

## Pinned source set

Hashes below are the source and installed target set for the disabled candidate.

| Source | SHA-256 |
|---|---|
| `scripts/local-ai/f2_scheduled_release_candidate.py` | `67510f7b7be42feec28d98c80109793b6e34538ecae3e495aeb7478b36f28f3d` |
| `scripts/local-ai/test_f2_scheduled_release_candidate.py` | `7dab3d555880d6517f85a805bffb855a59fbcba28f245871054d77622efb6949` |
| `services/local-ai-lease/systemd/f2-preflight-prepare.service` | `48998c82799e39cd3f8c988c05c8d0eff73b7b63a2bd16325ef5a3cef5004e4c` |
| `services/local-ai-lease/systemd/f2-preflight-prepare.timer` | `93567ab331acc4b574ae04cbb8d3a3161d1ccbbc8cf8e153776a464aa1660aa7` |
| `services/local-ai-lease/systemd/f2-preflight-final.service` | `dd7bb66a6575956ffe55056406b1082da25377cd802a5eaeec5f30aa6d2338c5` |
| `services/local-ai-lease/systemd/f2-preflight-final.timer` | `fd64356e68508b98427338b50b87170adb1e47faa7ea0c2a5a03fcf75b81dfff` |

The release candidate depends on the already pinned fixed wrapper and snapshot
modules recorded in `F2-PREFLIGHT-FIXED-WRAPPER-DISABLED-INSTALL-CARD-20261019.md`.
It must not broaden that dependency map or silently replace the installed
disabled modules.

## Installed target paths and unit controls

The Python entrypoint is installed at
`/usr/local/libexec/local-ai-lease/f2_scheduled_release_candidate.py` as
root:root 0644. Stage the four units under
`/etc/systemd/system/` as root:root 0644. Target-Linux tests and
`systemd-analyze verify` passed; all four units remain disabled and stopped.

The prepare service creates the fixed state directory as root:root 0700 before
the Python custody check. Both services use the exact fixed `ExecStart`, `User=root`,
`NoNewPrivileges=yes`, `ProtectHome=yes`, `ProtectSystem=full`, `PrivateTmp=yes`,
`UMask=0077`, bounded startup time, `Restart=no`, and null stdout/stderr.
The timers have zero randomization, one-second accuracy, and `Persistent=no`.
The state directories are the only declared writable paths. The rollback
checkpoint is `/root/aster-f2-scheduled-rollback-correction-56fcf4f3`, with
root:root 0700 directory custody and 0600 saved files. The scheduled state
directory is root:root 0700 and empty. No daemon reload, unit enablement,
start, capture, scan, lease, service stop, or model request occurred.

The next resolved calendar times are preparation at 2026-10-20 01:09 PDT and
final at 2026-10-20 01:10 PDT. The heartbeat observes only terminal state and
reports completion, failure, or required action.

## Evidence required before activation

1. Recompute all six hashes above and revalidate every dependency pin from the
   disabled-install card after any future source change.
2. Before activation, repeat `systemd-analyze verify`, the focused target-Linux
   suites, and the full local suite.
3. Confirm no timer, service, receipt, snapshot, lease, GPU/model request, or
   service state changed during the activation decision.
4. Obtain a fresh explicit authorization for enablement and a separate fresh
   authorization for any remote push.

Until those gates are met, F2 remains OPEN and the installed candidate remains
disabled.
