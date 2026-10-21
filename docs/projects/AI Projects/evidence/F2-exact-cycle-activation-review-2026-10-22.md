# F2 exact-cycle activation review — 2026-10-22

## Decision

The platform candidate at local commit
`f239d097` is internally consistent and ready for a separate activation
decision. This review does not install or enable a timer and does not authorize
an archive scan.

## Reviewed sequence

| Step | Vancouver time | Boundary |
|---|---:|---|
| Prepare | 2026-10-22 01:15 | Fresh 00:30 Proxmox and 01:00 TrueNAS task-1 evidence; no future 02:00 mirror dependency |
| Final/read-only F2 | 2026-10-22 01:20 | Exact prepared state, corrected dependency pins and no competing work |
| Outer deadline | 2026-10-22 01:40 | No extension or same-cycle retry |
| Reconciliation | 2026-10-22 01:42 | Observation only; remove/disable spent date units and retain the terminal result |

The 02:00 LXC110 mirror remains a later F5 gate.

## Independent checks

The date-specific timer sources were exported from `f239d097` and verified:

- prepare timer SHA-256
  `8abd7ddb82fbedb38d72c10957998b6f533f09155dc4fa6e2fd56a0fc605f9a0`;
- final timer SHA-256
  `ef38ebc9d2fe761498813ab8c2c1182c3283eb7ba46f23577f78fb287bf1ee6d`;
- exact `OnCalendar` values 01:15 and 01:20 Vancouver;
- `AccuracySec=1s`, `RandomizedDelaySec=0`, `Persistent=no`; and
- the intended prepare and final service targets.

Read-only Proxmox checks found the five installed coordinator/correction hashes
matching the reviewed chain. Recurring F2 timers are disabled/inactive, the
lease is `ready`, no lease/lock/receipt exists, and the prior cycle has its own
date-keyed state file. A new cycle writes a distinct `2026-10-22.json` state;
it does not retry or overwrite October 21.

## Required activation boundary

If approved, the platform owner may stage only the two pinned October 22 timer
files, run `systemd-analyze verify` and `systemd-analyze calendar`, then
daemon-reload and enable them without manually starting either service. A
one-time 01:42 observation must inspect the terminal state and remove/disable
the spent date units. Any failed or uncertain prerequisite means NO-GO without
a scan or retry.

This activation does not authorize F3, a receipt, a lease, a service stop, a
full-stop drill, A1, a model call or automatic promotion.
