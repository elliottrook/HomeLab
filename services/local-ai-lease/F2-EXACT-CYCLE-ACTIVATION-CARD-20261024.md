# F2 exact-cycle activation candidate — 2026-10-24

Status: inactive candidate; HOLD pending separate explicit activation approval.
This is a fresh date-specific candidate and does not reuse or shift the
expired October 23 card. It authorizes no timer installation, enablement,
service start, scan, receipt, lease, retry, reschedule, production stop,
model call, or F3.

## Proposed one-shot schedule

| Event | Exact Vancouver time | Required condition |
|---|---:|---|
| F2 prepare | 2026-10-24 01:15 | 00:30 Proxmox backup and 01:00 TrueNAS task 1 succeeded; no competing work |
| F2 final | 2026-10-24 01:20 | Fresh prepare state; exact-minute, source-pin, and final subchecks pass |
| Hard deadline | 2026-10-24 01:40 | Disable/stop date-specific timers and reconcile observation-only |
| F5 mirror gate | after 02:00 | Validate the completed LXC110 mirror; never required by F2 prepare |

The candidate timers are nonpersistent, exact-date units with no randomized
delay. They require target-side `systemd-analyze verify` and exact-calendar
validation before any future activation.

| Candidate timer | SHA-256 |
|---|---|
| `services/local-ai-lease/systemd/f2-preflight-prepare-20261024.timer` | `0b13bcd78b6ec1623f35942bcbc9f7ae63a03433223058eac25ce0920df53376` |
| `services/local-ai-lease/systemd/f2-preflight-final-20261024.timer` | `81c7cb6a57c95f946d85348f856852db9839f469acd76ad21a3c15511a666860` |

## Installed source baseline

The diagnostic coordinator is installed at SHA-256
`98b26e88fc17418f0f48dbf24aafb3b44b06069de5fec2d244b55e58d7adb425`, with
rollback at `/root/aster-f2-final-subcheck-rollback-1ca66cee`. The four
supporting final-window sources remain pinned and installed from the prior
approved correction.

Before any activation, re-read all hashes and custody, validate both exact
calendar entries, and require absence only of:

- `/var/lib/local-ai-lab/f2-scheduled/2026-10-24.json`
- cooperative lease state and lock
- trusted F2 receipt

Preserve all historical terminal evidence from October 19–23; do not require
the historical files to be absent or delete them.

## Bounded activation boundary

After separate approval, stage and validate only these two 2026-10-24 timer
units, daemon-reload, and enable them without manually starting either service.
At completion, no-go, failure, or 01:40, the Stream A observation-only Codex
heartbeat owns cleanup at 01:42 PDT: it may disable and stop only the spent
2026-10-24 units, verify every F2 timer is inactive/disabled, and report the
terminal result. It cannot delete historical evidence, retry, reschedule,
launch F2, acquire a lease, or advance F3.

F3/F4 remain separately gated on successful F2 and a clean postcheck. Rollback
is limited to disabling/removing these two date-specific units; do not restore
the coordinator rollback checkpoint unless separately authorized.
