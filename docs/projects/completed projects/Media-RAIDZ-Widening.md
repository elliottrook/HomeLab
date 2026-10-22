# Media RAIDZ2 widening

Owner Jason; started 2026-10-03; Stream M. User authorized beginning sequential
addition of the four SAS candidates, healthiest first. First bounded operation:
attach Z1Z4BJ7Z0000C4453Q38 (WWN 5000c50058c120ef) to the existing RAIDZ2 vdev.
Status: CLOSED — 2026-10-21, at Jason’s direction. Ten-member expansion and final scrub completed; zero repairs or ZFS errors. All ten leaves ONLINE. Automation remains PAUSED; second-drive non-medium increase 295→298 remains an unresolved review item, stable at the final check. BTVM and BK81 serve the separate disposable lab mirror.


## Close-out — 2026-10-21

Jason directed “Push and end the project” after receiving the final scrub,
capacity and health results, including the stable but unexplained non-medium
counters. This closes the bounded expansion project with that limitation
explicitly retained; it does not establish a cause or authorize future growth.

Final architecture: one production Media RAIDZ2 with ten members; Recovery
and the disposable lab mirror remain separate. Both HP additions completed
full-surface write/read verification, sequential expansion and clean subsequent
scrubs. Final validation at 17:02 PDT found all ten leaves ONLINE, zero ZFS
errors, 15.0 TiB available and Jellyfin Healthy. No new speech, service endpoint,
identity, firewall or user workflow was introduced by the widening.

Intent and efficiency review: the requested capacity increase is delivered in
the existing vdev, without another vdev or application migration. The final
available capacity provides headroom; expansion and scrub I/O have finished.
No further disk addition, retest or maintenance action is queued. The
`truenas-drive-tests` heartbeat is PAUSED and must not be resumed to replay
attachments. Routine TrueNAS storage monitoring remains the operational owner;
Jason owns hardware replacement decisions. TrueNAS retains its existing native
storage/Doctor monitoring hand-off rather than adding a duplicate Beszel agent.

Recovery and handover: qualification, backup hashes, attachment job records and
pre-change evidence remain under
`/mnt/Media/backup-ops/sas-qualification-20261018/`. Configuration/recovery-copy
checks passed before each attachment, as recorded above. Do not attempt to undo
RAIDZ widening by removing a member. Future disk replacement requires current
serial/WWN verification, pool health checks and a separately scoped operation.

Documentation adequacy: this record preserves identities, gates, evidence,
capacity and recovery references; the enclosure record preserves the known
bay set. The individual serial-to-bay assignment for bays 3 and 6 remains
unconfirmed and must be verified before physical removal. Counter causation and
that physical mapping are deferred operational follow-ups, not claims of repair.
No addressing or NetBox service object changed in this widening. This archived
Git record is the handover authority; no wiki or derived mirror synchronization
is claimed. The close-out push is expressly authorized by Jason.

### Final scrub complete — checked 2026-10-21 17:02 PDT

The automatic post-expansion scrub finished at 12:11:10 PDT after 6h44m56s,
repairing 0 B with zero errors. Media is one ten-member RAIDZ2, all leaves
ONLINE with zero read/write/checksum errors. Available dataset capacity is
15.0 TiB, with 9.04 TiB used. All pools report healthy; Jellyfin `/health`
returns Healthy.

Both HP drives report SMART OK, zero grown defects and zero uncorrected
reads/writes. SAS PHY counters remain unchanged from qualification baselines.
Non-medium counters remain 347 (019) and 298 (01H); temperatures 35/32 C.
The second drive's previously reported increase to 298 remains unexplained
and has not received a revised acceptance from Jason. The clean scrub does
not erase that review item. Expansion and final scrub are complete; automatic
follow-up remains paused. This check made no remote changes, submitted no
duplicate scrub or attachment, and did not push Git changes.

### Final expansion complete; scrub running — 2026-10-21 07:25 PDT

Expansion completed05:26:14 PDT, copying13.6 TiB over16h35m15s. Job7221
SUCCESS. A scrub began automatically at05:26:14; no duplicate scrub submitted.
At07:25 it is32.79% complete,0B repaired, approximately4h04m remaining
(about11:29 PDT at current rate). All ten RAIDZ2 leaves ONLINE with zero ZFS
read/write/checksum errors. Media available15.1 TiB. Both HP SMART OK, zero
grown defects/uncorrected reads/writes; non-medium counts stable347/298.
Temperatures36/34 C; Jellyfin Healthy. Final scrub result still pending.
Read-only user check-in; no remote mutations or automation resumption.

