# M1 independent approval-ingress unit candidate — 2026-10-24

## Current live boundary

A read-only LXC104 check found all three existing services active and enabled:
`homelab-broker`, `homelab-broker-approval` and `aster-agent`. Aster remains UID
997 and a member of `hlabroker-approvers`; that group still contains `aster`.
There is no `aster-approval` account. The approval service still accepts
`--approver-user aster`, creates its socket under `/run/homelab-broker`, and
shares that runtime directory with the execution broker. Aster listens privately
on `192.168.70.10:9120`; no 9121 listener exists.

This confirms the earlier separation finding remains current. The healthy live
services were not restarted or changed, and no approval, request, token, socket
message or credential was read.

## Offline candidate

Two deliberately inactive unit candidates now make the intended process boundary
reviewable:

- `aster-approval-ingress.service.candidate` runs only the existing approval
  ingress factory as a dedicated `aster-approval` identity on the private 9121
  listener. It has no chat or model entrypoint.
- `homelab-broker-approval-independent.service.candidate` gives the approval
  socket its own runtime directory and accepts only the dedicated identity/group.
  It is not coupled to execution-broker runtime-directory ownership.

Neither file has an enablement section. No account, unit, listener, firewall,
proxy route, socket ACL, environment file or Companion configuration was created.
The candidates contain no approver subject hash or credential.

Five static tests pass. They verify inactive status, absence of the AI-facing
`aster` identity and old approver group, the independent socket path, the private
approval-only command, bounded address families and baseline systemd hardening.

A later [environment-lineage review](M1-independent-ingress-environment-lineage-2026-10-24.md)
found that the broker candidate referenced an environment variable without
loading its source. The corrected candidate loads the same root-managed file and
subject-hash variable as the ingress. The expanded static and focused approval
path now passes 18/18. This source correction is still uninstalled.

## Remaining deployment gate

Before a change request can be presented, the platform owner must review the
exact account creation, package/runtime compatibility, internal firewall and NPM
route, Companion URL behavior, subject-hash configuration custody, checkpoint and
restrictive rollback. The first live cutover remains Yellow-only because the
production factory has no passkey mapping; Red and management stay denied.

The cutover must avoid any interval with both Aster and the independent verifier
authorized. It must prove Aster is denied at the new socket, the verifier is
accepted, Aster chat remains healthy, approval outage is bounded, the approval
plane survives an execution-broker stop, and human SSH recovery remains usable.
That deployment is not authorized or attempted by this checkpoint.
