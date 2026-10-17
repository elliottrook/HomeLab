# F2 read-only archive observer — source-pinned release candidate

**Status: SOURCE ONLY; NO INSTALL, TIMER, ARCHIVE SCAN OR RUN APPROVAL.**
Owner: platform release. Stream A owns the F2 timing evidence. This card
implements the four gaps recorded in Stream A `b2fa7f9f`; it does not reuse
Jason's approval for the completed seven-path disabled installation.
**Immutable source checkpoint:** local branch `codex/aster-lease-compat` at
`339b554e` for all three proposed host files. The schedule-type regression
tests were strengthened after that checkpoint and are pinned by file hash
below. Verify the full source commit and test bytes again before an
installation review. Earlier common-exclusion commit `a38da489` is historical
background, not the release source for this card.

## Frozen source and current host boundary

| Role | Source SHA-256 | Proposed host target / current state |
|---|---|---|
| Manual `acquire --light` with common lock | `67ca223d03a4922603f570c6db87fed919879aedf3706e586b2684f7be84073c` | Replace `/usr/local/sbin/local-ai-lease` mode 0750, currently `f9744b4efd1340eca513e677af6b9eceda25e992db33e977b2f7f75adc101e23` |
| One-shot F2 guard | `d50ee2207bc4185db266ad01af540b9b719397dec3855ee579ee18f983a3535d` | Add `/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py` mode 0644; absent now |
| Fixed-source producer with observed TrueNAS schedule types | `5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb` | Replace `/usr/local/libexec/local-ai-lease/retained_archive_producer_candidate.py` mode 0644; currently `7e9b82a0c5216aad99ca1350849abb486a482586548c00ae6d7b6f309a1516c8` |
| Read-only observer | `f07071d3544fafd0579a4e360674664ec95dd32bd2c4114c3e073c849805e363` | Already installed, disabled, same hash |
| Whole-host and A1 `host_exclusion.py` | `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` each | Already installed at both roots, disabled candidate |
| Observer imports `retained_archive_integrity.py` and `fixed_source_adapters.py` | `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` and `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9` | Already installed at whole-host root with these read-only-verified hashes |

The new manual controller takes the same nonblocking lock over its entire
acquisition. The pinned observer holds that lock throughout the scan. The F2
guard checks the manual controller, producer, observer and its three runtime
imports by exact installed hash and root-owned file custody **before**
starting the observer child; the old manual executable therefore causes
NO-GO. This advisory lock does not exclude manual backup or TrueNAS pull
commands, so the first cycle requires a supervising operator and no manual
backup, pull or lease action during the bounded scan. The manual controller's
legacy lease-state schema is still unsuitable
for the later full-stop/watchdog drill. This change does not approve that
route for F6 or repair authority.

Live read-only `rsynctask.query` on October 16 showed task IDs 1/2/3 enabled
as JSON booleans `true`, with schedule hour/minute as strings: 1=`"1"`/`"0"`,
3=`"2"`/`"0"`, 2=`"3"`/`"0"`. The previously installed producer expects
numeric hour/minute, so it would reject this valid live state. The source
repair above pins the observed types and rejects numeric, boolean or padded
variants. This finding requires the producer replacement in this release;
the earlier two-path card is superseded. A current-cycle job success is still
unproven by this schedule query.
`test_retained_archive_producer_candidate.py` and
`test_f2_observer_runner_candidate.py` assert that boolean `enabled=true` and
string schedule values pass their respective admission checks, while numeric,
boolean-as-number and padded schedule variants fail. Recheck those assertions
on target Linux against the pinned source, without querying a live archive.

The guard accepts only an explicit `--read-only-authorized` one-shot argument.
It has no timer. It verifies the manual, observer, producer and imported
runtime file custody/hashes,
absence of either lease namespace and the retained receipt, a fixed start
window, 1-minute host load at most 4.0, no matching active Proxmox backup or
archive processes, and no running TrueNAS rsync task. It checks the exact
1/2/3 TrueNAS schedules. The pinned observer's fixed producer independently
rechecks same-cycle 00:30 Proxmox job completion, 01:00 task-1 success and
the exact current 104/110/116 volids/identity immediately before scanning.
Any check failure is NO-GO. The 4.0 load cutoff is a conservative candidate,
not a measured performance threshold; confirm it against the current host
baseline before a run, and skip if exceeded rather than raising it ad hoc.

