# November 5: R1 assisted restoration; corrected R2 armed

Jason's operational continuation remains authorized. R1 did not qualify.
Production was restored and the exact lease released before its deadline.
The source-bound corrections below are deployed, and a distinct R2 is actually
armed for this afternoon. No candidate benchmark or model change is claimed.

## Actual R1 outcome

`b60-exclusive-20261105-day-r1` passed fresh integrity and admission, captured
entry, claimed at1793907113, and completed its no-experiment trial. At the
12:40 reconciliation, session phase was restoring; owner inactive, guardian
failed with fixed code UNIT_FAILURE_UNCLASSIFIED, booking claimed and markers
retained. Core production services were running but scheduled timers were
inactive. The launcher exit zero was never counted as qualification.

Fixed-field diagnosis found two timer-policy gaps: systemd omits empty
TimersMonotonic/TimersCalendar properties, and Paperless uses a nonpersistent
OnBootSec2min / OnUnitInactiveSec5min timer. The old policy rejected both the
observed omitted-field calendar shape and that monotonic profile. The old
watchdog also fenced an alive restoring owner at the trial cutoff instead of
allowing its reserved restoration window.

The exact-booking assisted recovery was hash-bound, independently launched on
Proxmox, and required both prior owner/guardian inactive with zero tasks, the
exact retained claim/binding and session lock, entry/checkpoint validation and
all existing recovery-file identities. It cleared only declared runtime masks
for rows that were not runtime-masked at entry, resumed calendar timers with
explicit skip-missed-event state cleaning, and restored Paperless using a
temporary root-owned false ExecCondition. That gate prevented the overdue
summary worker from executing, was removed before final verification, and
proved a future monotonic interval. A disposable systemd test first proved the
algorithm; no document/model worker ran in that proof.

All original metadata plans matched after temporary-gate removal. Existing
verify_entry checks, including the authenticated accepted-production probe,
passed before release. This is not a candidate/model benchmark and does not
claim no health generation occurred. No recovery bytes or credentials left
their source-local custody.

The assisted unit exited successfully. Final session is released,
production_restored=true, deadline_missed=false, manual_assistance_required=true.
The ledger is terminal failed / FAILED_RESTORED, finish1793908345 (12:52:25
UTC−07), before13:15. R1 is spent; manual assistance deliberately prevents an
unattended pass. Do not retry it.

Exact R1 protected receipts:

| Path under /var/lib/local-ai-lab | SHA-256 |
|---|---|
| exclusive-integrity/b60-exclusive-20261105-day-r1/terminal.json | 6f4265fcda19d6901c110e2d9a8caae55e2cec5c186c480748beb73f761130e0 |
| exclusive-sessions/b60-exclusive-20261105-day-r1/admission.json | 879f231e4a91d1c354c8e96a10fbe65cf2915f496827eba26853b66b2ded2b20 |
| exclusive-sessions/b60-exclusive-20261105-day-r1/entry.json | 3fb57d79aadd1d9ecd98ab30039537acbaf9e442c9b6f2a269ce42d27bb5f9f2 |
| exclusive-sessions/b60-exclusive-20261105-day-r1/manual-recovery.json | 8c25c23084db2ef2b7688f3c4f6c06c367a0f350a5e2219acb21270bb0d0c479 |
| exclusive-sessions/b60-exclusive-20261105-day-r1/manual-recovery-terminal.json | bd2c43a1c4ec13303510accbbc0193134e52f2b032d8d4c35fde205f46eeeb79 |
| exclusive-sessions/b60-exclusive-20261105-day-r1/session.json | 809084d945090a12c44b390c0dc024a1f43e73dc28109279b9c74cf4a4dd9bc7 |
| reservations/records/b60-exclusive-20261105-day-r1.json | cf79def46bbfc5be347cd91428546d61c85b9a8abefbf266583710a57d7bdf4c |
| exclusive-releases/b60-exclusive-20261105-day-r1.json | 74158747e83a9d6f5ebd2b04b2bf71dc8152c90ce89882b8aabc38b3df033336 |

