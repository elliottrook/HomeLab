# F3/F4 conditional post-F2 sequence — approval-ready, inactive

Status: source and host reconciliation complete; HOLD. This card is not
authorization to create a receipt, acquire a lease, stop a service, call a
model, enable a unit, clear state, or push remotely.

## Current readiness and blockers

The October 21 F2 cycle is scheduled but has not run. F3/F4 may not inspect or
consume a future result until the exact terminal state exists. The current
Proxmox reconciliation found every reviewed F3/F4 path matching the frozen
source pins, root custody, and mode. The retained producer remains explicitly
`EFFECTS_ENABLED = False`; no F3 receipt writer is enabled or callable as a
trusted live effect. F4 has no active unit and its receipt path is absent.

The blockers are therefore deliberate and bounded:

1. F2 must finish the 2026-10-21 cycle with an exact complete result.
2. F3 needs its own effect-enabled release review and one-shot approval.
3. F4 needs a later, fresh runtime observation and a separate approval.

F3 and F4 must remain separate approvals. F3 writes durable retained evidence
after F2; F4 binds that digest to a fresh 03:05 healthy runtime observation.
Their distinct freshness, write paths, and failure consequences make one
combined live approval unsafe, even though this card records their dependency
order together.

## F2 success contract — prerequisite, not an implied action

Before any F3 action, perform read-only reconciliation and require all of the
following for `/var/lib/local-ai-lab/f2-scheduled/2026-10-21.json`:

- root-owned mode `0600`, regular file, bounded size, valid JSON and schema
  `aster-f2-scheduled.v1`;
- `cycle=2026-10-21`, `phase=final`, `state=complete`;
- `result.state=complete`, `result.date=2026_10_21`, and
  `result.admission_receipt_written=false`;
- exactly three archive rows, with VMIDs `104`, `110`, and `116`, current-cycle
  backup identities, positive size/ctime/timing fields, and `test_exit=0` for
  every row; no extra or duplicate row is accepted;
- the F2 terminal state is read twice and its bytes/digest remain unchanged;
- both October 21 F2 timers and all F2 services are inactive after the
  one-shot cleanup, and no observer, zstd, backup, lease, receipt, or model
  process is present.

Missing, malformed, late, replaced, partial, or uncertain state is NO-GO. The
October 20 terminal state is historical evidence and must not be cleared or
used for F3/F4.

## Conditional sequence

### F3 — retained archive-integrity receipt

After the F2 contract passes, obtain a separate bounded F3 approval. Reconcile
the complete installed 12-file F3 call graph and the rollback checkpoint,
then run the effect-enabled retained producer exactly once. It must bind the
same local cycle and all three F2 archive identities, rerun the fixed
read-only backup/TrueNAS/whole-job checks, and write exactly one root-owned
`0600` `/var/lib/local-ai-lab/archive-integrity.json` below a root-owned `0700`
directory. It must never acquire a lease, create a lock, stop production, or
call a model.

Independently reread the receipt, verify custody, schema, local date, archive
set, digest, freshness and unchanged F2 state. An existing or uncertain
receipt is NO-GO; no overwrite or retry is allowed. No automatic retry is
permitted. F3 success is not F4.

### F4 — fresh non-isolating pre-acquire envelope

Only after F3 succeeds and at the later 03:05 observation point, obtain a
separate F4 approval. Independently reread the F3 receipt and bind its digest
to a fresh `Observation` with the exact schedule set, production services
healthy, accepted GPU/model/backend/unit/auth identities verified, and
`consumers_isolated=false`, `scheduled_work_quiesced=false`. Encode exactly
one root-owned `0600` `/var/lib/local-ai-lab/pre-acquire-receipt.json`, then
independently reread and validate it within its 15-minute freshness limit.

F4 creates no lease, lock, isolation claim, service stop, model call, or
permission to start the drill. F5/F6/F7 remain later independent gates; no
drill, A1, or watchdog action follows automatically.

## Installed and rollback reconciliation

The following installed F3/F4 source paths were read-only reconciled on
2026-10-20; all hashes match the table below and all files are `root:root
0644`, except the receipt wrapper which is `root:root 0755`:

| Source path | SHA-256 |
|---|---|
| `scripts/local-ai/platform_receipt_producer.py` | `11d58e2147859ab981f3cc52e09e80af7b9200900f301777c8dc645698909be4` |
| `scripts/local-ai/source_receipt_boundary.py` | `4c981c94e33ff5bf11f50eec2b2f091a31fd8c3d32e20bed49ea3a3d8a3082ee` |
| `scripts/local-ai/fixed_source_adapters.py` | `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9` |
| `scripts/local-ai/admission_gate.py` | `8b6497565ba95e5ee8b21993b64f48d704f7a1298414f1ce1131adb969970e77` |
| `scripts/local-ai/backup_receipt_adapter.py` | `26a7741b484cee6159827fb2fd8f9fd62c5d305c267d04a3d0b6367f76b38a2f` |
| `scripts/local-ai/quiescence_receipt_adapter.py` | `effebc28fe862f152f67cc8a772e4daed055415a4e4e6d14b7e3428855f4175e` |
| `scripts/local-ai/source_receipts.py` | `35bbecdacec30226e5483e7214f7e318008c1e40d418b37861f000b0e8d701d4` |
| `scripts/local-ai/retained_archive_producer_candidate.py` | `5d98f6d9dde9797a92802060b151e9929a4d24849555679f76d65f32ed7caaaf` |
| `scripts/local-ai/retained_archive_integrity.py` | `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` |
| `scripts/local-ai/host_exclusion.py` | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` |
| `scripts/local-ai/admission_state.py` | `af0854b9bd5f1157dba9027485ea7f91fdd88473f85c49ea850faa31f8181acc` |
| `services/local-ai-lease/local-ai-lease-produce-receipt` | `ebd3902f12e7045d480577eb7f88daaf8ac505c041b30d9b93b2d2d4cbc2bcc0` |
| `scripts/local-ai/pre_acquire_receipt.py` | `7c70b6c8097ec9b5b9d2dd6e980f59a6b15ebd8397fbf5acbced98a2e7cc2170` |
| `scripts/local-ai/full_stop_source_preflight.py` | `a656845321cbaf005ebd6e16945b55a026903d13fd32392f64d28cf65146b572` |
| `scripts/local-ai/full_stop_acquire_candidate.py` | `fb59110ebf8236c67c40818f16f2e501503ebe2740e0eaf9672a5a09174b4ecb` |
| `scripts/local-ai/lease_contract.py` | `420ce2ecc44bde3d17ad25218462618d150a4ec37c4a597067ebb45f8e2f780b` |
| `scripts/local-ai/lease_watchdog.py` | `3146d292dd42a6a3f305b67cccf5518e7c0585c9c6de2e195d1a00686003d1fc` |
| `scripts/local-ai/trusted_observer.py` | `de6d2da913a1dab4f5e371739a6a3eada79b99d8e11e2d3b64cf0f825274074e` |
| `scripts/local-ai/lease_recovery_executor.py` | `d75ddfae4ccb3de4bd059aca75d41f4cdac6c60f4951d0ea6ab11a13b9f98e4d` |

F3 rollback checkpoints are present at `/root/aster-f3-receipt-rollback-9e04061e`
and `/root/aster-f3-boundary-rollback-421ac11b`. No new checkpoint, install,
receipt, or F4 state was created during this reconciliation.

## Explicit boundary

This card prepares the conditional sequence only. It does not invoke F3/F4,
write either receipt, acquire a lease, stop production, call a model, arm
watchdog/recovery, run a drill/A1, clear historical state, activate a timer,
or push remotely.
