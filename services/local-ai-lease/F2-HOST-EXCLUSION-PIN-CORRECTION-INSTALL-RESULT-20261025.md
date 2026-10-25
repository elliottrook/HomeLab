# F2 host-exclusion pin correction installation result — 2026-10-25

Status: approved two-file correction installed and validated; timers remain
inactive and no F2 cycle was run.

## Installed files

| Path | SHA-256 | Custody |
|---|---|---|
| `/usr/local/libexec/local-ai-lease/f2_preflight_fixed_wrapper.py` | `e61b7de53a277b3af747693485f398f293853314e6ad49172c9e5cc43a1a5c34` | `root:root 0644` |
| `/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py` | `3011c419fbe3392a1d0d74d8deabf9c891985459890622aa968ab9714376c858` | `root:root 0644` |
| `/usr/local/libexec/local-ai-lease/host_exclusion.py` | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` | unchanged, canonical dependency |

Prior wrapper and observer files are preserved at
`/root/aster-f2-host-pin-rollback-3ae489db-20261025` with root-only directory
mode 0700 and files mode 0600.

## Validation and safety result

- Target-Linux pin, observer, and wrapper validation: 17/17 passed.
- Temporary validation files were removed.
- October 26 date-specific timers are absent/inactive.
- Recurring F2 timers remain disabled/inactive.
- The October 26 cycle state, cooperative lease/lock, and trusted receipt are
  absent.
- No F2 process, scan, lease, receipt, service stop, model call, retry, or F3
  action occurred.

## Next activation gate

The next candidate is [F2-EXACT-CYCLE-ACTIVATION-CARD-20261026.md]. Activation
still requires separate approval, fresh hash/custody checks, exact-calendar
validation, and the same observation-only 01:42 cleanup boundary.
