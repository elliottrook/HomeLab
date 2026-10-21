# F2 exact-cycle activation candidate — 2026-10-22

Status: inactive candidate; HOLD pending a separate explicit activation
approval. This card authorizes no timer installation, enablement, service
start, scan, receipt, lease, retry, reschedule, production stop, or model call.

## Proposed one-shot schedule

| Event | Exact Vancouver time | Required condition |
|---|---:|---|
| F2 prepare | 2026-10-22 01:15 | 00:30 Proxmox backup and 01:00 TrueNAS task 1 succeeded; no competing work |
| F2 final | 2026-10-22 01:20 | Fresh prepare state; exact-minute and dependency pins pass |
| Hard deadline | 2026-10-22 01:40 | Disable/stop date-specific timers and reconcile observation-only |
| F5 mirror gate | after 02:00 | Validate the completed LXC110 mirror; never required by F2 prepare |

Both candidate timers are nonpersistent, exact-date units with no randomized
delay. They must be validated with `systemd-analyze verify` and
`systemd-analyze calendar` before any future activation.

| Candidate timer | SHA-256 |
|---|---|
| `services/local-ai-lease/systemd/f2-preflight-prepare-20261022.timer` | `8abd7ddb82fbedb38d72c10957998b6f533f09155dc4fa6e2fd56a0fc605f9a0` |
| `services/local-ai-lease/systemd/f2-preflight-final-20261022.timer` | `ef38ebc9d2fe761498813ab8c2c1182c3283eb7ba46f23577f78fb287bf1ee6d` |

## Installed source pins

The four corrected sources are already installed and validated by
`F2-FINAL-MINUTE-CONSISTENCY-INSTALL-RESULT-20261021.md`. Re-read hashes,
custody, lease state, timer state, and absence of F2 state/receipt immediately
before any activation. Do not use the failed 2026-10-21 state as a retry target.

## Bounded activation protocol

After separate approval, stage and validate only these two 2026-10-22 timer
units, daemon-reload, and enable them without manually starting either service.
At 01:15 and 01:20, let the date-specific timers invoke the existing services.
At completion, no-go, failure, or 01:40, disable and stop both units and
verify every F2 timer is inactive/disabled. Preserve the terminal result and
do not retry automatically.

Rollback is limited to disabling/removing these two date-specific timer units;
the already installed four-source rollback checkpoint remains available but
must not be restored unless a separate rollback decision is authorized.
