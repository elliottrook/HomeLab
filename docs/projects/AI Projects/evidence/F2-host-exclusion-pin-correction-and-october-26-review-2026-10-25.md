# F2 host-exclusion pin correction and October 26 review — 2026-10-25

Status: corrected installation independently verified; the separately approved
October 26 one-shot timers are active and waiting.

## Installed correction

Jason approved the bounded two-file correction from platform source commit
`3ae489db9b672f5c44d6023edbcfbdfbec8e2de0`. The platform owner recorded the
installation at `e7aeea74ac1dc61533aca06f3d51bee7078cf51c` after preserving a
root-only rollback checkpoint and passing 17/17 target-Linux checks.

Stream A independently re-read the installed hashes:

| Installed path | SHA-256 |
|---|---|
| `f2_preflight_fixed_wrapper.py` | `e61b7de53a277b3af747693485f398f293853314e6ad49172c9e5cc43a1a5c34` |
| `f2_observer_runner_candidate.py` | `3011c419fbe3392a1d0d74d8deabf9c891985459890622aa968ab9714376c858` |
| `host_exclusion.py` | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` |

The October 26 date-specific timers were absent/inactive and
`local-ai-lease status` was `ready`. No scan, lease or receipt was created.

## October 26 candidate review

The activation card and timer candidates are from the same exact platform
commit. Recomputed timer hashes match the card:

- prepare at 2026-10-26 01:15 PDT: `e356915e419afa6199afa86bd997231b1d48c2a2e9f46356069d8ee5ce4788fe`;
- final at 2026-10-26 01:20 PDT: `fd05327676d3a5dc9383d23ca747b81be7dba1dfb88fe39a2ee535679bc6a8f4`.

The other installed source pins also match: `f2_preflight_snapshot.py` at
`6340c29e…cc684` and `f2_scheduled_release_candidate.py` at
`9efe6e5d…e8a1`. The October 26 state, lease, lock and trusted receipt are
absent. Recurring F2 timers remain disabled/inactive.

Static review therefore passes. Activation still needs one exact approval.
Runtime success remains conditional on the fresh 00:30 backup, 01:00 TrueNAS
pull, archive identity, quiet-host and absence gates. A 01:42 observation-only
reconciliation must remove the spent one-shot units and report either exactly
three exit-zero rows or the first bounded failure.

Jason subsequently approved that exact activation. The platform owner recorded
it at `7d74e6cf9cd2dae057b8ed3b10e3515606f3989e`; Stream A independently
observed both date-specific timers enabled, active and waiting for 01:15 and
01:20 PDT. Recurring timers remain disabled/inactive and the lease remains
ready. The one-occurrence observation-only reconciliation is active for 01:42.
No service was manually started and no scan or F3 action occurred during
activation.

## Authority boundary

This record authorizes no manual service start, scan, retry, receipt, lease,
production stop, model call or F3 action beyond the exact timers Jason approved.
