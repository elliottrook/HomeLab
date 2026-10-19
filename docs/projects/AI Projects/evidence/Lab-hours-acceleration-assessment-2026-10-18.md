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

The live LXC114 News ingest timer was observed firing about once per hour. A
90-minute outage allowance therefore does not translate to a 90-minute usable
lab session without a separately reviewed missed-ingest/catch-up policy. The
first 30+15 pilot fits between hourly ingests with a five-minute margin; every
later longer reservation must explicitly address that production dependency.

The first complete offline full-drain packet at platform commit `b247f57f`
was **not** cleared for disabled installation. Independent read-only Linux
checks found that its News `NextElapseUSecRealtimeUSec` probe returned an
empty value, the GPU-driver `readlink` returned a relative target while the
validator expected an absolute one, and the authentication helper was only
available through its absolute `/usr/local/sbin/` path. More seriously, the
backup check treated any nonempty Proxmox backup *schedule* list as successful
current-cycle backup evidence. That would allow a false PASS. The platform
owner was sent the actual outputs and is correcting source collection and
positive/negative tests before any target stage. The first pilot remains
NO-GO until a corrected packet passes this review and target-Linux checks.

## October 18 daytime acceleration decision

Jason accepted a **maximum 90-minute daytime Aster/voice outage** for a first
supervised pilot, excluding host reboot and fault injection. This is an outage
budget, not approval of a host installation or live service drain. The News
ingest timer runs hourly, so the first card limits itself to 30 minutes of lab
time, 15 minutes of restoration and five minutes before the next ingest.
That pilot proves isolation and recovery only. It does not yet give the MacBook
agent a verified, usable workload path, and it cannot establish unattended
recurring lab hours.

Read-only Proxmox evidence showed the current-cycle 00:30 all-guest `vzdump`
task completed successfully and positive-size current-cycle archives exist
for 104, 110 and 116. The Proxmox-to-TrueNAS observer SSH route timed out;
that is a route failure, not proof that TrueNAS itself is down. The platform
owner therefore prepared a distinct **local-Proxmox-only** preflight for the
no-reboot, no-file-change pilot. TrueNAS mirror, F2 archive integrity and F3
retained-receipt claims remain closed on this evidence.

Independent review caught a consequential source mismatch: the local-only
preflight could admit the pilot while the original final validator still
required the unavailable TrueNAS route. Platform commits through `1d230b8f`
added a separate local-only final validator and a legacy-lease readiness
check, plus synthetic partial-stop and owner-loss recovery cases. The initial
14-file card also omitted an imported dependency; `97aa7390` removed that
dependency and added a fixed host entrypoint. Subsequent review caught a
nonzero-command handling defect and a mismatch between promised authenticated
warm-up and actual restore order. Platform commits through `1b612c91`
corrected both. Stream A independently ran the 21 focused offline tests and
verified all 14 card hashes against the local source; these checks passed.

The packet is **not yet staged on Proxmox**. An exact disabled-install approval
is pending; staging would test Linux imports and leave all effects off. The
live daytime drain remains NO-GO until installed-path tests and a separate
reviewed live card pass. The short-lived entrypoint does not hold its
advisory lock across the whole proposed session. The currently installed
manual helper hashes to `67ca223d03a4922603f570c6db87fed919879aedf3706e586b2684f7be84073c`,
matching the B60 project's October 17 observation of a newer helper with an
archive-exclusion wrapper; the platform owner is verifying its exact shared
lock path and source provenance. Even if it participates in the same lock,
the gap between phased CLI invocations permits a competing acquisition. A
readiness snapshot plus human supervision is not an unattended exclusion or
recovery guarantee. The first
live run must remain attended, with any partial effect reconciled before the
lock is released; recurring lab hours need a durable supervisor and
independent owner-loss recovery proof.