The guard launches the observer in a separate process group, with an external
deadline at the earlier of 20 minutes from child start and 01:40 Vancouver.
On timeout it SIGKILLs the group, including a child `zstd`; the observer's
own sequential 120/900/120-second bounds and remaining-budget check remain
independent. The wrapper suppresses child stderr, accepts only the fixed
no-receipt result schema, rechecks that no receipt/lease appeared, and emits
only bounded archive identity/size/ctime/timing/exit fields. The source
observer substitutes a no-op `save` callback. It cannot produce F3/F4
trusted admission evidence. No automatic retry or same-cycle fallback exists.

## Required offline and target-Linux proof before installation review

The local `scripts/local-ai` suite passed **206 tests, two macOS root-custody
skips**, including 23 focused F2/manual/producer tests. Test file SHA-256 values:
manual-lock `32365ef687e3a26e632662df3c559944a06f7d794302976b81ab66f1d5bcaafd`;
F2 guard `67965725af9b64132dd804d13ddc50e836957c1daff97c78f84bc5bb46c73998`;
producer `e8fdc622532efe8e842d58440cbf1df69158fffa261c86f3a3c43845d30f0bfa`.
An independent reviewer
must inspect the guard, manual diff and exact dependency hashes before any
host change.

On Proxmox, stage these source/test files in a new root-only mode-0700
directory; do **not** replace the manual executable or start an archive yet.
With a private test `TMPDIR`, verify target-Linux imports and run the focused
manual-lock, producer and F2 guard tests, including the synthetic process-group child
heartbeat termination test. Also prove: manual acquire is denied while a
second process holds the common lock without any checkpoint/stop; the guard
rejects the old manual hash, bad mode, active lease, busy job and missed
window **before** child launch; no real observer, archive or service is
contacted by these tests. Verify no child remains after the termination
fixture. Record exact test counts, source hashes and service/timer baseline.
The target-Linux focused command, after copying only these six source/test
files into that private stage, is `PYTHONDONTWRITEBYTECODE=1
TMPDIR=<private-stage>/tmp PYTHONPATH=<private-stage>:/usr/local/libexec/local-ai-lease
python3 -m unittest test_manual_lease_archive_exclusion
test_retained_archive_producer_candidate test_f2_observer_runner_candidate`; `<private-stage>/tmp` must be root-owned
mode 0700. This command never invokes the real observer. The process-group
test spawns and kills only a synthetic sleeper and verifies its child stops
writing a disposable heartbeat. The command is a future test instruction,
not authorization to stage or run it now.

## Separate approvals and rollback

Only after those tests and independent review should Jason be asked to
approve a **bounded three-path disabled host change**: checkpoint and replace
the old manual executable and producer with the pinned files, add only the
new guard file, and verify imports, hashes, manual status, inactive timers,
unchanged backup/News schedules, no lease/receipt and running LXC104/110/116.
That installation must neither pass `--read-only-authorized` nor invoke the
observer. Preserve both old files root-only for rollback. If import,
test or postcheck fails with no scan/lease active, atomically restore only the
old executable and producer and remove only the new guard; reverify their old hashes, units,
schedules and services. If a scan/lease is active, do not swap code beneath
it; require operator reconciliation.

The **actual F2 read-only run needs a second, one-cycle approval** after a
fresh 00:30 backup and 01:00 TrueNAS pull. Before requesting it, the operator
must verify the exact current-cycle job/task result, 104/110/116 volids,
host load, no competing job or lease, installed hashes and matching schedules.
The operator must remain present for this first cycle and avoid manually
starting any backup, pull or lease while it runs. Proposed exact approval
wording: “Approve one supervised read-only F2 run for the verified [date]
Vancouver backup cycle between 01:10 and 01:19, using the pinned guard and
104/110/116 archives, with a hard stop by the earlier of 20 minutes or 01:40;
no receipt, lease, service stop, model call, timer enable or rerun. If any gate
fails, skip.” Afterward the operator must confirm no orphan scanner, new
receipt/lease or changed backup/News schedule and record only bounded result
metadata. Any failed or uncertain postcheck is NO-GO, not an F2 pass. This
sample text is not standing authorization.

The fixed 02:00 pull remains untouched and gets at least 20 minutes of
margin. A passed F2 timing result is not F3 trusted receipt release. F3,
F4–F10 and A1 retain their own gates. Do not represent this candidate as a
promise that tomorrow's scan or full-stop drill will run.