### Final expansion review gate — 2026-10-20 14:51 PDT

Job7221 RUNNING, expansion13.75% (1.85/13.4 TiB),269 MiB/s, estimated12h32m
remaining (approximately03:24 PDT October21 at current rate). Single RAIDZ2,
all ten leaves ONLINE with zero ZFS errors. All pools healthy; Jellyfin Healthy.
019 stays at accepted non-medium347; 01H increased295→**298**. Both SMART OK,
zero grown defects/uncorrected reads/writes and unchanged SAS PHY counters;
temperatures37/33 C. The +3 after attachment matches the first drive's observed
pattern, but its cause is not established and the explicit gate still applies.

Successfully PAUSED truenas-drive-tests automatic follow-up for review. This
does not stop or cancel job7221 or active ZFS expansion; no disk removed, no
counter reset, no additional storage mutation. Final scrub/verification remains
outstanding. Resume monitoring only with an appropriate revised decision.

### Final attachment — 2026-10-20 12:50 PDT

Jason answered Yes when asked to accept the now-stable first-drive non-medium
count347 and resume the approved sequence. Accepted baselines are now347/295;
further growth still triggers review. Fresh preflight verified first expansion
FINISHED and subsequent scrub FINISHED with zero repairs/errors, nine ONLINE
leaves, both candidates SMART OK, zero grown defects/uncorrected errors,
unchanged PHY counters and stable347/295. Second disk alone remains unused,
serial37H0A01HFT2C1711/WWN50000397a832e289, size4,000,787,030,016 bytes.

Today's configuration archive (12:02:59 UTC, 19 apps/22 verified databases)
passed SHA256 verification:
`98c0321e3bae72ff3ee469fbc267cb2b98ebd79cca3f7e7a6dd6abf22a40b61e`.
No backup failure marker; latest three recovery-copy jobs SUCCESS. Jellyfin
Healthy, Recovery/lab healthy. Saved evidence under
`/mnt/Media/backup-ops/sas-qualification-20261018/expansion-01h/`.

Submitted pool.attach at12:50:46 PDT, pool1, existing RAIDZ2
GUID13190488833263279493, verified sdl/01H. Persisted **job7221** immediately
in attach.json. Expansion started12:50:59, tenth partition
`0713779d-47c8-41ef-a1fb-cc50b92f87d8` ONLINE. All ten leaves zero ZFS errors;
Jellyfin remains healthy. Initial ETA is not meaningful during startup.
The two-hour heartbeat is ACTIVE, instructed never to attach again and to
monitor expansion then final scrub (recognize any automatic scrub before
starting one). Completion requires clean final scrub and service/SMART checks.
No Git push authorized.

### Expansion and scrub complete — checked 2026-10-20 12:49 PDT

Expansion completed 01:31:00 PDT, 13.3 TiB copied over 15h12m58s.
Subsequent scrub completed 08:21:07 PDT after 6h50m07s, repaired 0B with zero
errors. Job3597 SUCCESS; nine ONLINE leaves, zero read/write/checksum errors.
Media reports 12.7 TiB available. Jellyfin Healthy. Both HP candidates SMART OK,
zero grown defects and uncorrected reads/writes; non-medium counters unchanged
since the review hold at 347 (019) and 295 (01H). Temperatures 35/31 C.
No second attachment or automation resumption performed during this status
check. Original accepted exception was 344/295, so 019's later increase to347
still requires a revised decision despite stability and the clean scrub.

### Review gate triggered — 2026-10-19 12:20 PDT

Job3597 remains RUNNING. ZFS reports 1.85/13.4 TiB copied, 13.86%, 265 MiB/s,
12h40m remaining (approximately 01:01 PDT October20 if rate holds). Nine leaves
ONLINE, zero ZFS read/write/checksum errors; Jellyfin Healthy, all pools healthy.
However, 019 non-medium errors increased from the accepted 344 to **347**.
01H remains at 295. Both SMART OK, zero grown defects and uncorrected reads/
writes, PHY counters unchanged, temperatures 35/34 C. Cause not established.