**Midday design review:** The platform owner reconciled the installed manual
helper's exact hash and found that it takes the same state-directory flock on
acquisition but does not inspect a full-drain marker. This confirms the
between-invocation gap rather than removing it. A separate source-only
persistent-supervisor design at `be19d82f` and combined-pilot proposal at
`dcbcdd74` would avoid consuming an outage on isolation alone: one attended
45-minute run could stop the known consumers, exercise three fixed direct-9B
smoke requests and restore production. A later source candidate at
`6a79e987` is **not live-ready**: its first GPU-user check occurs after effects,
its smoke command can block without enforcing the cutoff, its watchdog
decision is not wired to an independent process, and the in-guest wrapper is
not yet implemented. These findings were sent to the platform owner. The
existing 14-file disabled-install question concerns only no-effect staging of
the earlier source packet; it must not be represented as approval of the
combined pilot or recurring lab hours.

The platform owner's next offline combined candidate through `632f21a3`
adds a bounded workload process, a fixed in-guest lab wrapper and synthetic
deadline/recovery tests. Independent review found a remaining process-lifetime
gate: killing the host-side `pct exec` process group does not prove the
in-guest wrapper or its separately started llama-server stopped. The wrapper
starts that server in a new session, so an abnormal wrapper termination can
leave a GPU consumer running while production is restored. The combined live
card must bind the in-guest process/PID or cgroup, test forced owner loss, and
prove no lab listener/process/GPU handle remains **before** production
unmasks. This finding was sent to the platform owner; no host change or model
call followed.

Platform source commits through `01cc0a32` now add a lease-derived systemd
scope, a recovery-only cleanup path, a distinct no-listener/process/GPU-handle
check, and a fail-closed `/proc` render-device probe after a live read-only
check found `fuser` absent in LXC110. These are **offline candidate repairs**.
The combined supervisor, in-guest wrapper, independent watchdog and GPU
absence observer have not been staged or validated together on target Linux;
no actual owner-loss or production-restoration proof exists. The earlier
14-file disabled-install card remains a separate limited package.

An independent October 18 source check at `01cc0a32` passed all **39 focused
offline tests**. It also found the decisive remaining integration gap: the
`PersistentFullDrainSupervisor` and bounded three-request workload are used by
tests but not by the host entrypoint. `full_inference_lab_runtime.py` still
exposes separate `start`, `heartbeat`, `resume` and `restore` phases and does
not invoke the persistent supervisor or smoke. A successful disabled install
of the older 14-file packet would therefore prove imports only; it would not
deliver a supervised lab session. The platform owner has been asked for one
bounded host entrypoint wired to the fixed observers, workload and recovery,
followed by a **new** exact hash-pinned disabled-install card. The older stage
approval question, if answered, applies only to that older packet and cannot
authorize installation of the combined candidate. The wrapper also needs a
target-Linux check for an already collected transient scope: cleanup must
distinguish an absent unit from a surviving process using independent
listener, process and GPU-handle evidence before production restarts.

Platform commit `f1e6715f` now adds a `--phase pilot` entrypoint that invokes
the persistent supervisor and bounded fixed smoke; the 40 focused offline
tests pass. This closes the missing import/call path **in source**, but the
tests do not yet exercise the effectful `pilot` CLI from admission through
restoration. A new process could also open the render node during the three
requests and exit between the before/after GPU snapshots. The candidate may
prove known-consumer drain and restoration; it must not claim exclusive use of
the whole B60 without continuous occupancy evidence or a deny-new-opens
boundary. Both gaps and the need for a fresh combined-source install card were
sent to the platform owner. No host stage or live pilot followed this review.

A second source check found that the pilot initializes its allowed GPU users
from **every** process holding `renderD128` before drain. An unlisted process
already using the GPU would therefore be implicitly trusted and could survive
the five service masks without failing the allowlist comparison. Admission
must bind preexisting holders to the exact accepted production process or
require no holders after drain. This counterexample was sent to the platform
owner for a regression test and source correction.

