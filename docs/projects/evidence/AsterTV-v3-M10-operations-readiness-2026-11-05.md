# AsterTV v3 M10 — operations readiness reconciliation

Date: 2026-11-05

Status: fail-closed audit installed; 13 named gaps remain

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

The audit correctly reports `attention` with 13 gaps:

- Doctor: Bedroom and Family are unobserved; Jen has composition drift limited
  to three later accepted Remote-client payloads;
- Beszel: no AsterTV appliance is enrolled;
- NetBox: Jen has a primary address and MAC; Bedroom and Family do not yet have
  complete AsterTV identity records;
- Wiki: all 25 AsterTV pages exist in the validated local candidate at
  `fc33f735c…5718351`, but the live LXC 113 corpus has zero AsterTV pages;
- reviewed reference: no AsterTV operations page exists;
- derived mirror: no registered/provenance-linked AsterTV source exists; and
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
51 test files passed, 93 candidate files scanned clean, and the 13 gaps remained
explicit rather than being converted into a release pass.

## Next bounded work

The least disruptive sequence is: refresh Jen's sanitized observation; onboard
Bedroom and Family into NetBox and Doctor; add the three appliances to Beszel;
publish the already validated wiki candidate through the existing LXC 113
workflow; add the reviewed reference and derived mirror source; then rehearse
Bedroom and Family restore independently. Each remote write or appliance
rehearsal retains its normal authorization and recovery gate.