Paused `truenas-drive-tests` successfully under the explicit further-growth
review gate. This pauses automated follow-up and prevents second attachment;
it does NOT pause or cancel the already-running ZFS expansion. No disk removed,
no counters reset, no pool changes attempted. Existing expansion continues on
TrueNAS. Review is required before resuming progression; do not submit attach
again or infer these counts are media errors without diagnostic evidence.

## 2026-10-19 — reviewed counter exception; first HP expansion started

After being told both full write/read tests passed without bad blocks but each
non-medium counter increased by one, Jason instructed **Continue with the
expansion**. This accepts only the observed 343→344 and 294→295 increments.
Any further increase still triggers review. Historical FAIL_REVIEW result files
remain intact; neither their original classification nor the counter history
has been rewritten. All other qualification and sequential scrub gates remain.

Fresh preflight: both serials/WWNs/capacities match unused-disk inventory, SMART
OK with zero grown defects and uncorrected reads/writes, unchanged PHY counters,
non-medium stable at 344/295. Media was eight ONLINE leaves, zero ZFS errors,
no active scan/expansion. Recovery and lab healthy. Configuration export created
2026-10-19 15:33 UTC covers 19 apps and 22 verified SQLite databases; its
1,437,662,943-byte archive SHA256 matched
`747cadfea2024ef24f52314bd2c3ae606c3d8b9cb34821daa391ab6fb35a0c74`.
Latest recovery-copy jobs 2312/2594/2454 succeeded. Jellyfin Healthy.

Submitted pool.attach at 10:17:57 PDT for Media id1, RAIDZ2 GUID
13190488833263279493, verified sdg/37H0A019FT2C1711/WWN50000397a832e111.
Job **3597** is RUNNING/Expanding. ZFS expansion started 10:18:02; ninth leaf
`30827556-c0ff-4d25-ba52-99859d3d7943` is ONLINE under the same RAIDZ2.
All nine leaves report zero read/write/checksum errors. Jellyfin remains healthy.
Initial ZFS ETA is not reliable during startup; do not use middleware's 25%
formatting/job progress as data-expansion progress.

Checkpoint: `/mnt/Media/backup-ops/sas-qualification-20261018/expansion-019/`
contains attach.json with submitted job ID, pool topology, pre-attach SMART and
backup evidence. Never repeat the first attachment. The two-hour heartbeat was
updated with Jason's counter exception and job3597 and successfully reactivated.
Wait for this expansion and a clean verification scrub, then independently
recheck all prerequisites before adding 01H. No new Git push authorized.

## 2026-10-18 — full verification and ten-member expansion authorization

Jason requested full write/read verification and addition of both HP candidates.
When explicitly asked whether to replace the existing SAS members or widen to
ten, he selected **expand the existing RAIDZ2 to ten members**. This supersedes
the earlier eight-member cap for this bounded operation. Keep a single RAIDZ2;
never add either disk as a separate single-disk vdev. Two-disk parity remains.

Extended SMART tests completed successfully on both candidates: zero grown
defects, zero uncorrected reads/writes; non-medium counts unchanged at 343/294.
At 20:25:45 PDT, after fresh serial/WWN/size/unused-disk validation, launched
one full destructive 0xaa-pattern write/read pass per disk with badblocks,
4096-byte blocks, 16384-block batches, and stop after the first bad block.
Both workers confirmed RUNNING with zero initial test errors. Estimated runtime
16–24 hours, subject to measured progress. No pool changes made at this stage.

Evidence/runner: `/mnt/Media/backup-ops/sas-qualification-20261018/full-surface/`.
Each serial directory contains result.json, progress.log, bad-blocks.txt and
before/after SMART. Units: `sas-full-verify-37h0a019ft2c1711` and
`sas-full-verify-37h0a01hft2c1711`. These survive chat closure, not a NAS reboot;
interruption is not a pass and must not trigger automatic rerun. PASS requires
exit0, empty bad-block list, healthy SMART and unchanged defect/uncorrected/
non-medium counters. Review PHY counters independently before integration.

Integration sequence after both pass: recheck current configuration/recovery
backup, live pool health, exact disk identities and unused membership; attach
one candidate to the existing RAIDZ2 through pool.attach; wait for expansion
and verification scrub, then recheck health before attaching the second. Save
job IDs immediately and inspect live membership on every resumption. Final
gate is ten ONLINE members and a clean final scrub, with service checks.

