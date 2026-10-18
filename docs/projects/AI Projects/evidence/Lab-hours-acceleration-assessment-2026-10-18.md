# Lab-hours acceleration assessment — October 18, 2026

**Decision sought:** establish exclusive B60 lab time for the MacBook Codex,
with normal Aster/voice/News production restored before the next reservation.
This is a different deliverable from Stream A's F2 archive timing check, the
full-stop recovery fault drill and the A1 benchmark. No live lease, service
stop, scheduler or backend change is authorized by this assessment.

## Verified current state and repository intent

- **Verified live, read-only, 08:18 Vancouver:** Proxmox's manual
  `local-ai-lease status` returned `ready`; both watchdog and owner-heartbeat
  timers were inactive/disabled; the fixed all-guest Proxmox backup job was
  enabled at 00:30; Aster Agent (104), llama.cpp (110) and Speech (116) were
  active. LXC110's one instant of established TCP connections showed only
  Beszel, which does **not** prove that no other client can start later.
- **Repository intent:** [Local-AI-Platform-Split](../../Local-AI-Platform-Split.md)
  calls for one exclusive GPU, a host lease, production drain, bounded recovery
  and a 04:15 restoration boundary after the 00:30/01:00/02:00/03:00 backup
  chain. It permits light sessions and broader maintenance, but the recurring
  lab scheduler is not installed. News reservations are 06:15 and 17:15.
- **Implemented historical evidence:** the old manual light controller
  completed one attended drain-and-release test on October 12; an attended
  quiescence drill stopped and runtime-masked the three AI consumers and News
  timer, then restored them on October 13. These prove bounded effects in
  those tests, not reusable unattended lab-hour admission.
- **Installed limitation:** the old manual controller accepts caller-supplied
  `--backup-verified` and `--test-window`, stores no hard restoration deadline,
  stops llama.cpp along with the consumers and does not interoperate with the
  disabled strict watchdog. Source-bound application-B60 prelease adapters
  remain offline/unwired. A clock slot or another blanket approval cannot
  repair these gaps.

## Fast path: a cooperative, attended lab reservation

The smallest useful first release should isolate B60 from competing Aster,
Speech, News and other known inference clients while allowing the MacBook
agent to run a reviewed B60 workload. It should preserve the accepted
backend if the workload only tests it; an exact backend restart requires a
separate pinned rollback within the same lease. It should not permit Proxmox
reboot, injected watchdog failure, arbitrary shell, credential changes, model
promotion or a full-stop fault drill.

The controller needs a source-authenticated preflight, exclusive host lock,
lease ID/generation, start and hard restoration deadline, atomic effect
journal, fixed consumer allowlist and a way to refuse new inference starts.
The operator must remain present. Release requires an independent read-only
postcheck of the exact production model/SYCL binary, GPU visibility,
authenticated serving, Aster/Speech/News units and schedules, backup jobs and
control-plane health. Any uncertain effect retains the lock and triggers
reconciliation; do not declare production restored from `systemctl active`
alone.

A planned daytime pilot is **architecturally possible** after these controls
are staged and tested. It needs explicit acceptance of a bounded period when
Aster/voice may be unavailable, a fresh no-overlap check against News, backups
and other leases, and a restoration cutoff with reserve before the next
production event. A candidate is at most 90 minutes, ending at least 45
minutes before the 17:15 News run. Jason explicitly accepted up to 90 minutes
of daytime Aster/voice unavailability for a first supervised, no-reboot pilot.
That acceptance sets the outage budget; it does not approve a particular live
lease or prove the controller can meet it. The first implementation can use a
stricter 45-minute work period and 15-minute restoration reserve.

The overnight F2 archive scan is **not inherently the critical path** for a
cooperative, no-reboot lab reservation. It is the current full-stop drill's
integrity gate. A daytime F2 scan would need a different source-bound backup
card because the installed guard is fixed to 01:10–01:19 after that night's
backup and TrueNAS task 1; it would still not create F3's trusted receipt.
The lab reservation must nevertheless identify a usable rollback checkpoint
and the exact accepted B60 artifact before any backend-changing work.

## Two release levels; no inferred promotion

| Level | Earliest evidence needed | What it permits | What remains closed |
| --- | --- | --- | --- |
| Attended cooperative pilot | Source-authenticated current state; exact consumer inventory and deny-new-start mechanism; bounded lease/deadline/journal; synthetic and target-Linux disabled checks; exact daytime outage and rollback card; Jason's approval | One supervised lab session, with one reviewed workload and production restoration before release | Host reboot, unattended hours, fault injection, general model promotion, F2/F3/F6 and A1 |
| Recurring unattended maintenance hours | Above plus independent watchdog/owner-loss recovery, proved at a bounded live drill; scheduler exclusion and fresh source-bound admission every cycle; failure alert and hard stop | Repeated exclusive sessions with tested recovery | Any workload or permission outside its own reviewed card |