The platform owner then froze a separate 19-file host packet plus one LXC110
wrapper through `f3b62a3e`. All 20 listed file hashes matched the current
source, and 45 focused offline tests passed, including new pilot-path tests.
No target Linux stage occurred. Independent review found one remaining
admission counterexample: the revised baseline accepts any single GPU holder
whose executable path ends in the accepted `llama-server`, even if that
process is unrelated to LXC110's production `aster-llama.service`. A rogue
same-binary process could survive the five masks while remaining allowlisted.
The platform owner has been asked to bind the allowed process to the actual
service/cgroup or require zero GPU holders after drain. The pilot still lacks
continuous device admission and must not be described as host-wide exclusive
B60 time. The older 14-file approval remains inapplicable to this new packet.

Read-only target preflight after the packet freeze found Proxmox's manual
lease `ready`; LXC110's production `aster-llama.service` active and enabled;
the render node present; and the fixed `systemd-run`, `runuser`, accepted
binary, model and production authentication-probe paths present. This is
path availability only. It does not prove the target Linux import, scope
cleanup, GPU process identity, credential flow, model call, restoration or
MacBook custody, and it does not authorize staging or the live pilot.

A further read-only Proxmox check of the active production GPU holder found
the exact cgroup `0::/lxc/110/ns/system.slice/aster-llama.service`, the
accepted `llama-server` executable path, and an fd to
`/dev/dri/renderD128`. The revised source at `73b17c92` matches only the
broader `lxc/110` substring. A same-binary process in another LXC110 unit
could still be accepted as baseline. The platform owner received the observed
cgroup and a request to bind admission to the exact production unit and test
the same-guest/different-unit case. No GPU workload was started.

Platform source `b43d4971` now requires the observed exact production service
cgroup, and its synthetic same-binary/different-unit case rejects the rogue
holder. The refreshed combined card lists 19 host files and one LXC110
wrapper; all 20 hashes matched the current source. The full local AI test
suite passed **281 tests with four expected skips**. Read-only checks found
both proposed target paths absent, so disabled staging can be rolled back by
removing only newly created paths after proving no process is using them. A
new exact approval has been requested for that **disabled installation only**.
The target Linux import, full process-lifetime check and live drain remain
unproven. Continuous host-wide GPU exclusivity is still outside the pilot's
claim, and the first live run retains its separate attended approval gate.

## Disabled target installation — October 18, 15:54 Vancouver

Jason approved the **new** 19-file Proxmox plus one-wrapper LXC110 packet,
superseding the unanswered older 14-file staging request. The files were
extracted from source commit `b43d4971`, checked against the combined card,
and installed only into previously absent paths:

- Proxmox: `/usr/local/libexec/local-ai-lease/full-inference-pilot/`,
  `root:root` mode 0700 directory with 19 mode-0644 files.
- LXC110: `/usr/local/sbin/aster-llama-lab-smoke`, `root:root` mode 0750.

All **20 installed SHA-256 hashes** matched the card. The target-Linux import
preflight returned 10 modules, five drain effects, eleven restore effects and
`effects=not-attempted`. The target ran 47 focused synthetic tests successfully;
the in-guest wrapper parsed successfully. A postcheck found the manual lease
`ready`, Aster Agent, Speech and production llama active, both News timers
active, and no listener on lab port 11436. No unit/timer was installed or
enabled, no service was stopped, and no model request or live pilot was invoked.

This closes **disabled staging and target import** only. The revised combined
live run card, actual MacBook operator custody, no-overlap timing, attended
stop/recovery and independent restoration checks are still required before
using `--effect-authorized`. The pilot can demonstrate known-consumer isolation
and fixed smoke; its point-in-time GPU checks do not establish recurring or
host-wide exclusive lab hours. Rollback for this stage removes only the new
Proxmox directory and LXC110 wrapper after confirming they are unused.

