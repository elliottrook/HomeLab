# F3 next-cycle dependency and effect-order card

Status: approval-ready source plan; HOLD. This card records the only valid
dependency order for the next eligible backup cycle. It is not an authorization
to mutate the host, enable a unit, acquire a lease, stop a service, write a
receipt, call a model, change a timer, or push a remote.

## Decision and cycle boundary

The current F2 exact-cycle observer cannot be reused as F3 evidence. It writes
no trusted archive-integrity receipt and makes no lease admission claim. F3
therefore begins only in a fresh cycle in which the retained archive producer
has created and independently verified the current-cycle integrity receipt.

F3 source-receipt production and the full-stop lease must share that same
cycle: the lease binds the backup digest and the source receipt binds the
admitted lease. The retained producer and full-stop acquisition are separate
effects, but their evidence chain is one cycle. F2 observation may precede
them in that cycle, but it remains timing evidence only.

## Dependency-ordered run sequence

1. **Inactive release check.** Verify every staged file against the frozen
   hashes below, ownership/mode, disabled effect flags, and inactive/disabled
   systemd units. Confirm no archive-integrity receipt, source receipt, lease,
   lock, or application-B60 state exists. If any path is live, drifted, or
   ambiguous, stop before the cycle.
2. **F2 observation.** Run the approved read-only three-row observation and
   record a successful current-cycle result. It must not be relabeled as a
   trusted F3/F4 receipt.
3. **Retained archive effect.** In the approved 01:10–01:20 window, with the
   producer release separately authorized, invoke the retained producer once
   with its effect gate. It verifies the fixed backup chain and all three
   retained archives, then atomically writes
   `/var/lib/local-ai-lab/archive-integrity.json`. The hard deadline is 01:40.
   There is no retry and no overwrite of an existing or uncertain receipt.
4. **Independent archive readback.** Open the receipt through the pinned
   read-only verifier. Rebind it to the current Proxmox/TrueNAS/Mac artifacts,
   unchanged archive identities, local date, and freshness. Require root:root
   0600 under a root:root 0700 parent and no temporary files. Failure is NO-GO.
5. **Watchdog-compatible lease acquisition.** During 03:10–03:15, use only
   the approved full-stop controller path. Require the watchdog service and
   timer active/enabled, an exact matching archive backup digest, fresh trusted
   observations, and no conflicting lease. The controller persists its
   watchdog-compatible lock/state before stopping only the allowlisted
   LXC104/LXC110/LXC116 services. News remains active. Admit the lease only
   after the required repeated quiescence checks pass. The lease expires at
   the 03:30 hard cutoff.
6. **Exactly one F3 source receipt.** After `state=leased`,
   `consumers_isolated=true`, and `scheduled_work_quiesced=true`, invoke
   `/usr/local/sbin/local-ai-lease-produce-receipt` exactly once. It must bind
   the current lease ID/generation and backup digest and atomically write
   `/var/lib/local-ai-lab/source-receipt.json`. The one-attempt boundary
   refuses an existing destination; do not retry, delete, or overwrite after
   an uncertain result.
7. **Independent source readback.** Validate the exact boundary schema,
   lease identity/generation, backup digest, freshness (maximum 15 minutes),
   custody, and absence of temporary files. Capture only the content-free
   status projection; never log receipt contents.
8. **Restore and reconcile.** Use the existing watchdog/controller restore
   path, not ad-hoc service commands. Restore all services that were active,
   verify schedule/GPU/health checks, then release the lease and lock only on
   complete restore. Restore must finish by 03:30; otherwise retain the
   lock/state and classify the cycle FAILED/UNKNOWN for operator review.
   Record archive receipt, lease, source receipt, restore, and final
   postchecks independently.

The retained producer and source receipt can share one backup cycle. The F2
observation can share that cycle as read-only evidence. Full-stop acquisition,
source receipt, and restore must be one contiguous lease sequence. F6 recovery
arming/human drill and A1/B60 benchmarking remain separate gates and must not
be inferred from F3; any competing exclusive experiment is mutually exclusive
with this full-stop sequence.

## Inactive staging versus live effects

The following are staged only while inactive/disabled: the retained producer
and integrity verifier; `full_stop_acquire_candidate.py`, its preflight,
controller, lease contract, trusted observer, recovery executor, and source
receipt modules; the receipt producer wrapper; and the watchdog/recovery/
heartbeat units. Staging includes hash, owner, mode, dependency, and rollback
verification. It does not enable a unit or create state.

The following are live effects and require the cycle-specific approval: enabling
or invoking the retained producer with effects; writing the archive-integrity
receipt; acquiring the host lock/lease; stopping the three allowlisted
services; writing the source receipt; and invoking watchdog/controller restore
and lease cleanup. F3 itself makes no model request. A partial stop, uncertain
write, watchdog loss, receipt mismatch, expiry, or restore failure is a
fail-closed stop requiring review.

## Frozen release identities

All installed paths must match these SHA-256 values before a run. Any mismatch
is a NO-GO and requires a separately approved inactive replacement and a new
review of this card.

