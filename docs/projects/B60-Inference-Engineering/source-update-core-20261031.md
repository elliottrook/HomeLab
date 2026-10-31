# October31 preparation — exact diagnostic transition core

Implemented the next source-update component, not a production updater or
arming operation. This heartbeat remained offline apart from authoritative Git
coordination; it did not probe guests, acquire a lease, change production,
install packages, mount storage or call a model/GPU.

## Implemented boundary

`lab_hours_source_update.py` implements a durable transaction core for exactly
the already-recorded30-file old/candidate pin maps. It refuses any other map,
dependency set or changed-module set. Only the two reviewed host diagnostic
modules may change; the28 other dependencies and all guest helpers remain
fixed. The existing no-overwrite installer is not repurposed as an updater.

Before source replacement, the core requires strict adapter idle proof, exact
old observed pins, an immutable plan and a verified checkpoint digest. It
journals before replacements, verifies complete intermediate maps, validates
imports and records `installed-not-activated`, never model success. An import
failure rolls back once and retains the attempt; apply cannot silently retry.

A new object/process can use the durable plan/journal to roll back recognized
old/new mixed source maps after interruption between a replacement and its
next journal update. Unknown bytes, unrelated dependency drift, invalid plan /
journal, failed custody/checkpoint/import proofs or lost idle proof stop
without overwriting foreign state. Completed rollback is verified/idempotent.
Source bytes/configuration are not emitted in the journal.

There is **no production adapter, CLI, default target or scheduler**. A boolean
from a fake adapter is not authenticated ownership or source custody. The
eventual host adapter must hold the shared host exclusion continuously,
independently verify no active/recovering owner/guardian or armed future
old-profile consumer, validate root custody and exact checkpoint/candidate
bytes, replace source atomically and prove imports without executing models.
It must not mutate old profiles or historical receipts to conceal pin drift.

## Tests and explicit unqualified cases

Thirteen new tests use fake digest-map effects and real disposable journals:
reviewed map restriction; round-trip rollback/idempotence; denied/unproven idle;
unverified checkpoint; import-failure rollback without retry; simulated loss
after either replacement followed by a new core object; unknown peer bytes;
checkpoint corruption; plan tampering; idle rechecks/strict booleans; malformed
journal; unrelated initial drift; and retained partial journal writes.

These are not real host replacements or a real process-kill qualification.
In particular, the underlying store deliberately retains an uncertain
`update.json.next`. The added test proves that this blocks further effects,
not that every interrupted journal write auto-recovers. A reviewed resolution
of recognized partial journals remains required before live deployment; never
delete an uncertain `.next` merely to make a retry pass.

Validation:149 Lab Hours tests,10 dormant-installer tests and115 B60 tests pass
with no skips against the exact replay dependency root. Independent replay
and implementation tree equal `ba5d8b0218f8430e0e4531e65660aaca9dd3c403`.
Implementation commit `8b3e2c3247d248a54611714dcb2d150098588e69`.
The final replay test file was mechanically synchronized after adding the
partial-journal test; its committed tree equality was rechecked. No claim of
an independent human/security review is made.

Portable patch, after `a30322cb2` preflight and its pinned prior dependencies:
`scripts/b60-inference/source-update-core-20261031/0001-Implement-exact-diagnostic-source-transition-core-wi.patch`,
SHA-256 `7e571a02186c99febaf17d8a3765c0485ea0a4341fe3e4e30bb58ac385000bf6`.
Core SHA-256 `d19882d9a448981eb584afef0f891e0761ccccc91be9171eeddbdcd93cbb8872`.
The core is not imported into the existing30-file runtime closure and does not
change the already-built diagnostic candidate or any installed source pins.

## Next safe work and unchanged live gates

Implement and fault-test the bounded host adapter and partial-journal
resolution, then review the complete source-update transaction before any
deployment. The [exact old/new source receipt](source-update-preflight-20261031.md)
remains its dependency/custody contract. The [backup-clock mismatch](backup-clock-hazard-20261101.md)
also remains unresolved; this core cannot repair schedules or make a booking
admissible. Future activation must be separately source/date/booking bound.
Normal restoration and independent owner-loss qualification still precede
model/candidate/mount/resource trials. October30/31 may never be replayed.
No new human model approval, peer response, fake test or local commit supplies
those missing technical proofs. Programme remains active and incomplete.

## Exact authoritative peer receipt refresh

Fetched BOTH liaison branches and registry/booking refs; no new peer replies.
Read their actual owning records. SHA-256 below is over Git file bytes:

| Ref / commit | Path | SHA-256 |
|---|---|---|
| Adaptive / `d88f8239b6771836c3e56c59229db81a8c18ddd6` | `docs/projects/AI Projects/evidence/SA3-expanded-source-quality-inactive-install-preflight-2026-10-29.md` | `f4f72df5d792f17ce11ec87aae69e856f83865cac5b31b08146c65c32e8ac94a` |
| B60 / `eff3d424629a203185c34ae6d46cad0e88976fc4` | `docs/projects/B60-Inference-Engineering/arming-continuation-20261031.md` | `93bd4b74d5d0f67c2cc555d7b15c4c03ac3d0958360e26c59ea732c7e5797a58` |
| Registry / `6fb0207fec5190e0c34ed3bc72ea38e128f06127` | `docs/projects/Local-AI-Platform-Split.md` | `6bd3106078315a80046a6f917646410698df6a73f6e34c219b32272ce9f935d7` |
| Booking / `5a9c3471398cfeecc0c6db35bfb264f87d8318f9` | `services/local-ai-lease/ASTER-LAB-HOURS-RESERVATION-RUNBOOK.md` | `ed990e68fe04e4c238c192ff94fc81b275cf6cf622c0004e55afb26edda047ba` |

The received B60 record explicitly retires the delayed old arming task. No
peer acknowledgment is inferred from publication. Publish only the sanitized
coordination artifact under standing branch authority, and verify the GitHub
protection mirror read-only. No workflow, main or direct-GitHub push is allowed.
