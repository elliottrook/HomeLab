# F3 retained receipt — target-Linux preflight card

**State:** preparation only; HOLD. This card is not approval to install a file,
write a receipt, start a lease or run a full-stop drill. The October 17 F2
read-only timing check remains a separate, conditional operation.

## Observed installed state (2026-10-16, read-only Proxmox inventory)

| Host path | Owner/mode | Bytes | Installed SHA-256 |
| --- | --- | ---: | --- |
| `/usr/local/libexec/local-ai-lease/source_receipt_boundary.py` | root:root 0644 | 4430 | `8ed7b3250a531a656ff128a823318fb49d58d876ca3cbea74f85b23b820f7eab` |
| `/usr/local/libexec/local-ai-lease/platform_receipt_producer.py` | root:root 0644 | 1843 | `11d58e2147859ab981f3cc52e09e80af7b9200900f301777c8dc645698909be4` |
| `/usr/local/libexec/local-ai-lease/retained_archive_producer_candidate.py` | root:root 0644 | 9044 | `5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb` |

The `/usr/local/sbin/local-ai-lease-produce-receipt` entrypoint exists. The
expected archive-integrity and source-receipt files were absent when checked.
These are path/metadata observations, not evidence that the producer was run,
that the CLI is safe to invoke, or that backup admission has passed. Recheck
all identities immediately before any later host change; reject drift.

## Reviewed source candidate and limits

The combined writer/reader candidate is `codex/aster-lease-compat` commit
`a8d0f380`, `scripts/local-ai/source_receipt_boundary.py` SHA-256
`033a21f798536dcc53f9ffcdf6589ff9725067976f4d146b2da142d3530fa784`.
Its original test file SHA-256 at that commit is
`ced83f24f3fa136fabecf1bba2f06c946178f907d979fedc8778234da0fa888f`.
The platform owner independently integrated the reader change in local commit
`3170d2a0`; that is source review, not a host deployment. macOS offline tests
passed 209 with two root-only cases skipped in this branch. The owner reported
203 passed with two skipped in its broader checkout. Neither substitutes for
Linux root-custody proof. A subsequent source-only test addition at this
card's commit adds explicit opened-file symlink, hardlink, wrong-mode,
oversize and unsafe-parent cases; the new test file hash is
`9a6c4298e7adee9a72cc9a944294b4866155ce2ef081230de3907b37a5fe1108`.
The complete Mac suite then passed 207 tests with four expected root-only
skips (211 total); no target-Linux test was run by this card.

The candidate `produce_candidate_receipt()` obtains evidence from
`evidence_from_retained()` and binds its backup receipt to the acquired lease.
The observed installed source hash differs from this candidate, so an eventual
release must pin the *whole* target file and checkpoint the installed bytes.
The effect-enabled retained producer, its source inventory, and its actual
installed entrypoint remain separate review objects. A one-file replacement
does not close F3.

The source call graph is: `local-ai-lease-produce-receipt` →
`platform_receipt_producer.py` → `source_receipt_boundary.py` →
`fixed_source_adapters.py` → backup/retained-integrity and quiescence
adapters. The platform entrypoint requires a leased host state before it can
write. The installed platform producer matches the source hash above; the
installed boundary is the older hash. Read-only hashes of the other direct
admission files are compared below. All must be rechecked immediately before
an eventual installation because this inventory is a dated observation.

| Source file | Source SHA-256 | Installed comparison |
| --- | --- | --- |
| `platform_receipt_producer.py` | `11d58e2147859ab981f3cc52e09e80af7b9200900f301777c8dc645698909be4` | match observed |
| `source_receipt_boundary.py` | `033a21f798536dcc53f9ffcdf6589ff9725067976f4d146b2da142d3530fa784` | differs; old hash above |
| `fixed_source_adapters.py` | `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9` | match observed |
| `admission_gate.py` | `8b6497565ba95e5ee8b21993b64f48d704f7a1298414f1ce1131adb969970e77` | match observed |
| `backup_receipt_adapter.py` | `26a7741b484cee6159827fb2fd8f9fd62c5d305c267d04a3d0b6367f76b38a2f` | older installed `9bc07d567657deee07a757cb2518c078c37ef187d1922ff849d150313ec60a64` |
| `quiescence_receipt_adapter.py` | `effebc28fe862f152f67cc8a772e4daed055415a4e4e6d14b7e3428855f4175e` | match observed |
| `source_receipts.py` | `51052b26ee52ca0e2b4b561f6d5e9f303aadd20badfa9856bd15f551427629a4` | older installed `35bbecdacec30226e5483e7214f7e318008c1e40d418b37861f000b0e8d701d4` |
| `retained_archive_producer_candidate.py` | `5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb` | match observed; `EFFECTS_ENABLED = False` |

The two older installed hashes match earlier committed source, as recorded in
the staging and compatibility cards. The newer backup adapter adds a Mac
source/destination subset validator; the newer receipt composer adds an
`authenticated=False` parameter and passes that compatibility value to the
evidence object. Neither change is proven to affect the retained F3 path,
which currently calls the composer without that optional argument. This is a
source-level inference, not target-Linux proof. Pin the installed older
bytes for any F3 staging test; do not silently replace them as part of an
unrelated boundary update.

## Work that can be completed before the next backup cycle

1. Independently review the exact candidate and the `3170d2a0` integration;
   reconcile any changes to hashes before writing an installation card.
2. Freeze the complete effect-enabled F3 call graph, including producer,
   adapter, admission gate, receipt boundary and entrypoint. Record each
   source path/hash and the corresponding installed path/hash. Do not treat the
   disabled F2 observer as a trusted producer.
3. Prepare a synthetic target-Linux root test using a temporary root-owned
   mode-0700 directory, never `/var/lib/local-ai-lab`. Prove valid round trip,
   malformed/oversized/symlink/multilink/wrong-owner/wrong-mode/stale denial,
   and preservation of a prior good receipt on pre-replacement failure.
   Record only test counts and hashes, no receipt content.
4. Write a narrow host-change card with the exact file set, source and
   installed hashes, effect flags, checkpoints and rollback. Request its own
   bounded approval after F2 timing is measured and the complete source is
   reviewed. Keep timers and effects disabled during staging.

## Later release proof and rollback gate

An approved disabled stage would first verify every installed old hash,
checkpoint the exact old bytes, install only the pinned reviewed files,
verify new hashes and imports under target Linux, run the synthetic root
tests, and confirm every timer, service and effect flag remains off. Any
mismatch or failed test rolls back only the files changed by that stage and
requires hash verification of the restored bytes. No retry should overwrite
an uncertain receipt write.

F3 cannot be marked done until a separately approved effect-enabled release
uses the complete current-cycle source evidence, records a trusted root-owned
receipt only after all fixed source and archive checks pass, and has its
installed-path and rollback behavior independently verified. F4 then needs a
*new* backup cycle and a fresh receipt. F2's read-only scan cannot be reused
as that receipt. F6 recovery arming, human drill approval and A1 benchmarking
are later independent gates.
