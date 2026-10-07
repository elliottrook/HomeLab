# D3 broker status-read deployment — 2026-10-06

**VERIFIED CURRENT STATE:** the bounded approved deployment is complete.
Jason's approval covered the exact [deployment preparation](D3-deployment-preparation-2026-10-06.md). That approval is consumed, not permission to repeat deployment or push Git.

## Change and recovery

Updated only `/opt/homelab-broker/broker_approval_service.py` on LXC 104 and restarted only `homelab-broker-approval.service`.

- Previous SHA-256: `c0f2e5fa5585e3867fad760b9dfa4dd917d3116a80dbf7a9d5b420372ce1d6a4`.
- Deployed SHA-256: `eeefdf23fd08602f6d78a8499a81a7db04465ae78fa3ab3806f2d7f8a385f043`, matching repository source at `cfe8dea`.
- Checkpoint: `/var/lib/homelab-broker/checkpoints/aster-status-20261006`, root-owned 0700, retaining original source/metadata and non-secret baseline. No credentials copied. Do not overwrite.
- Staged source was hash-checked and compiled, then atomically replaced preserving ownership/mode. No rollback was needed. Recovery remains restoring the checkpoint source/metadata and restarting only the approval service.

## Observations

Read-only preflight found no requests outside consumed, denied, expired or revoked states. Terminal counts were 22 consumed, 3 denied, 9 expired and 3 revoked.

| Check | Observed result |
|---|---|
| Exact `automation.status` as configured Aster UID 997 | `ok: true`, `global_enabled: true` |
| Same request as unconfigured UID 0 | Denied by peer check |
| Actor-less `management.snapshot` as Aster | Denied |
| Actor-less `management.global-enabled` as Aster | Denied before mutation |
| Global switch before/after | True, unchanged; not toggled |
| Approval socket | 0660, `hlabroker:hlabroker-approvers`, unchanged |
| Separate post-check of approval and Aster services | Both active/running |
| Aster gateway source | Unchanged SHA-256 `24bdc580f074003fe8fbb064c0f5effbded9f15a33e0a8ef07b37075d6511fb0` |
| Companion page HTTP check | 200 |

Source: direct SSH/pct execution and separate systemd/HTTP checks in this task. No secret values or real privileged approval were inspected. HTTP 200 proves page reachability, not a complete human passkey approval flow. Prior local regression evidence remains 84 broker tests including 12 approval-service tests; unchanged tests were not rerun.

## Limits and resume

The production broker now exposes this narrow read. The delegation callback is **not wired into the deployed gateway**, and delegation remains disabled. Native Companion changes are built candidates, not installed. No new identity, credential, group membership, model call, switch toggle or Git push occurred.

Next: finish credential custody/bootstrap and disabled gateway/worker wiring. Keep human credentials separate. Prepare a bounded integration deployment with rollback before seeking approval; do not repeat authentication-only or model canaries. The earlier stop-reporting failure remains unexplained and retained.