Automatic approval review initially rejected unattended expansion scheduling
because the bounded user request did not explicitly authorize persistent
unattended irreversible pool changes. Jason was then explicitly asked whether
to approve unattended sequential expansion after both tests pass, with health
checks and a clean scrub before the second drive; he replied **Approve**.
The existing `truenas-drive-tests` heartbeat was successfully updated to execute
this exact sequence every two hours. It must stop and report on failed tests,
new errors, interrupted/missing evidence, unhealthy pool, uncertain topology or
unverified current recovery backups. It must inspect live membership/jobs before
each mutation, persist job IDs immediately, and never duplicate an attachment.
After ten-member expansion and a clean final scrub, report and pause the
heartbeat. This authorization does not include Git pushes or unrelated changes.

### Verification checkpoint — 2026-10-18 22:28 PDT

Both systemd workers remain active after 2h02m. Pattern-write progress is
36.28% (019) and 36.27% (01H); this is not total write-plus-read completion.
Both bad-block files remain empty and progress reports show zero errors.
SMART health passed, zero grown defects/uncorrected read/write errors;
non-medium counts unchanged at 343/294 and both SAS PHY counter sets unchanged
from the original baseline. Temperatures 38/36 C. All pools healthy. Tests
continue; no attachment or other remote mutation performed at this checkpoint.

### Verification checkpoint — 2026-10-19 00:31 PDT

Both workers remain active after 4h05m, at 67.76% (019) and 67.79% (01H)
of the write phase. Read-back verification has not yet completed. Zero test
errors and empty bad-block lists; SMART passed, zero grown defects and
uncorrected reads/writes, non-medium and SAS PHY counters unchanged against
original baselines. Temperatures 37/36 C. All pools healthy; Media remains one
eight-member RAIDZ2 with no new expansion started. No remote changes made.

### Verification checkpoint — 2026-10-19 02:35 PDT

Both workers active after 6h09m: write phase 93.11% (019), 93.07% (01H).
Read-back phase has not started. Zero test errors, empty bad-block lists,
SMART passed, zero grown defects/uncorrected reads/writes, non-medium and PHY
counters unchanged from baseline. Temperatures 37/36 C. All pools healthy;
Media still eight-member RAIDZ2. No attachment or remote mutation performed.

### Verification checkpoint — 2026-10-19 04:34 PDT

Both full-disk write passes finished and workers are now reading/comparing:
24.01% (019), 23.78% (01H), after 8h08m total elapsed. Both remain active;
zero test errors and empty bad-block lists. SMART passed, zero grown defects
and uncorrected reads/writes, with non-medium and SAS PHY counters unchanged
from original baselines. Temperatures 36/35 C. All pools healthy; Media remains
one eight-member RAIDZ2. Neither test has completed; no attachment performed.

### Verification checkpoint — 2026-10-19 06:38 PDT

Read-back comparison reached 58.50% (019) and 58.36% (01H), after 10h12m
total elapsed. Both workers active; zero test errors, empty bad-block lists,
SMART passed and zero grown defects/uncorrected reads/writes. Non-medium and
SAS PHY counters still match original baselines. Temperatures 37/35 C. All
pools healthy; Media remains eight members. No attachment or remote mutation.
Measured progress suggests completion later this morning, approximately
09:30–10:30 PDT allowing for slower inner tracks; this is an estimate, not a
completion guarantee. Both final PASS records remain required before preflight.

### Verification checkpoint — 2026-10-19 08:42 PDT

Read-back comparison at 86.48% (019) and 86.37% (01H), after 12h16m.
Both workers active with zero test errors and empty bad-block lists. SMART
passed, zero grown defects/uncorrected reads/writes; non-medium and SAS PHY
counters unchanged. Temperatures 36/34 C. All pools healthy; Media remains
eight members with no new expansion. Earlier 09:30–10:30 PDT estimate remains
plausible; final results still pending. No remote mutation performed.

### Verification completed; integration held — 2026-10-19 10:09 PDT

019 completed at 09:59:18 (13h33m); 01H completed at 10:00:53 (13h35m).
Both badblocks processes exited 0, with zero bad blocks and zero read/write/
comparison errors. SMART remains OK, grown defects and uncorrected reads/writes
remain zero. SAS PHY counters match original baselines. However, non-medium
counts rose by one each: 343→344 (019), 294→295 (01H). Both result.json records
therefore correctly say FAIL_REVIEW under the approved unchanged-counter gate.
Fresh read-only SMART confirms the same counts; kernel journal has no entries
since 08:40. No specific cause is established; do not equate these counters
alone with failed media, nor waive the gate without review.

