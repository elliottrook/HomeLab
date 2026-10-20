# F2 exact-cycle run card — 2026-10-21 Vancouver

Status: proposed, not feasible with the currently installed coordinator;
HOLD. This card creates no active schedule and authorizes no scan, receipt,
lease, production stop, model call, service repair, or retry.

## Proposed quiet window

Measured evidence places the 00:30 Proxmox backup completion near 00:50 and
TrueNAS task 1 completion near 01:06–01:07. The safer proposed one-shot window
is therefore:

| Event | Proposed Vancouver time | Required condition |
|---|---:|---|
| Prepare | 2026-10-21 01:15 | 00:30 Proxmox backup succeeded; 01:00 TrueNAS task 1 completed successfully; no competing backup, pull, lease, or maintenance |
| Final | 2026-10-21 01:20 | Fresh prepare state; all final guards pass; at least 40 minutes remain before the 02:00 LXC110 pull |
| Hard outer deadline | 2026-10-21 01:40 | Disable/stop both one-shot timers and reconcile observation-only |

The 01:20 final leaves more than the required 20-minute margin before the
02:00 pull. The 01:15 prepare has approximately eight minutes of measured
margin after the latest observed task-1 completion.

## Feasibility gate

The installed coordinator is pinned to
`aef623afc1754d4fab75e09fc4182773bc0a1db9a56d2379274fec3f0855cd23`, but its
current source accepts preparation only at 01:09 and final only from 01:10
through 01:19. Consequently, these 01:15/01:20 timers are intentionally
**not feasible for activation** until a separately reviewed and installed
source-window correction accepts those exact times. Do not activate them in
their current form.

## Exact candidate timer files

Both files are nonpersistent, one-shot candidates only:

| File | OnCalendar | SHA-256 |
|---|---|---|
| `services/local-ai-lease/systemd/f2-preflight-prepare-20261021.timer` | `2026-10-21 01:15:00 America/Vancouver` | `184cd8b0f96644519ccf666d22dcfc7cf4799dbc8457e5f68f35dd25a98c6dab` |
| `services/local-ai-lease/systemd/f2-preflight-final-20261021.timer` | `2026-10-21 01:20:00 America/Vancouver` | `a18f8a797c4f4148aa5450e5569545fac1b0c7a2266550ebb5b02912a793cf9d` |

They reference the existing candidate services, pinned as follows:

| Source | SHA-256 |
|---|---|
| `services/local-ai-lease/systemd/f2-preflight-prepare.service` | `48998c82799e39cd3f8c988c05c8d0eff73b7b63a2bd16325ef5a3cef5004e4c` |
| `services/local-ai-lease/systemd/f2-preflight-final.service` | `dd7bb66a6575956ffe55056406b1082da25377cd802a5eaeec5f30aa6d2338c5` |
| `scripts/local-ai/f2_scheduled_release_candidate.py` / installed coordinator | `aef623afc1754d4fab75e09fc4182773bc0a1db9a56d2379274fec3f0855cd23` |
| `scripts/local-ai/f2_preflight_snapshot.py` | `a2324d6a5ba4869778713319a511acc207f1d8332dd1af7e4520be382cfe02fa` |
| `scripts/local-ai/f2_preflight_fixed_wrapper.py` | `2b381465300db3d7cc1d521123665df19ff58fad12d5cccd54720b9f89cb433c` |
| `scripts/local-ai/f2_observer_runner_candidate.py` | `6d18f9c88067edb11a04eae84d7c5fb3f0d3f4eb518b359f57277205539f3a2f` |
| `scripts/local-ai/fixed_source_adapters.py` | `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9` |
| `scripts/local-ai/retained_archive_producer_candidate.py` | `5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb` |

## Required run protocol after a future source correction

1. Reconcile the 00:30 Proxmox job and its successful artifacts, then verify
   TrueNAS task 1 completed successfully on 2026-10-21.
2. Confirm tasks 2 and 3 retain their 02:00/03:00 identities without running
   them early; confirm no backup, pull, maintenance, lease, lock, or competing
   F2 process is active.
3. Activate only these two date-specific timers after a fresh approval and
   `systemd-analyze verify` plus `systemd-analyze calendar` validation.
4. At 01:15 the prepare phase records only a prepared state or a bounded,
   content-free first failure phase/class. At 01:20 the final phase performs
   the existing bounded read-only observer and never writes an admission
   receipt or acquires a lease.
5. At completion, no-go, failure, or 01:40 deadline, disable and stop both
   date-specific timers, verify all F2 timers are inactive/disabled, and run
   observation-only reconciliation. Preserve the terminal state and do not
   retry automatically.

Rollback is deletion of only the inactive candidate unit files before
activation. After any separately approved activation, rollback is disable,
stop, and remove only these two date-specific units; do not touch daily timers,
services, terminal state, or the coordinator rollback checkpoint.

## Explicit boundary

This is a source-and-calendar proposal. It does not activate timers, run a
scan, clear failed units or old state, create a receipt, acquire a lease, stop
production, call a model, modify backup schedules, or push remotely.
