# Pre-admission diagnostics candidate — October 30 10:31 preparation

## Outcome and limits

Implemented and tested an **offline, undeployed** diagnostic correction for
the October 30 pre-admission failure. The installed controller remains
unchanged. No new profile, timer, lease, model call or production change.
The existing observer still confirms enabled pulls at 01:00 / 02:00 / 03:00.

The failed owner's generic `SourceAdapterError` lost the exact failure class.
The candidate wraps only the backup-source invocation in FreshAdmission:

- Exact known fixed-source messages map to constant command, JSON, task-chain,
  archive-path or retained-integrity failure codes.
- Unknown exceptions produce `FRESH_BACKUP_SOURCE_UNCLASSIFIED`; no raw
  exception text, stderr, command output or private paths enter the receipt.
- A create-once `admission-failure.json` records schema, booking ID, observation
  epoch, `phase=backup-source`, fixed code and `admitted=false`.
- It raises a fixed SessionError, so the existing CLI emits that sanitized code
  rather than just the outer Python exception class. No error admits work or
  retries probes. A prior failure receipt is not overwritten for another try.

The proposed receipt is B60 diagnostic metadata, not an accepted peer admission
format, backup proof, policy grant, historical reconstruction or qualification.
Failures in other phases retain their existing behavior. This candidate cannot
recover the exact missing October 30 source snapshot retroactively.

## Exact source and validation

Implementation commit `4e982d95d`, on top of `9c1b1336a` and installed-source
base `1f9af79b4c08b0881ab334b7a72ef7efe8f41ad8`.

- Changed runtime source: `scripts/local-ai/lab_hours_exclusive_admission.py`,
  SHA-256 `442159a032700694c7d4e7f60bd7050f70d83cf0764ac3646724f6cb2c88b6ec`.
- Source patch:
  `scripts/b60-inference/admission-diagnostics-20261030/0001-Retain-content-free-pre-admission-backup-failure-dia.patch`,
  SHA-256 `43d5c63b277eab931d3fc5f11931487451b301afb9b7e127852845e30a50911e`.
- Applied patch in independent replay checkout. Its Git tree and implementation
  tree both equal `bd455b0bb2517de59e77d69589e49e95577dbfa8`.
- 129 Lab Hours tests pass in both checkouts. Three added tests verify a fixed
  task-chain error, redaction of unknown secret-like fixture text and real
  SessionStore create-once custody preventing overwrite/retry.
- 107 focused B60 tests pass with exact replay dependency supplied. All tests
  are synthetic/fake effects, not live checkpoint/restoration or GPU results.

## Authoritative receipt refresh

Fetched/read all four refs. No new peer response or format change:

| Ref | Commit | Path | SHA-256 |
|---|---|---|---|
| Adaptive | `d88f8239b6771836c3e56c59229db81a8c18ddd6` | `docs/projects/AI Projects/evidence/SA3-expanded-source-quality-inactive-install-preflight-2026-10-29.md` | `f4f72df5d792f17ce11ec87aae69e856f83865cac5b31b08146c65c32e8ac94a` |
| B60 | `321bb5ac0943e5c46be3a9708cbd6ac8d9a93a81` | `docs/projects/B60-Inference-Engineering/mirror-schedule-restored-20261030.md` | `759022a1139a2638daed8fc19e0cc5e67de3952b7aa7121449fea3685414aa21` |
| Platform registry | `6fb0207fec5190e0c34ed3bc72ea38e128f06127` | `docs/projects/Local-AI-Platform-Split.md` | `6bd3106078315a80046a6f917646410698df6a73f6e34c219b32272ce9f935d7` |
| Booking owner | `5a9c3471398cfeecc0c6db35bfb264f87d8318f9` | `services/local-ai-lease/ASTER-LAB-HOURS-RESERVATION-RUNBOOK.md` | `ed990e68fe04e4c238c192ff94fc81b275cf6cf622c0004e55afb26edda047ba` |

Branch publication is not evidence of receiving-agent reading/adoption.

## Durable next action

For a future activation, explicitly choose the reviewed old installed source
or this candidate. Deploying this candidate requires an exact new source bundle,
updated protected profile pins and verification of its closure; copying one
changed module over installed pins is invalid. Do not install or arm it from
this preparation-only heartbeat. Preserve the failed booking and its receipts.

Prepare the fresh future booking/profile/guest-plan and integrity clocks under
the operational runner workflow, without reusing October 30 or launching a
second owner. Actual same-cycle backup/mirror proof and normal restoration
qualification remain ahead of actual owner-loss and candidate/mount/resource
integration. Capacity bookings are not active experiments. No model permission
is missing and no live performance result is claimed.