Media remains healthy with eight members and zero ZFS errors. Neither drive
was attached. The `truenas-drive-tests` heartbeat was successfully PAUSED per
the agreed failure/review policy. No tests restarted, no counters reset, no
remote storage changes. Next action is targeted diagnosis of the non-medium
increments before seeking any revised integration decision.

## Scope and live evidence

TrueNAS 25.10.5, Media id 1, single six-disk Hitachi RAIDZ2 vdev GUID
13190488833263279493. ONLINE, zero read/write/checksum errors; expansion feature
already enabled. 72% physical allocation, 3.81 TiB dataset availability.
Recovery is a separate two-SATA mirror running extended SMART tests.

BJ7Z has zero grown defects, unchanged three historical uncorrected reads,
zero uncorrected writes, stable non-medium count 37. Original extended test and
September 25 full write/read test passed with zero bad blocks. Fresh short test
requested before attach. Identify through WWN/serial and unused-disk inventory,
not a remembered Linux device letter.

Other candidates: 471FR has 110 grown defects and three historical reads;
BTVM has zero media errors but unresolved growing non-medium counts; BK81 has
1,205 grown defects and historical read/write failures. No further disks are
queued until first expansion is complete and health reviewed. BK81 is not
recommended for this healthy pool; BTVM's unexplained counter requires caution.

## Risk and recovery

Widening permanently rewrites allocation across the existing vdev; RAIDZ2 still
provides two-disk tolerance. It cannot be rolled back by simply detaching the
new disk. Existing media are replaceable by owner policy; current non-media
backups were verified today against Proxmox and retained cloud copies. Fresh
configuration export exists from 05:01 today. No snapshot claims rollback for
pool topology. No backup deletion or consumer change is part of this operation.
The pool remains accessible but heavy I/O can reduce performance. SATA extended
tests use different drives; avoid extra bulk migration or compaction experiments.
Stop on unhealthy pool, changing disk identity, failed fresh test, or new errors.

## Implementation and validation

Use TrueNAS `pool.attach`, pool 1, target existing RAIDZ2 GUID and exactly BJ7Z.
Never use pool.update to introduce an unprotected single-disk vdev. Capture job
ID and verify the new leaf is under the same RAIDZ2, then record expansion
progress. Do not queue repeated calls or another disk while expansion is active.
After completion verify zero ZFS errors, changed capacity, SMART counters and
application availability. Existing blocks retain their old parity ratio; final
capacity is not assumed equal to a freshly built seven-disk vdev.

## Integration and persistence

TrueNAS is storage authority; Doctor already queries all pool health. TrueNAS
job/status provides progression; no new service, credentials, exposure, network,
NetBox addressing or application topology. Existing scrub scheduling remains.
No immediate quota/backup schedule changes. Repository tracks disk membership;
update operator records at completion. Resume with pool job/status and exact
serial mapping; never blindly replay attach. Git push requires separate approval.

## Milestones

- [x] Fresh short test and exact live preflight pass.
- [x] Attach initiated; correct seven-leaf RAIDZ2 and active expansion verified.
- [x] Expansion completes; pool/SMART/capacity checks pass.
- [ ] Review next candidate independently before another permanent expansion.

## Reference

https://www.truenas.com/docs/scale/25.10/scaletutorials/storage/managepoolsscale/#extending-a-raidz-vdev

## Execution evidence — 2026-10-03 11:06 PDT

Fresh short test completed without error. Immediately rechecked exact serial/WWN,
unused membership, 4 TB size, zero grown defects, stable read=3/write=0 historical
uncorrected counters, Media healthy and six ONLINE original children with zero
ZFS errors. Submitted `pool.attach` for pool 1, RAIDZ2 GUID
13190488833263279493, disk sdf/BJ7Z. Job **292** is RUNNING, Expanding.

