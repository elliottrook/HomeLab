# October 30 booked qualification — pre-admission NO-GO

## Outcome

The 01:15 integrity job ran and completed at 01:22:47 PDT. The 03:10 launcher
ran on time, but its owner exited at 03:10:03 with sanitized
`SourceAdapterError`. This is **not** a restoration qualification or model
result. The launcher returning zero means only that it launched the owner.

The guardian has no start timestamp. The session directory contains only
`session.lock`: no admission, entry, adapter or session receipt exists.
Authoritative booking remains `reserved`, not claimed/complete. In the exact
source, archive admission precedes checkpoint, guardian, claim and drain.
Together these observations establish a pre-admission refusal before this
controller changed the AI stack. No retry or recovery effect was invoked.

Read-only current production checks: Agent (104), inference (110) and speech
(116) active/running; News ingest/digest timers active/waiting; Paperless and
EPUB timers active. Shared lease reports `ready`. These are availability
observations, not a complete model-health or recovery qualification.

## Schedule conflict found

Current TrueNAS task metadata, from the existing fixed observer:

| Task | Enabled schedule | Latest job | Started / finished epoch milliseconds |
|---|---|---|---|
| 1 guest pull | 01:00 | SUCCESS, arguments `[1]` | `1793347201000` / `1793347649000` |
| 2 Mac pull | 03:00 | SUCCESS, arguments `[2]` | `1793354402000` / `1793354403000` |
| 3 LXC110 mirror | **04:20** | SUCCESS, arguments `[3]` | `1793359201000` / `1793359581000` |

The accepted source contract requires task 3 at 02:00, after task 1 and before
task 2. A 04:20 mirror is also after the protected 04:15 boundary. The metadata
currently contradicts that contract. Do not silently weaken the gate, move
the protection boundary, change the task here or infer who changed it.

A read-only invocation of `backup_from_retained` against current metadata,
using the original 03:10 admission epoch, returned the mapped fixed error
`BACKUP_TASK_CHAIN_FAILED` (the source raises “TrueNAS backup tasks are not
all successful”). No archive scan or AI effect occurred. This reproduces the
current rejection, **not an immutable proof of the exact task snapshot at
03:10**; the owner log retained only the generic exception type. The schedule
conflict is independently actionable regardless of that provenance limitation.

## Exact host receipts

- `/var/lib/local-ai-lab/exclusive-integrity/b60-exclusive-20261030/terminal.json`:
  SHA-256 `4d4d6f05ca43d9d3c1fd27f7df44e67ce534e2a37e0a950d539d656084201f27`,
  schema `aster-exclusive-integrity-result.v1`, state complete,
  `ai_stack_effects=false`, `peer_receipt_reused=false`, finished epoch
  `1793348567`.
- `/var/lib/local-ai-lab/reservations/records/b60-exclusive-20261030.json`:
  SHA-256 `73dd305b37f707aa4389177c6ea896068c4f8befaae753e68ea3db29361a4328`,
  owner `b60-stream-a`, kind exclusive-stack, state reserved.
- Installed `/usr/local/libexec/local-ai-lease/exclusive-session/fixed_source_adapters.py`:
  SHA-256 `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9`,
  identical to the reviewed local source. No source or schedule was changed.

## Peer receipts and offline work

Fetched/read all four owner branches. No new replies. Exact commit/path/hash
receipts are unchanged from the [nightly reconciliation](nightly-reconciliation-20261030.md):
Adaptive `d88f8239b6771836c3e56c59229db81a8c18ddd6`, registry
`6fb0207fec5190e0c34ed3bc72ea38e128f06127`, booking owner
`5a9c3471398cfeecc0c6db35bfb264f87d8318f9`, published B60
`133ce06bdb16a4c1ab7d6e3308578900020a6bb6`. This does not imply peer reading.

Added three offline regression tests in implementation commit `9c1b1336a`:
expected synthetic chain fits; observed 04:20 metadata refuses admission even
after later SUCCESS; relabelling a late job does not repair it. No production
code changed. Published source patch:
`scripts/b60-inference/mirror-schedule-review-20261030/0001-Characterize-refusal-of-October-30-mirror-schedule-d.patch`,
SHA-256 `f83c3b9aaf2e59ea30173fcc789dfdee8ca68e3d77a5061e69f9cb47338a12b2`.
Applied independently to the exact replay checkout: all 126 Lab Hours tests
pass; all 107 focused B60 tests also pass. These are fake/offline tests, not
actual backup, guardian, model or restoration qualification.

## Owned response / next action

Platform owner: reconcile the actual task-3 schedule with the accepted 02:00
contract and protected 04:15 boundary; publish exact source/change authority
and fresh completion evidence. Do not repair it through this preparation-only
heartbeat. Preserve the failed booking/receipts and do not reuse or replay it.

B60: prepare a fresh future activation only after schedule reconciliation,
full same-cycle backup/mirror proof and reviewed current source pins. Keep
normal restoration, actual owner-loss and candidate/mount/resource gates
before 35B testing. Only October 30 had an activation; the remaining capacity
bookings are not automatically armed. No blanket reapproval or per-model
approval is missing. No new GPU/device failure was observed or retried.