The first revised live card did **not** clear the 16:05 Vancouver candidate.
It defined a 30-minute lab interval and a 15-minute restoration reserve but
compared the next News ingest against `S+1800+300`, omitting the restoration
reserve. The correct admission is at least `S+2700+300 <= N`, subject to the
source planner's exact check. More fundamentally, an interrupted owner/SSH
process has no independent live recovery executor; the present behavior
retains the lock and leaves the product outage for manual reconciliation.
That is not yet a reliable household restoration guarantee for Jason. The
platform owner has been asked to correct the arithmetic and design/test a
bounded independent rescue or prove an equivalent attended recovery path
before a live approval is requested. No effectful command was run.

A source-only one-shot guardian was proposed after this review, but its first
form does not yet meet the prearm requirement. It needs an exact lease ID
before pilot start, while the source producer creates that ID from the current
time *inside* the later pilot. If the pilot owner hangs, it also retains the
host exclusion lock; the guardian's rescue command waits for that lock and
can time out without restoring service. These are executable counterexamples,
not merely missing tests. The platform owner has been asked for a trusted
preissued identity or safe state binding, plus a bounded owner-fencing path
tested against a hung owner. The guardian and manual rescue are source-only;
the installed `b43d4971` binary has neither. The live pilot remains NO-GO.

### Guardian follow-up — October 18

The platform owner corrected the lease discovery and owner-scope fencing in
source commit `1172cf5b`. Eight focused offline tests passed. The fix is
**source-only**; the 20-file `b43d4971` target installation has not changed.
The new guardian has a further measurable deadline defect: with a durable
lease present, `rescue_at=110`, `hard_deadline=125`, and the clock at 110,
`run_guardian` gives the rescue subprocess a fixed 120-second timeout despite
only 15 seconds of reserve. A synthetic runner using that budget returned
`state=rescued` at simulated time 230, **105 seconds after the deadline**.
The owner-fencing commands can also consume time before rescue. The promised
`S+2700` restoration limit is therefore not yet enforced. This exact result
was sent to the platform owner for a bounded-time fix and regression test.

The live card still contains an older statement disclaiming automatic
owner-death recovery alongside its new guardian requirement. A reconciled
run card and a fresh hash-pinned disabled-upgrade manifest are needed before
another host stage. No live pilot or new host effect followed this review.

The platform owner subsequently bounded the rescue subprocess by the
remaining wall-clock reserve in `c3f559e2`. Independent review found the
owner-fence sequence could still consume 35 seconds from a 15-second budget;
the owner corrected that with a cumulative monotonic deadline in `b67373c4`.
Its ten focused offline guardian tests pass. These corrections remove the
specific timing counterexamples above at source level; they are **not**
installed-path proof or live owner-loss recovery evidence. The separate
four-path disabled upgrade, target-Linux checks, one-shot guardian prearm and
bounded restoration demonstration remain open.

The platform owner pinned a separate four-path disabled-upgrade card at
`31501e0c`: two replacements and two additions. Stream A compared every new
SHA-256 against a clean `b67373c4` archive, ran its complete local-AI suite
(`293` tests, four expected Mac root-custody skips), and checked Proxmox
read-only: both replacement paths still match the old `b43d4971` hashes, and
both guardian paths remain absent. This makes the proposed delta concrete but
does not authorize or execute it.

A further synthetic timeout test raised `subprocess.TimeoutExpired` from the
guardian's rescue runner. At `b67373c4` the exception escaped the one-shot
guardian; durable state remained, but no second recovery attempt occurred.
The platform owner is correcting the bounded timeout path before a final
upgrade stage. Keeping the lock on uncertainty is appropriate, but a stopped
guardian cannot meet the intended automatic-restoration claim.