ZFS reports expansion of raidz2-0 started 11:06:35 PDT, total 15.9 TiB to
redistribute. Seven ONLINE leaves now exist within the same RAIDZ2; the new
partition UUID is e6ee3b14-30d9-4848-ac8f-1d760123f1b1. No known data errors.
Do not interpret middleware's initial 25% formatting/job progress as actual data
expansion progress; use `zpool status Media`. Completion and final capacity are
pending. The operation persists on TrueNAS independently of this conversation.
Recovery SATA extended tests continue separately. No further SAS disks submitted.

2026-10-03 19:59 PDT check: 8.11/15.9 TiB redistributed, 50.98%, 266 MiB/s;
ZFS estimated 8h32 remaining (approximately October 4 04:31 PDT). All seven
leaves ONLINE, zero read/write/checksum errors. No further disks added.

2026-10-04 07:51 PDT: expansion finished at 05:39:56 after 18h33m21s,
15.9 TiB redistributed. All seven members ONLINE, no ZFS errors. BJ7Z remains
zero grown defects, read/write/verify uncorrected 3/0/0 unchanged. Media dataset
availability now 6.10 TiB (previously 3.81 TiB). Scrub started at expansion
completion: 26.93%, 0B repaired, estimated 5h56 remaining. Wait for scrub result
before another expansion or bulk backup migration.

2026-10-05 09:58 PDT: post-expansion scrub completed October 4 at 14:26:11
after 8h46m15s, zero bytes repaired and zero errors. All seven leaves remain
ONLINE with zero counters. Media available 5.98 TiB; Recovery 3.51 TiB.
No further expansion or backup migration has been initiated.

## Second candidate preflight — 2026-10-05 18:43 PDT

Jason requested continuing with the next SAS drive after the Recovery cutover.
Recovery's migration and first cloud relay validation passed; the next overnight
producer cycle is still pending, and the original backup sources remain intact.
Media's first expansion and scrub passed, all seven members are ONLINE with zero
errors, and no middleware jobs are running.

Selected candidate Z1Z471FR00009443T8ED, WWN 5000c50058afa24b, remains unused,
4,000,787,030,016 bytes. Its September 25 full write/read test passed; current
110 grown defects, read/write/verify uncorrected 3/0/0 and non-medium 393 remain
unchanged. It is a used disk with historical defects, not a clean-health disk.
A fresh short self-test is running. Attach only if that test completes without
error and a repeated exact-identity, topology and counter check passes. The
bounded next operation widens the existing RAIDZ2 from seven to eight members;
permanent topology change has no detach rollback. Leave BTVM and BK81 unused.
Resume by checking live topology first; never replay an attach blindly.

## Second expansion initiated — 2026-10-05 18:45 PDT

Fresh short test completed without error at 63,424 power-on hours. Repeated
preflight confirmed exact unused serial/WWN/size, unchanged health counters,
seven healthy leaves, no active scan/expansion or middleware jobs. Submitted
pool.attach for pool 1 and existing RAIDZ2 GUID 13190488833263279493, disk sdg
(Z1Z471FR00009443T8ED). Job **7963** returned successfully and expansion began
at 18:45:44 PDT. New partition UUID: 5806fe1c-c62b-4f87-86da-2222c18aac1d.

Verified eight ONLINE leaves in the same RAIDZ2, zero read/write/checksum errors,
and 16.3 TiB to redistribute. Initial ZFS estimate is not yet meaningful.
Previous expansion took 18h33 plus an 8h46 scrub; allow roughly a day or more
for expansion and verification, subject to live workload. Recovery stays separate.
No further candidate queued. Next check: job 7963, zpool status Media, then
candidate SMART counters. After completion require clean scrub and capacity/
application checks before considering any additional expansion.

2026-10-06 08:17 PDT check: second expansion 65.39%, 10.8/16.5 TiB at
232 MiB/s, estimated 7h09 remaining (about 15:25 PDT), before verification
scrub. All eight leaves ONLINE, zero ZFS errors. 471FR SMART passed, 41 C,
grown defects 110 and uncorrected read/write/verify 3/0/0 unchanged. Non-medium
counter increased from 393 to 396; cause unconfirmed. SAS PHY invalid DWORD,
disparity, synchronization-loss and reset-problem counters are all zero. Track
this small increase at next check; do not describe all SMART counters as stable.
Recovery ONLINE, zero errors, 1.13 TiB used and 2.38 TiB available. Overnight
rsync tasks 1/2/3 succeeded (9219/9259/9277), configuration checks pass, retention
guard succeeded at 06:00, cloud relay succeeded at 07:50:32 PDT. Old Media/backup
and histories remain intact; source retirement requires separately reviewed scope.

