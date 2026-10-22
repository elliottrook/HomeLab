# F2 exact-cycle activation candidate — 2026-10-23

Status: inactive candidate; HOLD pending separate explicit activation approval.
This card authorizes no timer installation, enablement, service start, scan,
receipt, lease, retry, reschedule, production stop, model call, or F3.

## Proposed one-shot schedule

| Event | Exact Vancouver time | Required condition |
|---|---:|---|
| F2 prepare | 2026-10-23 01:15 | 00:30 Proxmox backup and 01:00 TrueNAS task 1 succeeded; no competing work |
| F2 final | 2026-10-23 01:20 | Fresh prepare state; exact-minute, source-pin, and final subchecks pass |
| Hard deadline | 2026-10-23 01:40 | Disable/stop date-specific timers and reconcile observation-only |
| F5 mirror gate | after 02:00 | Validate the completed LXC110 mirror; never required by F2 prepare |

The candidate timers are nonpersistent, exact-date units with no randomized
delay. They require target-side `systemd-analyze verify` and exact-calendar
validation before any future activation.

| Candidate timer | SHA-256 |
|---|---|
| `services/local-ai-lease/systemd/f2-preflight-prepare-20261023.timer` | `002b84083bf87a39c9c6eb21d80bae641f9b2897e0965697df21dc9108bd3f6d` |
| `services/local-ai-lease/systemd/f2-preflight-final-20261023.timer` | `dbf285345f2aa3000fd007daedf023fd90e6f29bd95af8e777dddbd7fcb8cadd` |

## Installed source baseline

The coordinator diagnostic correction is installed at SHA-256
`98b26e88fc17418f0f48dbf24aafb3b44b06069de5fec2d244b55e58d7adb425`, with
rollback at `/root/aster-f2-final-subcheck-rollback-1ca66cee`. The four
supporting final-window sources remain pinned and installed from the prior
approved correction. Re-read all hashes, custody, timer state, lease state,
and absence of F2 state/receipt immediately before any activation.

## Bounded activation boundary

After separate approval, stage and validate only these two 2026-10-23 timer
units, daemon-reload, and enable them without manually starting either service.
At completion, no-go, failure, or 01:40, disable and stop both units and
verify every F2 timer is inactive/disabled. Preserve the terminal result and
do not retry automatically. F3/F4 remain separately gated on successful F2
and a clean postcheck.

Rollback is limited to disabling/removing these two date-specific units. Do
not restore the coordinator rollback checkpoint unless separately authorized.
