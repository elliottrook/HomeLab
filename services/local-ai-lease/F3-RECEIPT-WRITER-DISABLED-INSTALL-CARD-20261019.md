# F3 receipt writer — disabled-install card

Status: disabled install reconciled and verified; F3 remains OPEN pending a
separate effect-enabled authorization. This card is not authorization to invoke
the producer, write a receipt, acquire a lease, stop a service, call a model,
activate a timer, or push remotely.

## Reviewed effect-enabled call graph

The future target release must pin the complete path, not just the boundary:

`local-ai-lease-produce-receipt` → `platform_receipt_producer.py` →
`source_receipt_boundary.py` → `FixedSourceAdapters` → backup, TrueNAS,
quiescence, retained-integrity, admission, and receipt adapters. The retained
archive producer remains a separately pinned disabled dependency with
`EFFECTS_ENABLED = False`; it must not be treated as an F3 receipt writer.

## Source and installed inventory

The table below is the reconciled live 12-file set. The installed hashes are
the read-only 2026-10-19 Proxmox inventory after the inactive install. The
boundary and backup adapter were explicitly drifted and replaced. The
`source_receipts.py` variant is explicitly committed as the F3 release source;
the clean source tree now matches the live installed set exactly.

| Source path | Source SHA-256 | Installed path/hash | Mode |
|---|---|---|---|
| `scripts/local-ai/platform_receipt_producer.py` | `11d58e2147859ab981f3cc52e09e80af7b9200900f301777c8dc645698909be4` | `/usr/local/libexec/local-ai-lease/platform_receipt_producer.py` / `11d58e2147859ab981f3cc52e09e80af7b9200900f301777c8dc645698909be4` | root:root 0644 |
| `scripts/local-ai/source_receipt_boundary.py` | `4c981c94e33ff5bf11f50eec2b2f091a31fd8c3d32e20bed49ea3a3d8a3082ee` | `/usr/local/libexec/local-ai-lease/source_receipt_boundary.py` / `4c981c94e33ff5bf11f50eec2b2f091a31fd8c3d32e20bed49ea3a3d8a3082ee` | root:root 0644 |
| `scripts/local-ai/fixed_source_adapters.py` | `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9` | same / `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9` | root:root 0644 |
| `scripts/local-ai/admission_gate.py` | `8b6497565ba95e5ee8b21993b64f48d704f7a1298414f1ce1131adb969970e77` | same / `8b6497565ba95e5ee8b21993b64f48d704f7a1298414f1ce1131adb969970e77` | root:root 0644 |
| `scripts/local-ai/backup_receipt_adapter.py` | `26a7741b484cee6159827fb2fd8f9fd62c5d305c267d04a3d0b6367f76b38a2f` | same / `9bc07d567657deee07a757cb2518c078c37ef187d1922ff849d150313ec60a64` | root:root 0644 |
| `scripts/local-ai/quiescence_receipt_adapter.py` | `effebc28fe862f152f67cc8a772e4daed055415a4e4e6d14b7e3428855f4175e` | same / `effebc28fe862f152f67cc8a772e4daed055415a4e4e6d14b7e3428855f4175e` | root:root 0644 |
| `scripts/local-ai/source_receipts.py` | `35bbecdacec30226e5483e7214f7e318008c1e40d418b37861f000b0e8d701d4` | same / `35bbecdacec30226e5483e7214f7e318008c1e40d418b37861f000b0e8d701d4` | root:root 0644 |
| `scripts/local-ai/retained_archive_producer_candidate.py` | `5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb` | same / `5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb` | root:root 0644 |
| `scripts/local-ai/retained_archive_integrity.py` | `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` | same / `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` | root:root 0644 |
| `scripts/local-ai/host_exclusion.py` | `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` | same / `b39680d55d7203fe4e4a5f0ccbb7a3a708cc01616b02fd93d665585e467e3b61` | root:root 0644 |
| `scripts/local-ai/admission_state.py` | `af0854b9bd5f1157dba9027485ea7f91fdd88473f85c49ea850faa31f8181acc` | same / `af0854b9bd5f1157dba9027485ea7f91fdd88473f85c49ea850faa31f8181acc` | root:root 0644 |
| `services/local-ai-lease/local-ai-lease-produce-receipt` | `ebd3902f12e7045d480577eb7f88daaf8ac505c041b30d9b93b2d2d4cbc2bcc0` | same / `ebd3902f12e7045d480577eb7f88daaf8ac505c041b30d9b93b2d2d4cbc2bcc0` | root:root 0755 |

