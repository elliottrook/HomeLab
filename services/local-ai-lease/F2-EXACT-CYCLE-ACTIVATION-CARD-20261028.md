# F2 exact-cycle activation candidate — 2026-10-28

Status: **INACTIVE CANDIDATE; HOLD PENDING SEPARATE EXPLICIT ACTIVATION APPROVAL**

This is the first fresh cycle after the bounded observer-child phase diagnostic
was installed and target-tested. It does not reuse or alter the spent October
27 state. This card by itself authorizes no timer installation, enablement,
service start, scan, receipt, lease, retry, reschedule, production stop, model
call or F3 conversion.

F2 remains the early current-cycle archive-integrity gate after the 00:30
Proxmox backup and 01:00 TrueNAS task 1. Later task-2/task-3 and relay checks
belong to F4/F5 and remain outside this F2 card.

## Proposed one-shot schedule

| Event | Exact Vancouver time | Required condition |
|---|---:|---|
| F2 prepare | 2026-10-28 01:15 | Exact 00:30 Proxmox backup and 01:00 TrueNAS task 1 succeeded; no competing work |
| F2 final | 2026-10-28 01:20 | Fresh prepare state; exact-minute, source-pin and per-subcheck guards pass |
| Hard deadline | 2026-10-28 01:40 | Process group terminated at the outer deadline; no retry |
| Observation cleanup | 2026-10-28 01:42 | Read terminal state, remove only spent date-specific units and report |

| Candidate timer | SHA-256 |
|---|---|
| `services/local-ai-lease/systemd/f2-preflight-prepare-20261028.timer` | `69d0e4d2cafed2c1567009cfa87d1146c17440a7de8ac21dce17ce76eaffa843` |
| `services/local-ai-lease/systemd/f2-preflight-final-20261028.timer` | `b71e87d036ad70da437dba1c897b5b0f520ee4dff814af7f998522243ecd5545` |

## Required installed baseline

Require these exact `root:root 0644`, regular, one-link files before activation:

- `f2_preflight_fixed_wrapper.py`: `e61b7de53a277b3af747693485f398f293853314e6ad49172c9e5cc43a1a5c34`
- `f2_observer_runner_candidate.py`: `3011c419fbe3392a1d0d74d8deabf9c891985459890622aa968ab9714376c858`
- `host_exclusion.py`: `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61`
- `f2_preflight_snapshot.py`: `6340c29e91e03fa57ebe0d3404e9b36d2259b4ad10decb8c6c1412b7272cc684`
- `f2_scheduled_release_candidate.py`: `efe8bc99efd95ce85d2dbe3c8218419fdb187ceaa065cf59a906e7c0323987ec`

Before activation, repeat the installed projection assertions and focused
coordinator/observer suite. Require the complete target-Linux F2 suite to pass.

Require absence of only the new cycle file
`/var/lib/local-ai-lab/f2-scheduled/2026-10-28.json`, every lease/lock and the
trusted receipt. Preserve October 19–27 evidence byte-for-byte, including the
October 27 terminal-state digest `cf72cfbd…5d2a`. Recurring F2 timers must
remain disabled/inactive and no earlier date-specific unit may exist.

## Activation and rollback boundary

After separate approval, install and enable only the two exact-date timer
units. Do not manually start either service. Verify their resolved calendar,
hash/custody, active/waiting state, disabled recurring timers, absent new-cycle
state and healthy LXC104/110/116, Aster Agent, accepted llama.cpp/SYCL, Speech,
News timers, `pvescheduler` and `pvestatd`.

Create one observation-only reconciliation for 01:42 PDT. It may read bounded
terminal state and service status, then disable/remove only the spent October
28 timers. It cannot launch, retry, extend or replace F2, create an F3 receipt,
acquire a lease, stop a consumer or call a model.

If activation validation fails before the trigger, disable/remove only the new
timer units, daemon-reload, preserve all state and verify production. At
runtime, any failed, missing, stale, partial or uncertain gate is terminal
NO-GO for this cycle with no retry.
