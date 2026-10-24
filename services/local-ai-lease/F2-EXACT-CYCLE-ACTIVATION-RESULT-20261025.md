# F2 exact-cycle activation result — 2026-10-25

Status: approved one-shot activation completed; observation-only cleanup is
scheduled through `aster-f2-october-25-reconciliation` at 01:42 PDT. F3
remains gated pending the measured F2 outcome and clean postcheck.

## Activated date-specific timers

Platform evidence commit: `5608c5ba`.

Both timer units are `root:root 0644`, enabled, active, and waiting. Neither
service was manually started.

| Unit | SHA-256 | Exact elapse |
|---|---|---|
| `f2-preflight-prepare-20261025.timer` | `5902182e3da484cda6f5fc8503127840aaf752adb36e73d3a521571f3e52b5b8` | 2026-10-25 01:15 PDT |
| `f2-preflight-final-20261025.timer` | `0b6783ab6ae2e8625d48730cd8e5c2858cee9df9e619f62a9e55d77a0d00eeed` | 2026-10-25 01:20 PDT |

## Installed source baseline and safety post-check

The installed diagnostic hashes remain:

- `f2_preflight_snapshot.py`: `6340c29e91e03fa57ebe0d3404e9b36d2259b4ad10decb8c6c1412b7272cc684`
- `f2_scheduled_release_candidate.py`: `9efe6e5dc1aafdbbff5c7caa2af390a31c9b1c9935220243cd371023cb21e8a1`

At activation, October 25 state, cooperative lease/lock, and trusted receipt
were absent. Recurring F2 timers remain absent/inactive. LXC104/110/116 and
the Proxmox daemons were healthy.

The `aster-f2-october-25-reconciliation` automation owns observation-only
cleanup at 01:42 PDT. It may stop and remove only the spent October 25
date-specific units; it cannot retry, reschedule, invoke F2, acquire a lease,
delete historical evidence, or advance F3.

Runtime gates remain fail-closed. No receipt, lease, service stop, model call,
F3 action, or retry was authorized at activation.
