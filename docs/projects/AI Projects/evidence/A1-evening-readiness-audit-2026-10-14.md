# A1 evening readiness audit — October 14 Vancouver

Status: **source-side timing opportunity preserved; live drill and full-path
benchmark remain blocked until independently admitted**.

The October 13 B60 checkpoint at `57c551e3` described an unfinished shared
lease, independent watchdog, recovery drill, benchmark admission and paused
lab schedule. It did not certify that lab time alone would complete them. On
October 14, Jason approved a narrower **disabled** helper upgrade: 24 pinned
Proxmox/LXC110 files were installed and verified, while both application
watchdog and heartbeat units remained disabled/inactive. A fresh read-only
host check found the whole-host lease `ready`, no application lease/prelease/
receipt, active Aster Agent, B60 llama.cpp and Speech, and inactive A1 sidecar.
This is installation progress, not live recovery evidence.

The current Proxmox backup inventory has October 14 local artifacts for LXC
104, 110 and 116 at 00:34:31, 00:39:31 and 00:48:37 respectively. TrueNAS
tasks 1/3/2 are enabled at 01:00/02:00/03:00 and report October 14 SUCCESS;
task 2 started 03:00:01 and finished 03:00:02. These are last-cycle facts,
not a prediction of tonight's completion or archive integrity.

The live full-stop recovery files match the proposed card's installed hashes:
`lease_recovery_executor.py` `d75ddfae…`, trusted observer `fdc64fc2…`,
recovery wrapper `46ddd8a0…`, watchdog service `3041ed62…` and timer
`9f09de46…`; the timer is disabled/inactive. `lease_watchdog_cli.py` is
source-only, not installed or invoked by that unit. Proxmox's enabled
all-guest backup job is scheduled 00:30. LXC114's News timer is enabled and
active with `OnCalendar=*-*-* 06,17:15:00 Etc/GMT+7`, i.e. 06:15/17:15 at
the project's fixed UTC-7 offset. These are pre-drill baselines only.

Read-only LXC110 checks reconfirmed the accepted runtime pins: unit SHA-256
`a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3`,
serving binary `0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5`,
and 5,627,044,256-byte Qwen3.5-9B Q4_K_M model
`cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13`.
The physical B60 BAR2 remains 32 GB. No authenticated generation or recovery
event was inferred from these hashes.

An [installed-controller integration check](Full-stop-lease-schema-mismatch-2026-10-14.md)
then found that the old manual `local-ai-lease acquire --light` writes a
different state schema from the independent watchdog's strict decoder. An
offline synthetic record in that installed controller's shape was rejected.
Thus the full-stop card is **not approval-ready** merely because its recovery
files are installed. A compatible source-bound acquire path and target-Linux
integration test are required before tonight's 03:10 effect window.

The owner-only A1 v2 backup subset is present on the Mac and in TrueNAS task
2's destination. Independent read-only scans of both locations found **nine
regular files, 57,692 bytes**, and the same canonical manifest SHA-256
`f05a49aa437af68369c5b2b0e97f613aed7f85c96d5de0cf7059448276f25e96`.
The canonical scan sorts relative paths and hashes each file, then hashes a
compact JSON array of `(relative path, byte count, content SHA-256)` tuples.
No filenames, contents or secrets were printed or committed. This equality
is a historical observation; it does not prove task-2 transfer for a new
cycle.

At epoch `1792035502`, before the next 03:00 task, Stream A captured a
mode-0600 content-free **source-only** snapshot at
`/private/tmp/aster-a1-subset-source-20261014.json`, file SHA-256
`8f37f0000e52fc010250a426afde11d84a65746f1440bd210384e078c61fa1cf`.
It records the nine-file count, byte total, manifest digest, scan time and
`source-snapshot-only` claim. It is not a signed, host-admitted producer
receipt. A destination snapshot after task 2 must independently match it.

The earlier 03:40 Stream A automation is a read-only post-drill check. It is
too late to *first* admit an A1 run that requires 35 minutes remaining before
the 04:15 restoration deadline. A separate one-time **03:05 read-only**
backup/source preflight is now active in this same chat. It must mark A1
NO-GO for this cycle if task 2 is unfinished by 03:10, the destination differs,
the fixed producer/transport is unreviewed, or live approval is missing.
Neither automation starts a lease, enables a timer, calls a model or schedules
the platform owner's proposed 03:10 recovery drill.

The current platform source contains a restricted forced-command candidate
and an explicit live-drill gate, but no trusted prelease producer deriving
the root-owned JSON from the fixed Proxmox/TrueNAS/Mac evidence. The existing
TrueNAS Mac observer claims only `tree-present-only`, which the A1 validator
correctly rejects. Therefore tonight's window is **conditional**, not READY.
The fixed producer, current-cycle result, exact restoration baseline, an
approved effect card and independent watchdog drill must precede any A1
benchmark. A full-stop drill and an application-only A1 run use different
lease scopes; the full-stop lease stops the B60 backend and cannot carry the
benchmark.

**Platform-owner scope decision later on October 14:** The revised
`FULL-STOP-RECOVERY-DRILL-RUN-CARD.md` at `6c68df2c` declares the full-stop
drill and application-only A1 benchmark mutually exclusive in one backup
cycle **even if full-stop recovery succeeds**. Stream A's 03:05 automation
was updated accordingly. Tonight can prove the full-stop recovery path if
approved and all gates pass, or prepare A1 source evidence for the next cycle;
it cannot honestly complete both live tests in one window under this rule.