Executed assisted script retained at
`/root/b60-daytime-operational-20261105-v3/assisted-timer-recovery-231c8957.py`,
SHA-256 `231c8957817921657bb8a06f735c0797ba87db18613b7af89e3fab88ad8cb1af`.
An exact historical copy accompanies this record. Its fixed spent-booking and
source/state guards are not a general recovery interface. Never replay it.

## Permanent correction and exact dependencies

Source commit `afb2de8034f4d165d2b2f7fac797999f98331032` in
`/private/tmp/b60-resource-checkpoint-20261104` contains the following fixes:

- Parse repeated timer properties explicitly and treat omitted empty arrays
  correctly. Unsupported mixed/unknown schedules still refuse.
- Support only the observed exact Paperless monotonic profile. A false
  ExecCondition prevents any overdue workload, handles recognized interrupted
  gates, proves a future interval, removes the temporary gate and verifies
  the original schedule. An already-future interval does not wait for or invent
  an overdue activation. Unknown gate contents remain untouched. No skipped
  application job is reported successful. Active Paperless work at capture
  refuses before claim rather than relying on this idle-service resume policy.
- Preflight active timer recovery profiles before guest copying/claim/drain.
- Preserve a live restoring owner's window until the 900-second rescue margin;
  lost owners still trigger immediate independent recovery.
- Accept a freshly observed absent owner with zero PID/tasks as already fenced.
  No no-op owner is needed; nonzero stop is accepted only if a subsequent exact
  observation proves emptiness. Unknown/nonempty states remain refused.
- Keep archive integrity fresh through the later claim, not only preparation.

217 controller tests, six daytime tests and115 B60 tests pass against this
explicit source. Target-Linux checks passed28 timer/guardian/rollback tests,
five final timer-source rollback tests and11 owner-scope/source rollback tests.
Three disposable systemd recovery scenarios cover new/interrupted/unknown gates;
an additional actual-systemd test proves both overdue and already-future
intervals without executing the test worker through resume. These are synthetic
or disposable evidence, not live unattended qualification or model capability.
The initial owner-scope target import needed both declared pinned runtime and
tool roots; the isolated rerun asserted the exact loaded source and passed.
No untracked dependency or fake host-idle result is presented as live proof.

All source transitions used the shared-exclusion source adapter, exact old/new
maps, root-private checkpoints, comparison/import validation and rollback.
Final source map:
`96201c5d13d42886055f708a5c33b70108c51fdbbcd018bf28592458cf8dd4bd`.
Final bundle descriptor:
`dc06330ed1b602269f2a5100dfad6a82cd024428218646011ea37da7442b6cb5`.
Final source-only packet `/root/b60-timer-recovery-operational-20261105-v3/packet.tar`,
SHA-256 `76d1b220f6233e668bc14d66ddf0df265e14659ada7fd0d88c57d26a641012fd`;
42-tool manifest `5f48f4125014ddb615d27ff3a6924999acd3d6f526a7e97decd14ac1bce30829`.
The test closure uses those tool files plus the separately pinned30 runtime files.
Portable source commits are retained under scripts/b60-inference/timer-recovery-20261105.

## Actual R2 arming — final revision 3

Reservation `b60-exclusive-20261105-day-r2`, owner b60-stream-a, exclusive-stack,
start1793916000/end1793918700: **15:00–15:45 Vancouver UTC−07**, with recovery
reserve through16:00. It is a distinct future attempt, not R1 retry. At observed
epoch1793909837 both unique date-specific timers were enabled/active/waiting,
empty prior trigger, with inactive services/MainPID0/empty start timestamp:

- integrity: **14:05**;
- qualification: **15:00**.