If the MacBook task needs a host reboot or if no operator can supervise, use
the second level: the independent recovery proof is then indispensable.
Neither a user acceptance of daytime downtime nor a successful light pilot
alone establishes that guarantee.

## Immediate work and approval sequence

1. Platform owner builds the cooperative lease candidate and exact disabled
   install/rollback card from the current application-B60 source, or records
   why a separate controller is required. Stream A independently reviews the
   authority, source and restoration boundaries. This source work can run
   now; no overnight backup window is needed.
2. After synthetic checks, request one exact disabled target-Linux stage;
   verify installed hashes, tests and inactive state. No service is stopped.
3. Prepare one fixed daytime pilot card with named start/end, service-impact
   budget, workload, checkpoint, operator, deadline, rollback and postchecks.
   Jason approves that concrete live pilot. Stop/restore only within it.
4. If the pilot passes, decide whether the MacBook agent's tasks fit attended
   sessions or need recurring unattended/reboot-capable hours. Only the latter
   waits for independent watchdog/drill and scheduler release.

**Current decision:** GO for accelerated offline implementation and preparation
of a daytime pilot; NO-GO for a live daytime lease or recurring unattended
lab schedule from the currently installed manual controller.

## Independent review of the first platform candidate

The platform owner's source-only candidate at `86a74294` plans a 45+15 minute
session and names the exact Aster, Speech and News units. It has no live
effects or installed host entrypoint. Independent source review found these
blocking gaps before disabled installation or a live card:

1. The reused application controller's `_safe_window` requires restoration by
   04:15 Vancouver, so its effectful `acquire()` cannot admit daytime work.
2. The planner requires `prelease.news_quiesced` while also requiring active
   News timers before the planned stop. These states need a coherent
   before/after definition and source-verified transition.
3. The planner does not bind the proposed work duration to the prelease's
   restore-start deadline or independently validate the current time and
   deadline chronology. A plan therefore cannot establish a hard stop.
4. The existing application controller stops only 104 and 116; the new News
   commands are only returned as data. There is no effect journal and verified
   recovery path for all four units in one live operation. Its direct restore
   method deliberately rejects calls.
5. A host advisory lock works only among participating entrypoints. The old
   manual controller does not participate, and the candidate has no verified
   mechanism to refuse new direct inference starts from other clients. A
   one-time connection snapshot cannot prove exclusive B60 use.

Read-only live checks on October 18 found the accepted LXC110 service active
with Qwen3.5-9B Q4_K_M on the b11429 SYCL server; the Aster Agent and Speech
services and both News timers were active. These observations support a
baseline inventory, not exclusive access or admission. The platform owner has
been sent the five defects for correction. The next reviewable artifact is a
single source-bound host producer and effect/recovery card, not another clock
reservation or wider approval.

Subsequent source-only revisions through platform commit `1e4b341b` reduce
those first defects and narrow the initial card to **30 minutes of lab time
plus 15 minutes of restoration**, finishing at least five minutes before the
next hourly News ingest. This remains an *isolation/recovery pilot*, not yet
usable lab hours for the MacBook agent. A successful drain and restore does not
show that the other Codex can run its experiments.

The revised controller still accepts a caller-supplied restoration command
list; it must instead derive commands from its fixed allowlist and match the
persisted owner, lease and generation. Its heartbeat and owner presence are
caller claims until the host wrapper supplies trusted sources. No live
producer, target-Linux observer or deadline-enforcing supervisor is installed.
The platform owner has received these findings. **Release order:** source and
Linux proof, one attended isolation/restore pilot, then one separately reviewed
MacBook workload with direct-client exclusivity; recurring unattended hours
only after independent owner-loss recovery is measured.

## Architecture correction: drain the production backend for real experiments

The preserve-backend pilot is useful to test four consumer stops, but it cannot
by itself deliver exclusive GPU experimentation. The accepted llama.cpp server
still listens on `192.168.70.12:11435`, and an instant `ss` peer check cannot
prevent a later direct request. Building a new lease-aware gateway solely to
solve that pilot would add another trust boundary before proving the basic
lab/production transition.

For a first *usable* no-reboot lab session, the smaller candidate is to drain
the accepted LXC110 inference service along with Aster Agent, Speech and News
timers, then let the MacBook operator launch one reviewed workload through its
historically verified Proxmox SSH administration path. This removes the
production backend as a competing listener. It requires a fresh check that the
MacBook operator can use that path today, a named workload, a known-good
Qwen3.5-9B/b11429 SYCL restoration point, and exact authenticated warm-up and
schedule postchecks. Platform commit `282f9733` records the comparative
assessment and an offline 30+15 run card. Historical SSH success is not live
operator custody; no service stop or workload is yet approved or executed.

This attended light drain remains separate from the F2/F3 full-stop fault
drill. It prohibits Proxmox reboot, PCI rebind, fault injection and model
promotion. The restored production service, not an AI judgment, is the release
criterion. The platform owner is preparing its bounded controller and disabled
Linux card for independent review.
