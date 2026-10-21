# F2 exact-cycle run card — 2026-10-21 Vancouver

Status: proposed source correction and inactive-install/activation card; HOLD.
This card creates no active schedule and authorizes no scan, receipt, lease,
production stop, model call, service repair, or retry.

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

F2 deliberately does not require the current-cycle LXC110 mirror at prepare:
that mirror is produced at 02:00. F5 is the first gate that validates the
completed LXC110 mirror and binds it to the later F4/F5 observation.

## Source-window correction and feasibility

The source correction pins preparation to an internal `PREPARE_MINUTE = 75`
(01:15) and final to an internal `FINAL_MINUTE = 80` (01:20). All cooperating
sources now agree on that exact final minute: the preflight final guard, the
observer admission window, and the retained producer start window. The
preflight snapshot remains valid for the fixed 01:15-to-01:20 handoff, and the
observer/producer hard deadline remains 01:40. These are exact constants, not
caller-controlled arguments or broad time ranges. The corrected source is still
source-only until the bounded installation below is separately approved.

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
| `scripts/local-ai/f2_scheduled_release_candidate.py` / proposed installed coordinator | `fd711a4c1afa9fe128464f61390d63c54f7e513a8811cbc79f0d27c522452356` |
| Currently installed coordinator / rollback source | `aef623afc1754d4fab75e09fc4182773bc0a1db9a56d2379274fec3f0855cd23` |
| `scripts/local-ai/test_f2_scheduled_release_candidate.py` | `ef336677c57a03eca0796e136cd009c2933dad947bc39917346c7eab7544a43b` |
| `scripts/local-ai/test_f2_exact_cycle_20261021.py` | `42230751765ab14e944a44ad928b996aa1044e04b68b7e81451af03b5597a7e3` |
| `scripts/local-ai/f2_preflight_snapshot.py` | `a199e369b2a3843a911a3978b410b525db7f1c67a9a8a7878f86f4a829cf57d7` |
| `scripts/local-ai/test_f2_preflight_snapshot.py` | `7502d7df0872850cb4f4f315ecc6ea5bfd2b49de1a241b47fdb5a5c8748f14c2` |
| `scripts/local-ai/f2_preflight_fixed_wrapper.py` | `2b381465300db3d7cc1d521123665df19ff58fad12d5cccd54720b9f89cb433c` |
| `scripts/local-ai/f2_observer_runner_candidate.py` | `2af6689b82dce85d4a1856ffb6803269a5e2a20bee286012ff92faf9f925578e` |
| `scripts/local-ai/test_f2_observer_runner_candidate.py` | `c564f560a8c15b4f6d5876859a99b173d99a1c40b7c3a2e505b4ba4621cc38b8` |
| `scripts/local-ai/fixed_source_adapters.py` | `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9` |
| `scripts/local-ai/retained_archive_producer_candidate.py` | `5d98f6d9dde9797a92802060b151e9929a4d24849555679f76d65f32ed7caaaf` |
| `scripts/local-ai/test_retained_archive_producer_candidate.py` | `097136b7388b98120caf8936f516ed081486459d56a8da01b745b107ad8ba070` |

## Bounded inactive installation and activation card

One bounded approval may cover both operations because they are the exact
source and date-specific timer set needed for this one cycle. It must authorize
only:

1. Preserve the installed coordinator at
   `/root/aster-f2-failure-phase-rollback-20261021` with its observed old hash
   and `root:root 0600` custody.
2. Replace only the coordinator with the corrected source as `root:root 0644`;
   run compile/import and focused tests before activation.
3. Install only the two 2026-10-21 timer files above as `root:root 0644`,
   validate them with `systemd-analyze verify` and `calendar`, daemon-reload,
   and enable them without manually starting either service.
4. After the one-shot outcome or 01:40 deadline, disable and stop both exact
   timers, verify every F2 timer is inactive/disabled, and reconcile read-only.

No daily timer, service definition, failed historical unit, terminal state,
receipt, lease, production service, backup schedule, or model endpoint may be
changed. If any hash, custody, timer state, or preflight condition differs,
stop without activation. Rollback is restoration of the one coordinator from
the fresh checkpoint, followed by disabling/removing only these two
date-specific timers; never retry automatically.

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

This is a source correction and inactive-install/activation proposal. It does
not install or activate timers yet, run a scan, clear failed units or old
state, create a receipt, acquire a lease, stop production, call a model,
modify backup schedules, or push remotely.
