# F3 receipt writer — disabled-install card

Status: disabled install completed and verified; F3 remains OPEN. This card is
not authorization to invoke the producer, write a receipt, acquire a lease,
stop a service, call a model, activate a timer, or push remotely.

## Reviewed effect-enabled call graph

The future target release must pin the complete path, not just the boundary:

`local-ai-lease-produce-receipt` → `platform_receipt_producer.py` →
`source_receipt_boundary.py` → `FixedSourceAdapters` → backup, TrueNAS,
quiescence, retained-integrity, admission, and receipt adapters. The retained
archive producer remains a separately pinned disabled dependency with
`EFFECTS_ENABLED = False`; it must not be treated as an F3 receipt writer.

## Source and installed inventory

The source hashes below are the reviewed release set. The installed hashes are
the read-only 2026-10-19 Proxmox inventory. The boundary and backup adapter
are explicitly drifted and must be checkpointed before replacement; no other
file is silently assumed identical.

| Source path | Source SHA-256 | Installed path/hash | Mode |
|---|---|---|---|
| `scripts/local-ai/platform_receipt_producer.py` | `11d58e2147859ab981f3cc52e09e80af7b9200900f301777c8dc645698909be4` | `/usr/local/libexec/local-ai-lease/platform_receipt_producer.py` / `11d58e2147859ab981f3cc52e09e80af7b9200900f301777c8dc645698909be4` | root:root 0644 |
| `scripts/local-ai/source_receipt_boundary.py` | `033a21f798536dcc53f9ffcdf6589ff9725067976f4d146b2da142d3530fa784` | `/usr/local/libexec/local-ai-lease/source_receipt_boundary.py` / `8ed7b3250a531a656ff128a823318fb49d58d876ca3cbea74f85b23b820f7eab` | root:root 0644 |
| `scripts/local-ai/fixed_source_adapters.py` | `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9` | same / `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9` | root:root 0644 |
| `scripts/local-ai/admission_gate.py` | `8b6497565ba95e5ee8b21993b64f48d704f7a1298414f1ce1131adb969970e77` | same / `8b6497565ba95e5ee8b21993b64f48d704f7a1298414f1ce1131adb969970e77` | root:root 0644 |
| `scripts/local-ai/backup_receipt_adapter.py` | `26a7741b484cee6159827fb2fd8f9fd62c5d305c267d04a3d0b6367f76b38a2f` | same / `9bc07d567657deee07a757cb2518c078c37ef187d1922ff849d150313ec60a64` | root:root 0644 |
| `scripts/local-ai/quiescence_receipt_adapter.py` | `effebc28fe862f152f67cc8a772e4daed055415a4e4e6d14b7e3428855f4175e` | same / `effebc28fe862f152f67cc8a772e4daed055415a4e4e6d14b7e3428855f4175e` | root:root 0644 |
| `scripts/local-ai/source_receipts.py` | `35bbecdacec30226e5483e7214f7e318008c1e40d418b37861f000b0e8d701d4` | same / `35bbecdacec30226e5483e7214f7e318008c1e40d418b37861f000b0e8d701d4` | root:root 0644 |
| `scripts/local-ai/retained_archive_producer_candidate.py` | `5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb` | same / `5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb` | root:root 0644 |
| `scripts/local-ai/retained_archive_integrity.py` | `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` | same / `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` | root:root 0644 |
| `scripts/local-ai/host_exclusion.py` | `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` | same / `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` | root:root 0644 |
| `scripts/local-ai/admission_state.py` | `af0854b9bd5f1157dba9027485ea7f91fdd88473f85c49ea850faa31f8181acc` | same / `af0854b9bd5f1157dba9027485ea7f91fdd88473f85c49ea850faa31f8181acc` | root:root 0644 |
| `services/local-ai-lease/local-ai-lease-produce-receipt` | `ebd3902f12e7045d480577eb7f88daaf8ac505c041b30d9b93b2d2d4cbc2bcc0` | same / `ebd3902f12e7045d480577eb7f88daaf8ac505c041b30d9b93b2d2d4cbc2bcc0` | root:root 0755 |

The complete source set is 11 files. The two differing installed files must
not be replaced independently: checkpoint all 11 prior bytes, install the
whole set, and verify every post-install hash.

## Offline evidence

- Local focused F3 suites: 38 passed, 4 expected skips.
- Target-Linux focused suites: 46 passed, 0 skips.
- Local full `scripts/local-ai` suite: 335 passed, 8 expected skips.
- Target staging was temporary and removed; no installed file, receipt, lease,
  service, schedule, or model state changed.
- Boundary tests cover valid round trip, malformed/oversized input, symlink,
  hardlink, wrong mode, unsafe parent, replacement failure, and preservation
  of the prior receipt.

## Disabled installation and rollback plan

If separately authorized, verify every installed hash above, then checkpoint
all 11 target files under a fresh root:root 0700 directory such as
`/root/aster-f3-receipt-rollback-<commit>`, with saved files root:root 0600.
Install only the pinned set at the corresponding paths, preserving the
entrypoint mode 0755 and module modes 0644. Run target-Linux imports,
root-custody tests, and the full local suite from a private copy.

The producer must remain uncalled. Confirm before and after that the target
receipt path is unchanged, no lease or lock was created, all F2 timers and
services remain unchanged, the retained producer remains effects-disabled, and
no model or service stop occurred. Any failed precondition or postcheck rolls
back only these 11 files and verifies the restored hashes. Do not overwrite an
uncertain prior-good receipt.

F3 is not complete until a separately approved effect-enabled run produces a
current-cycle receipt after all source and quiescence checks pass, followed by
independent installed-path and rollback verification. F2 read-only output
cannot substitute for this receipt.

## Disabled-install receipt — 2026-10-19

The approved 11-file replacement completed using rollback checkpoint
`/root/aster-f3-receipt-rollback-9e04061e`, root:root 0700 with saved files
root:root 0600. The two drifted files were replaced only as part of the
complete pinned set; all 11 installed hashes match the source table. Modules
are root:root 0644 and `local-ai-lease-produce-receipt` is root:root 0755.

Target-Linux validation passed 46/46 focused tests, compilation, imports, and
custody checks. The rollback hashes match the pre-install inventory. The
receipt path, lease path, and lease lock remain absent; the F3 producer was
never invoked; the retained producer remains `EFFECTS_ENABLED = False`; F2
exact-cycle timers are active and both F2 services are inactive; F2 state is
empty; and temporary staging was removed. No daemon reload, schedule change,
service stop, model request, or receipt write occurred.
