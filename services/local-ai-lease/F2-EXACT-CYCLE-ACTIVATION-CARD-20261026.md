# F2 exact-cycle activation candidate — 2026-10-26

Status: inactive candidate; HOLD pending separate explicit activation approval.
This card does not reuse October 25 and authorizes no timer installation,
enablement, service start, scan, receipt, lease, retry, reschedule, production
stop, model call, or F3.

## Proposed one-shot schedule

| Event | Exact Vancouver time | Required condition |
|---|---:|---|
| F2 prepare | 2026-10-26 01:15 | 00:30 Proxmox backup and 01:00 TrueNAS task 1 succeeded; no competing work |
| F2 final | 2026-10-26 01:20 | Fresh prepare state; exact-minute, source-pin, and per-subcheck guards pass |
| Hard deadline | 2026-10-26 01:40 | Disable/stop date-specific timers and reconcile observation-only |
| F5 mirror gate | after 02:00 | Validate completed LXC110 mirror; never required by F2 prepare |

| Candidate timer | SHA-256 |
|---|---|
| `services/local-ai-lease/systemd/f2-preflight-prepare-20261026.timer` | `e356915e419afa6199afa86bd997231b1d48c2a2e9f46356069d8ee5ce4788fe` |
| `services/local-ai-lease/systemd/f2-preflight-final-20261026.timer` | `fd05327676d3a5dc9383d23ca747b81be7dba1dfb88fe39a2ee535679bc6a8f4` |

## Required source baseline

Before activation, the host-exclusion pin correction must be separately
installed and verified. The required corrected source hashes are:

- `f2_preflight_fixed_wrapper.py`: `e61b7de53a277b3af747693485f398f293853314e6ad49172c9e5cc43a1a5c34`
- `f2_observer_runner_candidate.py`: `3011c419fbe3392a1d0d74d8deabf9c891985459890622aa968ab9714376c858`
- `host_exclusion.py`: `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61`
- `f2_preflight_snapshot.py`: `6340c29e91e03fa57ebe0d3404e9b36d2259b4ad10decb8c6c1412b7272cc684`
- `f2_scheduled_release_candidate.py`: `9efe6e5dc1aafdbbff5c7caa2af390a31c9b1c9935220243cd371023cb21e8a1`

Require absence only of the new cycle file
`/var/lib/local-ai-lab/f2-scheduled/2026-10-26.json`, cooperative lease/lock,
and trusted receipt. Preserve all historical October 19–25 terminal evidence.

## Cleanup boundary

After separate approval, enable only these exact-date units without manually
starting services. The Stream A observation-only Codex heartbeat owns cleanup
at 01:42 PDT: it may stop/remove only spent October 26 units, preserve all
historical evidence, and report the result. It cannot retry, reschedule, launch
F2, acquire a lease, or advance F3.
