# Full-stop lease compatibility source packet

Status: **source candidate tested locally; live full-stop remains NO-GO**.
Owner: Stream A, with platform owner review before host installation. Date: 2026-10-15.
This candidate produces no speech. It does not change Aster's voice path.

## Problem and corrected sequence

The installed manual `local-ai-lease` writes an older `lease.json` shape, while
the installed watchdog/recovery executor decodes `AdmissionRecord`. Using them
together could leave the watchdog unable to recover. The former 03:05 source
check also tried a 300-second archive integrity scan; the 43.585 GB LXC110
archive had not finished at that limit. A successful task run or file presence
is not archive integrity proof.

The new source candidate separates the sequence:

1. At 01:10–01:20 Vancouver, after the exact current-cycle Proxmox 104/110/116
   artifacts, fixed 00:30 backup job configuration, same-cycle successful
   completion lines for those three guest backups, the same-cycle
   `pvescheduler` whole-job start and success records, and successful 01:00
   TrueNAS task 1 are observed, scan those
   three archives sequentially with low-I/O priority. The outer deadline is
   the earlier of 20 minutes after start and 01:40. A partial/late result
   cannot save a success receipt. The scan is **not scheduled or enabled**.
2. At 03:10–03:15, re-query the fixed artifact inventory, completed 01:00,
   02:00 and 03:00 TrueNAS tasks, and exact LXC110 mirror; re-stat the same
   archives against the root-owned retained receipt. Check the exact accepted
   SYCL/model/unit/auth runtime, schedules, control plane, owner liveness and
   independent watchdog timer. The proposed receipt explicitly says the three
   consumers are still running.
3. After persisting the watchdog-compatible state and lock, stop only the
   three allowlisted consumers. Record stop intent and outcome, observe stable
   isolation twice, then update the same schema to admitted. News timer stays
   enabled and active; its job must be idle. The post-stop receipt must retain
   the **same** backup digest as pre-acquire.
4. The watchdog decodes the same `AdmissionRecord`; it may only invoke the
   existing constrained restore path. An old state file without a lock now
   blocks acquisition rather than being overwritten.

The acquisition and scanner command-line paths are hard-disabled in this
revision. There is no live installer or enabled timer in this packet. The new
heartbeat timer is also an uninstalled candidate. Its file is only a bounded
liveness signal, not human authorization.

## Evidence and limits

The full local `scripts/local-ai` unittest discovery passed **173 tests, 2
root-custody tests skipped on macOS** on October 15. Coverage includes stale
archives, changed files, partial/over-deadline scans, failed TrueNAS task 1,
missing guest or whole-job completion and wrong Proxmox job configuration,
old-state overwrite rejection, pre/post isolation claims, fixed News timer
semantics, retained-digest continuity and controller-state → watchdog-schema
round trip. These are synthetic/offline tests, **not target-Linux or live
recovery evidence**. The 01:10 budget is a candidate based on a previously
observed warm 367.36-second LXC110 scan; fresh-cycle timing remains to be
measured. Whole-job proof is sourced from the fixed `pvescheduler` journal
window and tied to the three guest completion times. The journal format was
observed read-only on the current host; target-Linux testing must prove that
the exact query and bounded parser work on a new backup cycle.

## Required next gates

1. Review source and generate exact file hashes. Run the disabled candidate
   with target-Linux imports and verify 0700 root directory/0600 receipt
   custody. Confirm installed controller/watchdog paths and hashes; preserve
   the old controller for rollback only when no state or lock exists.
2. Dry-run the fixed journal, guest-log, task-1 and inventory gates on target
   Linux without saving a receipt. Do not infer whole-job success merely from
   guest log lines, artifact names or task 1 success.
3. Obtain separate approval for a disabled installation and verify no process,
   listener, timer activation, key, firewall or runtime change. Exercise
   source → receipt → controller → watchdog decode on target Linux without
   service effects, including timeout, stale, changed-archive and old-state
   cases. An enabled watchdog must never face the old controller's schema.
4. Freeze a revised single-cycle run card with observed timings, backup
   receipts, independent watchdog and exact restoration checks. Full-stop and
   A1 remain mutually exclusive in a cycle. Ask for the separate live-drill
   approval only after all prerequisites pass. Rollback restores the old
   controller only with no active/uncertain lease; otherwise retain lock and
   state for operator reconciliation.

No Proxmox service, B60 runtime, backup schedule, OpenBao control, Aster
Companion app or production credential was changed by this source packet.

## Source pins for review

These SHA-256 values identify source bytes only; they are not signatures or
deployment approval. All paths below are relative to the repository root.

| `scripts/local-ai/` source | SHA-256 |
|---|---|
| `retained_archive_integrity.py` | `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` |
| `retained_archive_producer_candidate.py` | `f3ae1a83f16e5b9c1bca571826029603e4c8d88fc6b529bfe79ffcd465288a3b` |
| `fixed_source_adapters.py` | `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9` |
| `full_stop_source_preflight.py` | `a656845321cbaf005ebd6e16945b55a026903d13fd32392f64d28cf65146b572` |
| `full_stop_acquire_candidate.py` | `6a7085036c9fb9558649c3114d055427c79649342bc5af37ecfb41b90d8fb386` |
| `lease_controller_candidate.py` | `e5d328937ea482de4b365e0be1869cabd3cd589eae86a2240b1d72bd5ae47226` |
| `lease_contract.py` | `420ce2ecc44bde3d17ad25218462618d150a4ec37c4a597067ebb45f8e2f780b` |
| `trusted_observer.py` | `de6d2da913a1dab4f5e371739a6a3eada79b99d8e11e2d3b64cf0f825274074e` |
| `source_receipt_boundary.py` | `8ed7b3250a531a656ff128a823318fb49d58d876ca3cbea74f85b23b820f7eab` |
| `platform_receipt_producer.py` | `11d58e2147859ab981f3cc52e09e80af7b9200900f301777c8dc645698909be4` |
| `lease_owner_heartbeat.py` | `533f3612613f8693d7debeff36e51e6ff42da6b816524946b636cc22b5b92690` |

The disabled heartbeat service and timer pins are
`261ded21db209512be1b258613de4813063ae68d8057b475216e9af6e7911739`
and `275e93ab7ab4a2ec5730feea8e8485126680837575f7d2a5756786a1e0a30b38`
respectively.