The timeout exception was handled in source `6308984a`, with two additional
focused tests. The platform owner pinned the revised four-path upgrade in
`COOPERATIVE-FULL-INFERENCE-PILOT-RESCUE-GUARDIAN-UPGRADE-DISABLED-INSTALL-CARD-20261018.md`
at `7c8a252a`. Stream A independently archived exact source `6308984a`,
matched all four new hashes to the card, and ran the complete local-AI suite:
`295` tests passed with four expected Mac root-custody skips. The read-only
target hash check still showed both `b43d4971` replacement bytes and both
guardian additions absent. This is ready for a **separate disabled-stage
decision**. It does not close target-Linux, guardian prearm, live owner-loss
recovery, MacBook access or ongoing lab-hours gates.

The final source-only timing correction at `dafc0332` rechecks the declared
start after the potentially long preflight and refuses a stale or more-than-
60-second early effect start. Its updated four-file card is `da082685`; the
two runtime hashes changed, so the preceding `6308984a` staging question is
superseded. Stream A matched all four new hashes against an exact clean
archive and ran the full local-AI suite: `296` tests passed with four expected
Mac root-custody skips. No target file has been changed for this revision.

### Approved inactive rescue upgrade — October 18

Jason approved the revised `dafc0332` four-file **inactive** upgrade. The
first transfer archive contained macOS AppleDouble metadata; the exact-member
check rejected it before any target file changed. A plain four-file archive
then passed the same guard. Both old Proxmox files were checkpointed in the
root-only `/root/aster-pilot-guardian-rollback-dafc0332` directory; their
SHA-256 values match `b43d4971`. The two replacement and two added files
now match every SHA-256 in card `da082685`. The target-Linux suite passed
**65 tests**.

Independent postchecks found the manual lease `ready`, Aster Agent 104,
production llama 110 and Speech 116 active, both News timers active and
enabled, no pilot systemd unit, and no listener on lab port 11436. The
temporary transfer files were removed after verification. No guardian was
armed, service stopped, model called, or live pilot run. The platform owner
received the hash and test result for its release record. This closes the
four-file **disabled installation** only. A one-shot live guardian, verified
operator path, fresh schedule/source admission, supervised outage and
restoration remain unproved and separately gated.

### Live-source preflight NO-GO — October 18, 17:29 Vancouver

After the inactive upgrade, a read-only call to the installed
`LocalProxmoxFullDrainSourceProducer._backup_current("2026_10_18")` returned
`False`. The fixed 00:30 all-guest Proxmox job is enabled and three positive-
size current-cycle 104/110/116 archives exist at 00:34, 00:39 and 00:48.
However, the producer queries `/nodes/proxmox/tasks --typefilter vzdump`,
which returned no tasks. An unfiltered 5,000-item query returned only 689
later `push_file`/`pull_file` tasks, oldest 07:38. The completed 00:30 task
has aged out of that listing. A proposed 18:05 pilot is therefore **NO-GO**
even if its separate conditional authorization is given; no guardian was
armed, service stopped or model called.

A durable task-log file for the 00:30 `vzdump` UPID still exists. The
read-only Proxmox task-status endpoint reports `stopped`, `exitstatus=OK`,
`starttime=1792308600`; the Proxmox task file's mtime is 1792309840
(00:50:40 Vancouver), after the three artifact times, and its final line is
exactly `TASK OK`. Its actual custody is `www-data:root` mode 0640 beneath
root-owned mode-0755 task directories. This is a **candidate** source for a reviewed, bounded
completion adapter, not admission evidence from the current code. A separate
source defect also rejects this observed valid UPID because its regex omits
the final colon. Both findings and the need for ambiguity/custody checks were
sent to the platform owner. The current source must be corrected, tested and
reinstalled under its own bounded approval before a live pilot can proceed.

### Inactive backup-proof repair — October 18

