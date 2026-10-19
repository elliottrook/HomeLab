# F3 effect-enabled receipt run — future-cycle card

Status: source-only; HOLD. This card is executable only after a successful F2
three-row result, a separately approved retained archive receipt/lease sequence,
and a fresh authorization for this effect-enabled run. It does not authorize a
producer invocation, lease acquisition, service stop, model call, timer change,
or remote push.

## Cycle decision

F2 cannot directly authorize F3 in the October 20 cycle. The F2 observer uses
`save=lambda _receipt: None` and emits only a content-free three-row timing
projection with `admission_receipt_written=false`; it does not create the
trusted `/var/lib/local-ai-lab/archive-integrity.json` required by
`FixedSourceAdapters.backup_from_retained()`. F3 also requires a newly acquired
leased state and binds its backup digest to that lease.

Therefore the current design must wait for the next backup cycle. A same-day
run would be valid only if a separately authorized retained-archive producer
had already created and independently verified the current-cycle integrity
receipt and the full-stop lease controller had admitted a matching lease; F2
success alone is insufficient and must not be reused as that receipt.

## Exact 12-file release set

Before any run, every installed path must match these clean committed hashes.
The current live host now has the one-attempt boundary hash
`4c981c94e33ff5bf11f50eec2b2f091a31fd8c3d32e20bed49ea3a3d8a3082ee`. Any
mismatch is a NO-GO and requires a separately approved inactive replacement
first.

| Source path | Required SHA-256 | Target path/mode |
|---|---|---|
| `scripts/local-ai/platform_receipt_producer.py` | `11d58e2147859ab981f3cc52e09e80af7b9200900f301777c8dc645698909be4` | `/usr/local/libexec/local-ai-lease/platform_receipt_producer.py`, root:root 0644 |
| `scripts/local-ai/source_receipt_boundary.py` | `4c981c94e33ff5bf11f50eec2b2f091a31fd8c3d32e20bed49ea3a3d8a3082ee` | `/usr/local/libexec/local-ai-lease/source_receipt_boundary.py`, root:root 0644 |
| `scripts/local-ai/fixed_source_adapters.py` | `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9` | same, root:root 0644 |
| `scripts/local-ai/admission_gate.py` | `8b6497565ba95e5ee8b21993b64f48d704f7a1298414f1ce1131adb969970e77` | same, root:root 0644 |
| `scripts/local-ai/backup_receipt_adapter.py` | `26a7741b484cee6159827fb2fd8f9fd62c5d305c267d04a3d0b6367f76b38a2f` | same, root:root 0644 |
| `scripts/local-ai/quiescence_receipt_adapter.py` | `effebc28fe862f152f67cc8a772e4daed055415a4e4e6d14b7e3428855f4175e` | same, root:root 0644 |
| `scripts/local-ai/source_receipts.py` | `35bbecdacec30226e5483e7214f7e318008c1e40d418b37861f000b0e8d701d4` | same, root:root 0644 |
| `scripts/local-ai/retained_archive_producer_candidate.py` | `5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb` | same, root:root 0644; `EFFECTS_ENABLED=False` |
| `scripts/local-ai/retained_archive_integrity.py` | `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` | same, root:root 0644 |
| `scripts/local-ai/host_exclusion.py` | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` | same, root:root 0644 |
| `scripts/local-ai/admission_state.py` | `af0854b9bd5f1157dba9027485ea7f91fdd88473f85c49ea850faa31f8181acc` | same, root:root 0644 |
| `services/local-ai-lease/local-ai-lease-produce-receipt` | `ebd3902f12e7045d480577eb7f88daaf8ac505c041b30d9b93b2d2d4cbc2bcc0` | `/usr/local/sbin/local-ai-lease-produce-receipt`, root:root 0755 |

## Preconditions

1. Record a successful, current-cycle F2 three-row result and clean F2
   postcheck. Do not convert the F2 projection into a trusted receipt.
2. Confirm a separately produced current-cycle
   `/var/lib/local-ai-lab/archive-integrity.json`, root:root 0600 under a
   root:root 0700 parent, and independently verify it against current
   Proxmox artifacts and unchanged archive identities.
3. Confirm `/var/lib/local-ai-lab/lease.json` decodes as `state=leased`, with
   a matching `/var/lib/local-ai-lab/lease.lock`, current lease identity and
   generation, `consumers_isolated=true`, `scheduled_work_quiesced=true`, and
   `expires_minute > now_minute`.
4. Confirm the lease’s `backup_receipt` equals the retained adapter’s current
   digest, all fixed TrueNAS tasks and Mac/consumer quiescence evidence are
   current, and the 12 installed hashes match exactly.
5. Confirm `/var/lib/local-ai-lab/source-receipt.json` is absent. If it exists,
   is malformed, or is uncertain, stop for review; do not overwrite it.

## One attempt and receipt contract

Invoke the fixed entrypoint once, with no retry and no caller-selected path or
identity. The boundary now refuses any existing target receipt before creating
temporary bytes, writes atomically only after fresh evidence passes, and leaves
the prior-good receipt untouched on every pre-replacement failure.

The expected envelope is schema marker `aster-source-receipt-boundary-v1` with
exact top-level fields `boundary`, `lease_id`, `generation`,
`captured_epoch`, and `evidence`. Evidence must contain the fixed source,
lease-bound backup receipt, completed-minute, verified flag, exact consumer
set, News quiescence, and source-observed flag. Maximum receipt size is 8192
bytes; target custody is root:root 0600 in the root:root 0700 state directory.

Capture only the entrypoint’s content-free status, lease ID, and generation.
Never log or export receipt contents. On any non-zero result, timeout,
uncertain write, custody mismatch, source drift, or lease expiry, classify
NO-GO and do not retry.

## Independent readback and postconditions

After a successful return, independently open the receipt with the pinned
read-only boundary and validate the current lease ID/generation, current time,
freshness limit, exact evidence shape, and equality of the backup digest to
the lease. Verify the receipt path is root-owned 0600, the parent is root-owned
0700, no temporary files remain, and the lease remains valid.

Then verify no new lease/lock was created by the producer, no service stop or
model request occurred in this step, F2 timers/services are unchanged, the
retained producer remains effects-disabled, and the current-cycle source and
quiescence evidence is still valid. A failed readback leaves the receipt for
operator review and blocks all downstream use; do not delete or overwrite it.

F3 is complete only after the independently read-back receipt and all
postconditions are recorded. F4 requires a new backup cycle and a fresh
receipt.
