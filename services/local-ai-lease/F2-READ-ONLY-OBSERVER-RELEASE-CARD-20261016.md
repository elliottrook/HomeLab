# F2 read-only archive observer — source-pinned release candidate

**Status: SOURCE ONLY; NO INSTALL, TIMER, ARCHIVE SCAN OR RUN APPROVAL.**
Owner: platform release. Stream A owns the F2 timing evidence. This card
implements the four gaps recorded in Stream A `b2fa7f9f`; it does not reuse
Jason's approval for the completed seven-path disabled installation.

## Frozen source and current host boundary

| Role | Source SHA-256 | Proposed host target / current state |
|---|---|---|
| Manual `acquire --light` with common lock | `67ca223d03a4922603f570c6db87fed919879aedf3706e586b2684f7be84073c` | Replace `/usr/local/sbin/local-ai-lease` mode 0750, currently `f9744b4efd1340eca513e677af6b9eceda25e992db33e977b2f7f75adc101e23` |
| One-shot F2 guard | `98bd2c7d88f90a02fac1617d143f0db67c8c8e8d8bb89409a882af4baf48b5bc` | Add `/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py` mode 0644; absent now |
| Read-only observer | `f07071d3544fafd0579a4e360674664ec95dd32bd2c4114c3e073c849805e363` | Already installed, disabled, same hash |
| Whole-host and A1 `host_exclusion.py` | `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` each | Already installed at both roots, disabled candidate |

The new manual controller takes the same nonblocking lock over its entire
acquisition. The F2 guard checks its exact new installed hash **before**
starting an observer child; the old manual executable therefore causes
NO-GO. The manual controller's legacy lease-state schema is still unsuitable
for the later full-stop/watchdog drill. This change does not approve that
route for F6 or repair authority.

The guard accepts only an explicit `--read-only-authorized` one-shot argument.
It has no timer. It verifies both manual and observer file custody/hashes,
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

The local `scripts/local-ai` suite passed **205 tests, two macOS root-custody
skips**, including fourteen focused F2/manual tests. Test file SHA-256 values:
manual-lock `32365ef687e3a26e632662df3c559944a06f7d794302976b81ab66f1d5bcaafd`;
F2 guard `22fd9705a50cfdd0a1f50629eaf58270b73d38ede9806eec4515b09cebdae2b8`.
An independent reviewer
must inspect the guard, manual diff and exact dependency hashes before any
host change.

On Proxmox, stage these source/test files in a new root-only mode-0700
directory; do **not** replace the manual executable or start an archive yet.
With a private test `TMPDIR`, verify target-Linux imports and run the focused
manual-lock and F2 guard tests, including the synthetic process-group child
heartbeat termination test. Also prove: manual acquire is denied while a
second process holds the common lock without any checkpoint/stop; the guard
rejects the old manual hash, bad mode, active lease, busy job and missed
window **before** child launch; no real observer, archive or service is
contacted by these tests. Verify no child remains after the termination
fixture. Record exact test counts, source hashes and service/timer baseline.
The target-Linux focused command, after copying only these four source/test
files into that private stage, is `PYTHONDONTWRITEBYTECODE=1
TMPDIR=<private-stage>/tmp PYTHONPATH=<private-stage>:/usr/local/libexec/local-ai-lease
python3 -m unittest test_manual_lease_archive_exclusion
test_f2_observer_runner_candidate`; `<private-stage>/tmp` must be root-owned
mode 0700. This command never invokes the real observer. The process-group
test spawns and kills only a synthetic sleeper and verifies its child stops
writing a disposable heartbeat. The command is a future test instruction,
not authorization to stage or run it now.

## Separate approvals and rollback

Only after those tests and independent review should Jason be asked to
approve a **bounded two-path disabled host change**: checkpoint and replace
the old manual executable with the pinned lock-compatible file, add only the
new guard file, and verify imports, hashes, manual status, inactive timers,
unchanged backup/News schedules, no lease/receipt and running LXC104/110/116.
That installation must neither pass `--read-only-authorized` nor invoke the
observer. Preserve the old executable root-only for rollback. If import,
test or postcheck fails with no scan/lease active, atomically restore only the
old executable and remove only the new guard; reverify its old hash, units,
schedules and services. If a scan/lease is active, do not swap code beneath
it; require operator reconciliation.

The **actual F2 read-only run needs a second, one-cycle approval** after a
fresh 00:30 backup and 01:00 TrueNAS pull. Proposed exact approval wording:
“Approve one read-only F2 run on the next verified current cycle between
01:10 and 01:19 Vancouver, using the pinned guard and 104/110/116 archives,
with a hard stop by the earlier of 20 minutes or 01:40; no receipt, lease,
service stop, model call, timer enable or rerun. If any gate fails, skip.”
The approval must identify the actual date/cycle and observed preflight;
this sample text is not standing authorization.

The fixed 02:00 pull remains untouched and gets at least 20 minutes of
margin. A passed F2 timing result is not F3 trusted receipt release. F3,
F4–F10 and A1 retain their own gates. Do not represent this candidate as a
promise that tomorrow's scan or full-stop drill will run.
