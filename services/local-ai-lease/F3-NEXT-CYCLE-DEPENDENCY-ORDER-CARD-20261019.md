# F3 next-cycle dependency and effect-order card

Status: approval-ready source plan; HOLD. This card records the only valid
dependency order for the next eligible backup cycle. It is not an authorization
to mutate the host, enable a unit, acquire a lease, stop a service, write a
receipt, call a model, change a timer, or push a remote.

## Decision and cycle boundary

The canonical tracker is serial: F3 is retained-receipt release; F4 is a
fresh trusted receipt for a later drill cycle; F5 is the 03:05 preflight; F6
arms independent recovery; F7 is Jason's human approval; F8 acquires the
full-stop lease and runs the bounded drill; F9 restores and releases it. F3
and F4 are evidence gates and must not stop services or acquire a lease.

The current F2 observer cannot be reused as F3 or F4 evidence. It writes no
trusted retained-integrity receipt and makes no lease admission claim. The
post-stop `/source-receipt.json` producer is also not an F4 producer because
it requires `state=leased` and observes quiescence after the stops. F4 instead
uses the new durable, non-effect pre-acquire receipt described below; the
full-stop controller consumes that receipt only after F6 and F7.

## Dependency-ordered run sequence

1. **Inactive release check.** Verify every staged file against the frozen
   hashes below, ownership/mode, disabled effect flags, and inactive/disabled
   systemd units. Confirm no archive-integrity receipt, pre-acquire receipt,
   post-stop source receipt, lease, lock, or application-B60 state exists. Any
   live, drifted, or ambiguous path is a NO-GO.
2. **F3 retained-receipt release.** In the approved 01:10–01:20 window,
   separately authorize the retained producer and invoke it once with effects
   enabled. It verifies the fixed backup chain and all three retained archives,
   then atomically writes `/var/lib/local-ai-lab/archive-integrity.json` by
   01:40. It never creates a lease or stops a service. No retry or overwrite
   follows an existing or uncertain receipt.
3. **F3 independent readback.** Rebind the archive receipt to current
   Proxmox/TrueNAS/Mac artifacts, unchanged archive identities, local date and
   freshness. Require root:root 0600 under a root:root 0700 parent and no
   temporary files. This closes F3 only after target-Linux custody/release
   evidence and rollback are recorded.
4. **F4 fresh pre-acquire receipt.** In the next eligible backup cycle, after
   task 1 and the F3 release, run the fixed retained adapter and 03:05 runtime
   observer without stopping anything. Pass the retained digest plus the
   healthy production observation through `prepare_pre_acquire`, then encode
   one root-owned `/var/lib/local-ai-lab/pre-acquire-receipt.json`. The
   envelope is schema-pinned, fresh for at most 15 minutes, lease-identity and
   digest bound, and explicitly records `consumers_isolated=false` and
   `scheduled_work_quiesced=false`. Independently read it back. This is F4;
   it is evidence only and does not grant permission to stop.
5. **F5 03:05 preflight.** Confirm the exact current-cycle schedules and
   completions, LXC110 mirror, three consumers still active, no competing
   lease/job, accepted Qwen3.5 9B Q4_K_M / llama.cpp b11429 SYCL-Level Zero / GPU
   / unit / authentication state, and News timer active/enabled and idle.
   The pre-acquire envelope must match this observation and backup digest.
6. **F6 recovery armed.** Verify the compatible watchdog and owner-liveness
   paths active/enabled, exact admission schema and constrained recovery
   executor. Do this before any stop. Loss of watchdog/owner is a NO-GO.
7. **F7 human approval.** Obtain approval for this exact bounded drill,
   target services, stop condition, 03:30 hard cutoff, 04:15 reconciliation
   reserve, and rollback. F7 is not implied by a schedule or an evidence file.
8. **F8 acquire and drill.** During 03:10–03:15, the controller reads and
   validates the F4 pre-acquire envelope, then persists the watchdog-compatible
   lock/state before stopping only LXC104/LXC110/LXC116. It performs repeated
   quiescence checks; News remains active. The post-stop source receipt may be
   produced exactly once for drill evidence, but it is not F4 and cannot be
   used to justify the earlier stop.
9. **F9 restore and reconcile.** Use only the watchdog/controller restore path.
   Restore previously active services, verify schedule/GPU/health checks, then
   release lease and lock only after complete restoration. If restoration is
   not complete by 03:30, retain lock/state and classify FAILED/UNKNOWN.

F3/F4/F5 can share a backup cycle only where F3 was already released before
that cycle; F5 must still be fresh. F6/F7/F8/F9 are serial and cannot be
compressed or inferred from earlier evidence. F6 recovery arming, F7 approval,
and A1/B60 benchmarking remain separate gates; competing exclusive work is
mutually exclusive with F8.

## Inactive staging versus live effects

The following are staged only while inactive/disabled: the retained producer
and integrity verifier; `pre_acquire_receipt.py`; `full_stop_acquire_candidate.py`,
its preflight, controller, lease contract, trusted observer, recovery executor,
and post-stop source-receipt modules; the receipt producer wrapper; and the
watchdog/recovery/heartbeat units. Staging includes hash, owner, mode,
dependency, and rollback verification. It does not enable a unit or create
state.

The following are live effects and require the applicable gate: enabling or
invoking the retained producer with effects and writing the F3 archive receipt;
writing the F4 pre-acquire evidence envelope (without a lease or stop);
arming watchdog/owner-liveness for F6; acquiring the host lock/lease and
stopping the three allowlisted services only after F7; writing the post-stop
source receipt; and invoking watchdog/controller restore and lease cleanup.
F3/F4 make no model request and stop no service. A partial stop, uncertain
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
| `scripts/local-ai/pre_acquire_receipt.py` | `7c70b6c8097ec9b5b9d2dd6e980f59a6b15ebd8397fbf5acbced98a2e7cc2170` |
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

## Canonical tracker semantics

The project tracker is authoritative: F3 is trusted retained-receipt release;
F4 is the fresh trusted pre-acquire receipt for the drill cycle; F5 is the
03:05 full preflight; F6 is independent recovery armed; F7 is human live-drill
approval; F8 is bounded full-stop acquisition/drill; F9 is exact recovery and
release; F10 is evidence close-out. No F3/F4 evidence may claim isolation or
authorize a stop. The post-stop source receipt is F8/F9 evidence, not F4.

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