The platform owner corrected the aged task-list dependency in source commit
`c66b9ae8`, using bounded `pvescheduler` start/success journal records tied to
the exact current-cycle archive times. The valid trailing colon in the
Proxmox UPID is accepted. Jason separately approved the four-file inactive
installation. Read-only inspection confirms all four installed Proxmox hashes
match that card and the rollback checkpoint retains the prior four hashes.
The focused target-Linux suite passes 10 tests; the platform owner reports
65 installed-path tests and `local_backup_proof=True` for the October 18
cycle. The manual lease remains `ready`; no pilot unit, guardian arm, lab
listener or pilot process was started. This fixes the observed backup-proof
NO-GO for this cycle, but does not establish a safe live lab window or
authorize a pilot. The proposed six-minute start window also conflicts with
the implemented 30-minute lab plus 15-minute restoration profile; a new
time-accurate live card and separate approval are required.

### Goal boundary: a successful pilot is not established lab hours

The installed `full-inference-pilot` and the separate source-only
`cooperative-lab` candidate solve different problems. The installed pilot
stops five named Aster/News consumers, runs a fixed three-request control
inside LXC110, and restores the accepted backend. It does **not** admit
arbitrary MacBook Codex work, prove the Aster full path, prevent every other
host process from opening the B60 render node, or create a recurring schedule.
The cooperative candidate keeps the production backend running but has no
reviewed MacBook client admission boundary; stopping LXC104 also removes the
current approved client path. Neither candidate alone meets Jason's requested
usable lab hours.

The programme may call lab hours *established* only after one reviewed
MacBook-to-host identity and request path is admitted under the lease; an
independent host-owned deadline and recovery path can stop that work and
restore production without the MacBook; a deterministic B60 admission
boundary prevents unlisted users (observation alone supports only a
*known-consumer* claim); and a scheduled run demonstrates the same cycle-bound
preflight, bounded work, cutoff, restoration and next-production margin.
The first supervised 30+15 pilot is valuable evidence for the drain/recovery
part of that chain. It cannot close the remaining criteria by inference.

### MacBook admission candidate review — October 18

The platform owner produced a separate offline-only admission contract at
`2a95c2d7` with staged gates for a usable MacBook workload. Stream A reviewed
the exact source, tests and design. It is not installed or connected to a
trusted transport. Two synthetic counterexamples hold its next stage:

1. `authorize_request` reads `now_epoch` from the supplied request. A matching
   request containing an in-window timestamp is admitted even when presented
   after actual expiry. The check must use a verifier-owned clock captured at
   admission, with no caller control over that value.
2. The claimed content-free receipt copies `request_id` without a format
   restriction. A caller-provided marker is echoed verbatim. Generate or
   strictly validate a bounded opaque identifier before recording it; never
   let request text or secrets become a receipt field.

The MacBook key fingerprint is likewise a request field in the candidate;
only a trusted ingress adapter's authenticated session observation can supply
it as authority. The platform owner received these findings and a concrete
offline reproduction. No host change, service stop, model call, live pilot or
permission grant followed this review. The admission candidate remains HOLD
until the trust boundary and expiry/replay tests are corrected and independently
rechecked.

The owner corrected the caller-clock and unrestricted-ID issues in source
`2e64b072`: the verifier now reads its own clock, validates the request-ID
shape and emits an ID digest. Stream A reproduced a remaining restart case:
constructing a second verifier with the same manifest admits the same ID
again because the replay set exists only in memory. The manifest also accepts
an arbitrarily long issued-to-expiry interval. These are source-level review
findings, not installed-path failures. Durable lease-bound replay/idempotency,
a bounded session expiry and an authenticated MacBook transport still gate
target staging or any live workload admission. The owner received the exact
synthetic counterexample; no host change followed.

The owner then added a file-backed replay store and a 45-minute manifest
limit in `f4fc919e`; the synthetic restart test now rejects the repeated ID.
This closes the specific in-memory replay and unbounded-window counterexamples
at source level. The future target adapter still must prove that the replay
file and lock live in a root-owned private directory, cannot be replaced by a
symlink or cleared during the lease, and are bound to the active lease
generation. A fresh missing store after lease start must not silently reopen
previous requests. The transport must derive the MacBook identity from an
authenticated session; matching caller-supplied strings are not authority.
The module remains uninstalled, and no live admission is released.
