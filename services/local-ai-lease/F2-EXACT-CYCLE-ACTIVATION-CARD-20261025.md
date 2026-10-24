# F2 exact-cycle activation candidate — 2026-10-25

Status: inactive candidate; HOLD pending separate explicit activation approval.
This card authorizes no timer installation, enablement, service start, scan,
receipt, lease, retry, reschedule, production stop, model call, or F3.

## Proposed one-shot schedule

| Event | Exact Vancouver time | Required condition |
|---|---:|---|
| F2 prepare | 2026-10-25 01:15 | 00:30 Proxmox backup and 01:00 TrueNAS task 1 succeeded; no competing work |
| F2 final | 2026-10-25 01:20 | Fresh prepare state; exact-minute, source-pin, and per-subcheck guards pass |
| Hard deadline | 2026-10-25 01:40 | Disable/stop date-specific timers and reconcile observation-only |
| F5 mirror gate | after 02:00 | Validate the completed LXC110 mirror; never required by F2 prepare |

The candidate timers are nonpersistent, exact-date units with no randomized
delay. They require target-side `systemd-analyze verify` and exact-calendar
validation before any future activation.

| Candidate timer | SHA-256 |
|---|---|
| `services/local-ai-lease/systemd/f2-preflight-prepare-20261025.timer` | `5902182e3da484cda6f5fc8503127840aaf752adb36e73d3a521571f3e52b5b8` |
| `services/local-ai-lease/systemd/f2-preflight-final-20261025.timer` | `0b6783ab6ae2e8625d48730cd8e5c2858cee9df9e619f62a9e55d77a0d00eeed` |

## Installed source pins

The installed diagnostic sources are already target-validated and must be
re-read before any activation:

| Installed path | SHA-256 | Custody |
|---|---|---|
| `/usr/local/libexec/local-ai-lease/f2_preflight_snapshot.py` | `6340c29e91e03fa57ebe0d3404e9b36d2259b4ad10decb8c6c1412b7272cc684` | `root:root 0644` |
| `/usr/local/libexec/local-ai-lease/f2_scheduled_release_candidate.py` | `9efe6e5dc1aafdbbff5c7caa2af390a31c9b1c9935220243cd371023cb21e8a1` | `root:root 0644` |

Rollback is preserved at
`/root/aster-f2-final-guard-rollback-770107df-20261024` with directory mode
0700. The supporting wrapper, observer, producer, and integrity pins remain
unchanged from the prior approved installation.

Before activation, require absence only of:

- `/var/lib/local-ai-lab/f2-scheduled/2026-10-25.json`
- cooperative lease state and lock
- trusted F2 receipt

Preserve all historical terminal evidence from October 19–24; do not delete or
require absence of those files.

## Bounded activation and cleanup

After separate approval, stage and validate only these two 2026-10-25 timer
units, daemon-reload, and enable them without manually starting either service.
At completion, no-go, failure, or 01:40, the Stream A observation-only Codex
heartbeat owns cleanup at 01:42 PDT: it may disable and stop only the spent
2026-10-25 units, verify every F2 timer is inactive/disabled, and report the
terminal result. It cannot delete historical evidence, retry, reschedule,
launch F2, acquire a lease, or advance F3.

F3/F4 remain separately gated on successful F2 and a clean postcheck. Rollback
is limited to disabling/removing these two date-specific units; do not restore
the coordinator rollback checkpoint unless separately authorized.