The complete installed set is 12 files: 11 modules plus the entrypoint. The
`host_exclusion.py` version is required because it documents the installed
manual-helper participation; its code path is otherwise unchanged. The
`source_receipts.py` release intentionally excludes the later optional `authenticated`
compatibility parameter because the current F3 call graph never passes it;
retaining it would change the reviewed artifact without adding evidence. The
two differing installed files must not be replaced independently: checkpoint
all 12 prior bytes, install the whole set, and verify every post-install hash.

## Offline evidence

- Local focused F3 suites: 38 passed, 4 expected skips.
- Target-Linux focused suites: 46 passed, 0 skips.
- Local full `scripts/local-ai` suite: 336 passed, 8 expected skips.
- Target staging was temporary and removed; no installed file, receipt, lease,
  service, schedule, or model state changed.
- Boundary tests cover valid round trip, malformed/oversized input, symlink,
  hardlink, wrong mode, unsafe parent, replacement failure, and preservation
  of the prior receipt.

## Disabled installation and rollback plan

If separately authorized, verify every installed hash above, then checkpoint
all 12 target files under a fresh root:root 0700 directory such as
`/root/aster-f3-receipt-rollback-<commit>`, with saved files root:root 0600.
Install only the pinned set at the corresponding paths, preserving the
entrypoint mode 0755 and module modes 0644. Run target-Linux imports,
root-custody tests, and the full local suite from a private copy.

The producer must remain uncalled. Confirm before and after that the target
receipt path is unchanged, no lease or lock was created, all F2 timers and
services remain unchanged, the retained producer remains effects-disabled, and
no model or service stop occurred. Any failed precondition or postcheck rolls
back only these 12 files and verifies the restored hashes. Do not overwrite an
uncertain prior-good receipt.

F3 is not complete until a separately approved effect-enabled run produces a
current-cycle receipt after all source and quiescence checks pass, followed by
independent installed-path and rollback verification. F2 read-only output
cannot substitute for this receipt.

## Disabled-install receipt — 2026-10-19

The approved 12-file replacement completed using rollback checkpoint
`/root/aster-f3-receipt-rollback-9e04061e`, root:root 0700 with saved files
root:root 0600. The two drifted files were replaced only as part of the
complete pinned set; all 12 installed hashes match the reconciled live table. Modules
are root:root 0644 and `local-ai-lease-produce-receipt` is root:root 0755.

Target-Linux validation passed 46/46 focused tests, compilation, imports, and
custody checks against both the staged source set and the actual installed
directory. The rollback hashes match the pre-install inventory. The
receipt path, lease path, and lease lock remain absent; the F3 producer was
never invoked; the retained producer remains `EFFECTS_ENABLED = False`; F2
exact-cycle timers are active and both F2 services are inactive; F2 state is
empty; and temporary staging was removed. No daemon reload, schedule change,
service stop, model request, or receipt write occurred.

The later single-file safeguard replacement completed from commit `421ac11b`
using `/root/aster-f3-boundary-rollback-421ac11b`. The prior boundary hash was
`033a21f...`; the installed one-attempt boundary is now `4c981c94...`,
root:root 0644. Its rollback file is root:root 0600. Target-Linux focused
tests passed 46/46 again, all 12 clean source hashes match the live install,
and no receipt, lease, lock, service, timer, or model state changed.

## Reconciliation result

The provenance gap is closed by commit `625505ed`, which pins the exact live
`source_receipts.py` bytes. The 46-test installed-path suite was rerun after
that commit, and all 12 clean committed source hashes now equal the live
installed hashes. F3 remains operationally closed until a separately approved
effect-enabled receipt run; no producer invocation is implied by this card.