2026-10-07 final gate: job 7963 expansion finished October 6 14:47:42 after
20:01:58, 16.5 TiB redistributed. Scrub finished 23:29:22 after 8:41:40 with 0B
repaired and zero errors. All eight leaves ONLINE. After approved old-backup
retirement, Media has 10.9 TiB available. No further disk added: BTVM has zero
grown defects but non-medium errors reached 18,344,482 and continue increasing;
BK81 has 1,205 grown defects, historical read/write uncorrected 3/5, and an older
failed long test. Adding either is not appropriate with current evidence and
ample capacity. Further expansion requires a suitable qualified replacement or
separate resolution of the remaining drives' health concerns.

## Replacement SAS qualification — 2026-10-18

Jason requested testing the two newly installed SAS drives for possible Media
integration. Scope of this step: non-destructive qualification only; no formatting,
write-pattern tests, pool attach or push. Media remains the healthy eight-disk
RAIDZ2, with clean completed expansion scrub; Recovery and boot pool healthy.

| Serial | WWN | Model / size | Initial power-on hours | Grown defects | Uncorrected read/write | Non-medium |
|---|---|---|---:|---:|---|---:|
| 37H0A019FT2C1711 | 50000397a832e111 | HP MB4000JFDSN / 4,000,787,030,016 B | 69354:31 | 0 | 0/0 | 343 |
| 37H0A01HFT2C1711 | 50000397a832e289 | HP MB4000JFDSN / 4,000,787,030,016 B | 69354:39 | 0 | 0/0 | 294 |

Physical location reported by Jason on 2026-10-18: these two candidates occupy
**NAS expansion enclosure bays 3 and 6**. The individual serial-to-bay assignment
has not yet been confirmed; do not infer it from table order, Linux device letters
or controller PHY numbers. Both serials belong to this two-bay set. Confirm which
serial occupies each bay before recording an individual mapping or removing one.

Both report HPD1 firmware, 512-byte logical sectors, 7200 RPM, 2017 week 11
manufacture, 24 C and SMART health OK. Both active SAS ports initially show four
invalid DWORDs, four disparity errors, one synchronization loss, zero reset
problems; negotiated 12 Gbps. These are baseline observations, not established
active faults. No self-tests were logged. The detailed smartctl -x unsupported
statistics-page flag is not interpreted as a failed health test.

Verified by exact serial/WWN in disk.get_unused, no partitions or imported/exported
pool membership. Current Linux letters sdg and sdl are informational only; never
reuse letters without identity verification. Existing questionable BK81 and BTVM
remain separate unused disks and are not targets.

Extended background self-tests started 08:45:45 PDT on both drives. Firmware
estimates 537 minutes, expected completion around 17:42:45 PDT October 18.
They run on the drives independently of the chat. Baseline text/JSON and start
records are root-only under /mnt/Media/backup-ops/sas-qualification-20261018/.
Resume with smartctl -a/-x on the two WWN paths; do not restart an active test.
Require completed successful results and compare media, non-medium and PHY
counters against the preserved baseline. Reject/diagnose failures or growing
errors before any integration. Their approximately 7.9 years of power-on time
must remain part of the suitability assessment despite a SMART OK summary.

Next qualification gate after extended tests: host full-surface read and, before
final production integration, consider a destructive full write/read test after
confirming nothing needs preservation on these new drives. This turn does not
claim a pass, schedule an automatic pool addition, or authorize erasing unknown
contents. No production service, network, identity, NetBox/Beszel service object,
backup policy or speech output changed; existing TrueNAS health monitoring remains.

## 2026-10-18 — rejected disks reused for disposable lab storage

Qualification check at 15:47 PDT: both HP candidates still report background
long tests in progress, SMART health passed, zero grown defects and zero
uncorrected read/write errors. No completed test pass claimed. Expected finish
remains approximately 17:43 PDT; tests were not interrupted by Docker recovery.

At Jason’s request, BTVM and BK81 now form the separate `lab` mirror; they
remain excluded from production Media. See [lab scratch mirror](../Lab-Scratch-Mirror.md)
for exact identities, VLAN70 NFS access, limitations and validation. Both new
HP replacement disks continue their extended SMART qualification unchanged.