No model experiment is scheduled. All30 runtime pins, five plans/four helper
hashes per guest and15 consumer rows independently verify. No guest helper
changed in this correction. Fresh profile is qualification-only, experiment
null and trial300. As the pre-execution edge cases were tightened, only R2's
untriggered clocks were temporarily paused under ready/exclusion/time guards.
Its exact old profile was checkpointed; atomic rebind changed only source
pins, preserved all other fields and rearmed the same still-future clocks.
No service, reservation time or spent attempt was altered. All earlier arming
revisions remain immutable history; use final revision3 below.

- `/var/lib/local-ai-lab/arming-receipts/b60-exclusive-20261105-day-r2-revision3.json`:
  `370f16fd24db4bfa314eb1131ebfaa3ec0b3da0cca3b6f6f82cc17db446e67eb`.
- Profile `/var/lib/local-ai-lab/exclusive-activations/b60-exclusive-20261105-day-r2.json`:
  `6d285561a93fde2110db6bba528b74f93cf0ed9ae3dd0d9e5b6b5b31c16757e6`.
- Reserved booking digest:
  `89b11e38728f66615b1ce082839785ac57f4b539671055296f19b8d6589d4196`.
- Final owner-fence source checkpoint manifest:
  `2503a3099cadce7f76c521b3d94b3d632cd4893805081d4e44554fa574992077`;
  source journal `0614b23013befa9b0881255be1dcec89763c33ff2b0c16e189ca4a5e49da25a9`.
- Prior timer correction checkpoint / journal:
  `1bce8c9cf84511ea3ece34522e4fdd3bb824c815c06f8cd91dd339b381913b18` /
  `8676f9376cd0cb8655e3a8023ae5fca0817e665d67ba7d8068baec0ec70deff9`.
- Final profile-rebind receipt under profile-updates/r2-owner-fence-20261105-v1:
  `fb00d17481133bd83ae03382de2f46a7259f1a0cf0dca7d18b2ce0c181c87242`.

At postcheck1793909960 Agent104, accepted inference110 and Speech116 were
active/running. Both News timers, Paperless timer and EPUB monitor were
active/waiting and enabled; R1 and R2 temporary deny gates were absent; lease
ready, shared ownership clear. This is current unit/gate-state evidence, not
a new model experiment or prospective R2 result. The standard recovery health
probe is separate from capability/latency measurement. No global driver,
package, boot, backup, credential or unrelated household/TTS change occurred.

## Exact next action and peer receipt

The existing operational continuation is updated to **15:10** and this final
source/receipt. Read actual integrity, admission, session, ledger and terminal /
release evidence after the booked run. If the exact owner is alive and restoring,
do not duplicate or interrupt it; its guardian owns the reserved rescue margin.
Never reinstall this migration or replay R1. R2 pass remains unproven until
actual full restoration/release. Normal restore-only success still does not
close separate owner-loss/resource recovery or27B+ reasoning-on grounded
capability and fresh9B complete-answer p50/p95 milestones.

The Adaptive peer independently published its R1 recovery audit, including a
no-op scope intervention and a second helper that safely failed on the session
lock while this assisted recovery held it. This is received evidence of shared
recovery activity, not a claim the sessions were independent or that the peer
read the new response. The source fix above removes the need to create no-op
owner units. Please inspect the exact current B60 owner/session/lock before
any further B60 intervention; do not race the R2 owner or its guardian. No
parallel recovery is requested. The retained exclusive binding remains authority.

- Received `0233187b2a6afd17aa4fcb4420b530dd04b7a3a3` / `docs/projects/AI Projects/evidence/B60-daytime-exclusive-recovery-2026-11-05.md` / SHA-256 `9ca4c396354ce296475bac8bcebc327580e1541808f17ad9f9496386111fc3d6`.
- Received `0233187b2a6afd17aa4fcb4420b530dd04b7a3a3` / `docs/projects/AI Projects/evidence/SA4-inactive-read-only-measurement-owner-2026-11-05.md` / SHA-256 `b8cf3c3853b84b86bb63438eb60d06c3269e613bed27737d0359e1395329134b`.
