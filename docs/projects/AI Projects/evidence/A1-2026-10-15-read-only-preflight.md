# October 15 read-only archive and A1 preflight

Status: **NO-GO for a full-stop drill and A1 model batch this cycle.** All
times below are Vancouver PDT. This is observation evidence, not a host
admission receipt, effect approval, model qualification, or proof of live
recovery. Stream A started no lease, stopped no service, and made no model call.

## Current backup cycle

The enabled all-guest Proxmox snapshot job is scheduled for 00:30. The
current `vzdump` task reported `OK` from 00:30:07 to 00:50:32. Its current-cycle
inventory returned these exact archives; `pvesm path` resolved each to the
corresponding file under `/mnt/backups/dump/`:

| VMID | Archive volid | Inventory bytes | Inventory ctime epoch | File ctime epoch |
|---|---|---:|---:|---:|
| 104 | `backups:backup/vzdump-lxc-104-2026_10_15-00_34_40.tar.zst` | 1,993,610,903 | 1792049680 | 1792049736 |
| 110 | `backups:backup/vzdump-lxc-110-2026_10_15-00_39_42.tar.zst` | 43,589,393,035 | 1792049982 | 1792050326 |
| 116 | `backups:backup/vzdump-lxc-116-2026_10_15-00_48_11.tar.zst` | 4,339,220,129 | 1792050491 | 1792050541 |

All three paths were regular, single-link files with sizes matching the
inventory. The distinction between inventory ctime and file ctime is retained
rather than silently normalized.

TrueNAS rsync tasks 1, 3 and 2 were enabled at 01:00, 02:00 and 03:00 and
reported `SUCCESS` for this cycle: task 1 at 01:00:02–01:05:47 (job 38258),
task 3 at 02:00:01–02:05:53 (job 38399), and task 2 at 03:00:01–03:00:02
(job 38540). A scheduler status is not archive integrity or a trusted
source-bound admission receipt.

## One-time cold archive timing check

At 01:14–01:15, `local-ai-lease status` was `ready`, there was no active
`vzdump` process, and host load was suitable. The one-time scanner started
before its 01:20 admission cutoff. It used `ionice -c3 nice -n 19 zstd -t
--quiet` sequentially, with a per-archive `timeout`.

| VMID | Start | Observed end | Elapsed | Outcome |
|---|---|---|---:|---|
| 104 | 01:15:17 | 01:15:34 | ~17 s | exit 0, integrity passed |
| 110 | 01:15:40 | unknown | unknown | final exit status unavailable after the chat turn was interrupted; **unverified** |
| 116 | not started | — | — | **unverified** |

At 03:10, no `zstd -t` process remained, but process absence cannot reconstruct
the lost 110 exit status. The 01:10 scanner was not restarted after its
one-time window. No current-cycle root-owned retained archive integrity
receipt directory existed on Proxmox at 03:10. The earlier source candidate
and a partial timing scan cannot satisfy the full-stop admission gate.

## A1 source and destination

The mode-0600 Mac source snapshot at
`/private/tmp/aster-a1-subset-source-20261014.json` still had SHA-256
`8f37f0000e52fc010250a426afde11d84a65746f1440bd210384e078c61fa1cf`.
It was captured before this cycle's task 2. A read-only destination scan on
TrueNAS finished at 03:10:42 after task 2 and found nine regular files,
57,692 bytes and canonical aggregate manifest SHA-256
`f05a49aa437af68369c5b2b0e97f613aed7f85c96d5de0cf7059448276f25e96`,
exactly matching the source snapshot. No private names, contents, per-file
hashes or credentials were printed or recorded. This proves observed subset
equality across the cycle; the observation helper is not an authenticated
source-bound producer or admission gate.

## Admission decision and continuation

The full-stop watchdog timer remained disabled/inactive, the host lease was
`ready`, and no retained current-cycle integrity receipt existed at the
03:10 preflight. The old-controller/watchdog schema mismatch has no verified
installed compatible acquisition-and-recovery path in this observation.
The full-stop drill is therefore **NO-GO**. A1 is also **NO-GO**: its
source-bound admission and live application lease/recovery are not proven,
and the project rules prohibit full-stop and A1 in the same backup cycle.
Do not infer either run from the clock or from successful backup schedules.

The platform owner was sent the content-free findings for its revised card.
The one-time 01:10 and 03:05 heartbeats were paused after these checks. The
separate 03:40 read-only postcheck remains active. The next safe work is
source/target integration and an independently verified producer receipt,
then a new bounded card and approval for a later cycle. Keep the obsolete
runner disabled.