| Source path | SHA-256 |
|---|---|
| `scripts/local-ai/platform_receipt_producer.py` | `11d58e2147859ab981f3cc52e09e80af7b9200900f301777c8dc645698909be4` |
| `scripts/local-ai/source_receipt_boundary.py` | `4c981c94e33ff5bf11f50eec2b2f091a31fd8c3d32e20bed49ea3a3d8a3082ee` |
| `scripts/local-ai/fixed_source_adapters.py` | `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9` |
| `scripts/local-ai/admission_gate.py` | `8b6497565ba95e5ee8b21993b64f48d704f7a1298414f1ce1131adb969970e77` |
| `scripts/local-ai/backup_receipt_adapter.py` | `26a7741b484cee6159827fb2fd8f9fd62c5d305c267d04a3d0b6367f76b38a2f` |
| `scripts/local-ai/quiescence_receipt_adapter.py` | `effebc28fe862f152f67cc8a772e4daed055415a4e4e6d14b7e3428855f4175e` |
| `scripts/local-ai/source_receipts.py` | `35bbecdacec30226e5483e7214f7e318008c1e40d418b37861f000b0e8d701d4` |
| `scripts/local-ai/retained_archive_producer_candidate.py` | `5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb` |
| `scripts/local-ai/retained_archive_integrity.py` | `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` |
| `scripts/local-ai/host_exclusion.py` | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` |
| `scripts/local-ai/admission_state.py` | `af0854b9bd5f1157dba9027485ea7f91fdd88473f85c49ea850faa31f8181acc` |
| `services/local-ai-lease/local-ai-lease-produce-receipt` | `ebd3902f12e7045d480577eb7f88daaf8ac505c041b30d9b93b2d2d4cbc2bcc0` |
| `scripts/local-ai/full_stop_acquire_candidate.py` | `5859aba6cccb8f0eb8a971ccc4e3ff7054c1039482f0838c800ed7a10fc0f791` |
| `scripts/local-ai/full_stop_source_preflight.py` | `a656845321cbaf005ebd6e16945b55a026903d13fd32392f64d28cf65146b572` |
| `scripts/local-ai/lease_controller_candidate.py` | `f46509e49227cf7ba78ce662184722192059277202e7315616d12456f0385217` |
| `scripts/local-ai/lease_contract.py` | `420ce2ecc44bde3d17ad25218462618d150a4ec37c4a597067ebb45f8e2f780b` |
| `scripts/local-ai/trusted_observer.py` | `de6d2da913a1dab4f5e371739a6a3eada79b99d8e11e2d3b64cf0f825274074e` |
| `scripts/local-ai/lease_recovery_executor.py` | `d75ddfae4ccb3de4bd059aca75d41f4cdac6c60f4951d0ea6ab11a13b9f98e4d` |
| `services/local-ai-lease/local-ai-lease-recovery` | `46ddd8a031ecdeb2f227fadb18f5bc76ee9ad6042bf59d7056522c13ffe5b81c` |
| `services/local-ai-lease/local-ai-lease-watchdog.service` | `3041ed62efadcb1bcffe0c66e9c311933fc90c0cb101ea08f24b546fc9bc656d` |
| `services/local-ai-lease/local-ai-lease-watchdog.timer` | `9f09de46e3ee55d8f765e1f279d34632ea914c8c6506416f0455853ef538b744` |
| `services/local-ai-lease/local-ai-lease-owner-heartbeat.service` | `261ded21db209512be1b258613de4813063ae68d8057b475216e9af6e7911739` |
| `services/local-ai-lease/local-ai-lease-owner-heartbeat.timer` | `275e93ab7ab4a2ec5730feea8e8485126680837575f7d2a5756786a1e0a30b38` |

## Failure, rollback, and freshness rules

- Existing or uncertain archive-integrity or source-receipt paths are NO-GO;
  neither receipt may be overwritten. Preserve prior-good evidence for review.
- A failed archive scan writes no success receipt. A failed or uncertain
  source write is not retried. A partial stop triggers the controller's
  bounded restore attempt; uncertain journal, lock, or state is retained.
- Never swap staged controller/watchdog files after a lease or lock appears.
  Reconcile the installed identity and state first.
- Archive integrity is same-local-date and at most 10,800 seconds old. Source
  receipt freshness is at most 900 seconds. Lease state must remain unexpired
  and digest-bound throughout readback and restore.
- The retained producer window is 01:10–01:20 with hard deadline 01:40;
  full-stop acquisition is 03:10–03:15 with restore hard cutoff 03:30.

## Tracker semantics

F3 means one independently verified, lease-bound source receipt and complete
restore/reconciliation. F4 means a fresh next-cycle receipt/evidence chain; it
cannot be closed by the F2 observer or by this card. F5 means the live
full-stop/watchdog recovery path has completed its own approved drill. F6 means
recovery arming, human drill, and any A1/B60 benchmark gates; those remain
independent and mutually exclusive per cycle. These labels follow the existing
cards' gate semantics where the repository does not provide a single central
F4/F5/F6 registry.

## Offline evidence

The dependency suites passed 91 tests with 4 expected macOS root-custody skips:

```text
test_retained_archive_integrity
test_retained_archive_producer_candidate
test_fixed_source_adapters
test_source_receipt_boundary
test_full_stop_source_preflight
test_full_stop_acquire_candidate
test_lease_controller_candidate
test_lease_contract
test_lease_recovery_executor
test_lease_watchdog
test_trusted_observer
```

No host mutation, receipt production, lease acquisition, service stop, timer
change, model call, or remote operation was performed while preparing this
card.
