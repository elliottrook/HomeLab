# AsterTV v3 M10 — operations readiness reconciliation

Date: 2026-11-05

Status: fail-closed audit installed; 5 named gaps remain

## Method

Read-only checks reconciled the fleet contract with sanitized live state and
the declared systems of record. No credential value, media title, household
state or camera content was read. No appliance, service, repository remote,
NetBox record, monitor, wiki or mirror was changed.

The checked authorities were:

- the committed fleet Doctor contracts and sanitized observations;
- Beszel's read-only system-name/status projection;
- a schema-restricted NetBox query for AsterTV device name, primary address and
  interface MAC only;
- the local 25-page HomeLab Wiki candidate and the live LXC 113 corpus;
- `homelab-reference` and the live collector source inventory;
- the established Forgejo/wiki restore evidence; and
- the manifested fleet/design skills and their forward-test record.

The resulting content-free snapshot is
`docs/projects/evidence/AsterTV-v3-M10-operations-observation-2026-11-05.json`.
`services/kodi/astertv-v3/m10/audit_operations.py` turns that snapshot into a
deterministic readiness result and fails closed when a required device or
authority is absent.

## Result

The audit correctly reports `attention` with 5 gaps:

- Doctor: Bedroom and Jen are clean; Family remains unobserved. Bedroom's 25
  declared payloads, 13 non-secret assertions and nine dependencies were
  independently checked. Two narrow drifts were checkpointed and corrected:
  an older release-guard executable and the mode on a content-identical remote
  apply helper. No credential value was read and Kodi was not restarted;
- Beszel: Bedroom and Jen are enrolled and report `up`; Family remains absent
  pending independent SSH identity verification;
- NetBox: Jen and Bedroom now have complete primary-address and MAC records;
  Family remains absent pending independent SSH identity/chassis verification;
- Wiki: all 25 AsterTV pages from `fc33f735c…5718351` are live on LXC 113;
- reviewed reference: `operations/astertv.md` is committed and synchronized at
  `62bb587a…a432`;
- derived mirror: the exact reviewed page is accepted as
  `astertv-operational-reference` and produces 12 provenance-linked entries;
  the deterministic mirror has 1,823 verified entries; and
- appliance recovery: Jen has an isolated rollback/reinstall rehearsal, while
  Bedroom and Family do not.

Forgejo and wiki infrastructure restore evidence already pass. Both Codex
skills are source-manifested and passed independent forward tests, so those
items are not falsely listed as gaps.

## Regression control

Three focused tests prove the current snapshot remains `attention`, a complete
synthetic observation passes, and an unknown schema is rejected. The main M10
gate now includes the readiness object. At clean commit
`746ade8f47fd8454c4926aec0d0f41a48de9e5b7`, two runs were byte-identical at
SHA-256 `8c2996f2c9ac570172a291ba7e8d574cf7b86f8e48e2fed9aebe16bb852fe901`:
51 test files passed and 93 candidate files scanned clean. That hash records
the initial 13-gap snapshot; the refreshed Jen observation reduces the current
audit to 12 without changing the fail-closed release result.

After committing the refreshed observation at
`15b662f8c8ff2e726638ebc45bd524ef38de2b47`, two further clean-tree runs were
byte-identical at SHA-256
`7da2a11199ba02b8403f3f1a5b8b6a6a1183d4d9d270d5e4dbef7fa3e62c80d5`.
They retain 51 passing test files, 93 clean candidate inputs and the current 12
explicit operational gaps.

The subsequent transaction-scoped Bedroom NetBox registration closed one more
gap, leaving 11. Its separate checkpoint and validation record is
`docs/projects/evidence/AsterTV-v3-M10-Bedroom-NetBox-2026-11-05.md`.

The Bedroom Doctor reconciliation closes the next gap, leaving 10. Its
checkpoint, exact content-free checks and rollback boundary are recorded in
`docs/projects/evidence/AsterTV-v3-M10-Bedroom-Doctor-2026-11-05.md`.

The host-bound Beszel overlay and two-device enrollment close the Bedroom and
Jen monitoring gaps, leaving 8. The hub checkpoint, private token custody,
exact binary pin and service validation are recorded in
`docs/projects/evidence/AsterTV-v3-M10-Beszel-clients-2026-11-05.md`.
Two clean-tree integrated runs immediately before the evidence-only amend
reported source commit `6ee63f2cbaff8addfd2692ffc6d2d11ecc4da352` and were byte-identical at SHA-256
`cd3368b5715fca6530c55ffb70d6a17f9d6f302c28e74efb3507444c2d4fadc7`;
54 test files pass and 93 candidate inputs remain free of credential/private-key
assignments.

The checkpointed knowledge publication closes the wiki, reviewed-reference and
derived-mirror gaps, leaving 5. All 25 AsterTV pages render through the existing
LXC 113 service; its 31 pre-existing sources and 62 generated files were
preserved before the new source was accepted. Collector verification passes for
32 sources, and mirror verification passes for all 1,823 entries at content
SHA-256 `8c9d4446…62ee5`. Corpus health has zero broken links, directory drift,
duplicates or unclassified sources. Its warning is limited to two pre-existing
stale Synology installation guides. Evidence is
`docs/projects/evidence/AsterTV-v3-M10-knowledge-publication-2026-11-05.md`.

## Next bounded work

Completed after the opening audit: Family identity was independently pinned,
then reconciled into NetBox, Beszel and Doctor. A failed first composition
transaction restored Family exactly and exposed the missing masked-unit runner
case; the corrected runner was regression-tested and the candidate accepted.
Bedroom and Family hash-bound bundles then passed disposable-root corrupt-file,
interrupted-install and accepted-state restore rehearsals. The final operations
observation passes with zero gaps. Detailed evidence is in
`docs/projects/evidence/AsterTV-v3-M10-Family-operations-and-restore-2026-11-05.md`.

Two final integrated runs were byte-identical at SHA-256
`70389670d184312b7f8fe3a2a84eee156e3b5d890f2146faa9363eb910563e59`.
All 56 local test files pass; 93 candidate inputs scan clean; all 15 pages and
127 focus controls conform; the screensaver double-build is identical; and the
operations gate remains `pass` with zero gaps. Connected playback,
performance and owner-walkthrough acceptance remain explicit later project
gates rather than being inferred from this repository result.
