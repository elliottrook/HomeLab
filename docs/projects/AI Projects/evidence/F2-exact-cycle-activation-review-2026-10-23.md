# F2 exact-cycle activation review — 2026-10-23

## Decision

The corrected platform candidate at commit
`58edf4e1` is internally consistent and ready for a separate activation
decision. This review installs or enables nothing and authorizes no scan.

## Reviewed sequence

| Step | Vancouver time | Boundary |
|---|---:|---|
| Prepare | 2026-10-23 01:15 | Fresh 00:30 Proxmox and 01:00 TrueNAS task-1 evidence; no competing work |
| Final/read-only F2 | 2026-10-23 01:20 | Exact prepared state, installed pins and final subchecks |
| Outer deadline | 2026-10-23 01:40 | No extension or same-cycle retry |
| Reconciliation | 2026-10-23 01:42 | Observation only; remove/disable spent date units and retain terminal evidence |

The 02:00 LXC110 mirror remains a later F5 gate and is not an F2 dependency.

## Independent checks

- prepare timer SHA-256:
  `002b84083bf87a39c9c6eb21d80bae641f9b2897e0965697df21dc9108bd3f6d`;
- final timer SHA-256:
  `dbf285345f2aa3000fd007daedf023fd90e6f29bd95af8e777dddbd7fcb8cadd`;
- both sources name the exact October 23 date and America/Vancouver zone;
- both are nonpersistent, use one-second accuracy and have no randomized
  delay;
- the prepare and final units are distinct and point to the existing services;
- only `/var/lib/local-ai-lab/f2-scheduled/2026-10-23.json` must be absent;
  historical October 19–22 terminal evidence must remain; and
- the 01:42 Stream A heartbeat owns observation and cleanup but cannot invoke,
  retry or advance F3.

Target-side `systemd-analyze verify` and calendar resolution remain activation
preconditions. The installed coordinator and supporting pins, custody, new
cycle absence, lease/lock/receipt absence, recurring timer state and production
health must be re-read immediately before activation.

## Activation boundary

After exact approval, stage only the two pinned date-specific timer files,
validate them on Proxmox, daemon-reload and enable them without starting either
service. Create one observation-only 01:42 heartbeat for this cycle. Any drift
or failed prerequisite means NO-GO without activation. This does not authorize
F3, a receipt, lease, service stop, drill, A1, model call or promotion.
