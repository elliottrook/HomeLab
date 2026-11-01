# November1 actual qualification — checkpointed, aborted before claim

## Outcome

**NO-GO before claim/drain/trial.** Backup integrity, full fresh admission and
verified entry checkpoint capture completed. The guardian did start; the claim
then refused because checkpointing took122 seconds while the claim gate allowed
only120. The session reconciled to `aborted-before-claim`; booking remained
reserved/unclaimed and common ownership markers/locks are clear. No model or
stack drain ran, and no live restoration qualification was earned.

Current read-only observations show Agent104, inference110 and Speech116
active/running, and both News114 timers active/waiting. These are unit states,
not authenticated model, speech or complete application-health probes. The
session's `production_restored=false` does not mean production was left broken:
the controller deliberately avoided restoring an old snapshot when no claim
or stack effects occurred. Guest protected checkpoint bytes remain source-local.

## Exact actual evidence on Proxmox

Paths below are under `/var/lib/local-ai-lab/`; SHA-256 covers actual bytes.

| Path | SHA-256 |
|---|---|
| `exclusive-integrity/b60-exclusive-20261101/terminal.json` | `4b075b7c72808ea4f654b2ca51afe0e5237768db1bf573694532977de967276f` |
| `exclusive-sessions/b60-exclusive-20261101/admission.json` | `e6f3de03f3d33d531a1b882a8f8fcaa2da683f11d4b2a72bdb046cdf9533fd50` |
| `exclusive-sessions/b60-exclusive-20261101/entry.json` | `768529fcfce247bfaafeca894e9c92a9fe76cebbe6257332e85194e5addeec32` |
| `exclusive-sessions/b60-exclusive-20261101/adapter.json` | `f0dfe69a8e4d8c6a9edacd36ebefaf548313ec2563df7892ee22420c416e4c20` |
| `exclusive-sessions/b60-exclusive-20261101/session.json` | `95da78b514693a1aae839ba0b76e3b8e19e3f652359f0cfe8858c4c7a13817ba` |
| `reservations/records/b60-exclusive-20261101.json` | `55ed0e33edf8c1db637cf6cc357d2250af2599aabb4f3b4fb4b0d898a3116d4f` |

Integrity ran01:15–01:23:53, terminal complete/AI-effects false, archive receipt
`retained-archive-integrity-sha256:4d2b66bcb3da5dc5dd8d6be03ea1c09f3bdd35c2a512a60d4a3963e70ed03512`.
Full admission observed epoch1793527801 (03:10:01 Vancouver UTC−07), whole job
verified and one accepted entry GPU holder. No admission-failure receipt exists.
Entry canonical hash equals its retained file hash and the session binding.
Adapter receipt contains no claim binding. Trial deadline1793528100 (03:15)
and restoration deadline1793530500 (03:55) stayed unchanged.

Owner ran03:10–03:12:02, exit1, fixed journal `no_go/BoundaryError`. Its specific
BoundaryError constant was not retained. Source-based diagnosis is decisive:
the matching reserved owner/kind passed identity, but the claim time exceeded
start+120. No need to infer a device, backup, authentication or unit failure.

Historical journal, not later transient-unit defaults:

- owner start event epoch-us1793527800866915;
- guardian start event epoch-us1793527922332864;
- owner `BoundaryError` result epoch-us1793527922356535;
- guardian `aborted-before-claim/recovery_attempted=false` result
  epoch-us1793527922409391.

**Correction to the provisional chat observation:** later `systemctl show`
returned an empty guardian start timestamp, but the historical journal proves
it started. An unloaded/garbage-collected transient unit's defaults are not
execution history. Do not repeat the initial “guardian never started” inference.
The journal proves clean pre-claim abort, not owner-loss restoration proof.

## Focused offline timing correction

Source commit `df09a99e204d5d8d68a62d924e4b986704d41894` adds a separate
checkpointed-exclusive claim path. The original fixed runner and default
exclusive claim APIs retain their120-second cutoff. The new path requires:

- admission within the existing first120 seconds;
- uninterrupted common host exclusion, with the epoch captured on acquisition
  and cleared on close/reacquire;
- verified checkpoint plus guardian before claim;
- claim before the **earlier** of the existing trial deadline or booking
  start+300 seconds, with at least900 seconds before the unchanged end;
- unchanged owner/kind/reserved state and exact entry/claimant binding.

The ledger independently rechecks these timing/identity constraints and records
admission epoch and claim cutoff. The adapter refuses already-expired capture
before even launching a guardian. No deadline, trial budget, task/scorer/policy
floor or useful-answer latency criterion is reset or relaxed. A late launch,
lost exclusion, exceeded cutoff or insufficient reserve still refuses.

Eight new boundary/combined fake-effect regressions reproduce the actual122-
second delay and prove claim/restore within the original window, while denying
late admission, an expired checkpoint, legacy late claims, lost/reacquired
exclusion and forged timing. Existing frozen diagnostic-updater tests now read
their exact frozen candidate bundle instead of incorrectly assuming every
future runtime development tree equals that old two-module candidate. The
updater's accepted map hashes/scope are unchanged; this fix is **not deployed**.

Validation:171 Lab Hours tests,10 installer tests and115 B60 tests pass without
skips against an independently replayed patch. Implementation/replay tree
`3f5c9b415400d4c8557982f5466f84ff4c382d83`.
Portable patch after source `d6e8aa6d8`:
`scripts/b60-inference/checkpoint-claim-window-20261101/0001-Bind-delayed-checkpoint-claim-to-timely-admission-an.patch`,
SHA-256 `10af066595532fa2c6ccbcfa6574954ec9cebfd2b4a1112e2604b1731e2ad970`.

## Persistence and exact next action

The previous focused checkout retained documents/objects but lost `.git/HEAD`,
`.git/config`, AGENTS and the standard. It was not reset, repaired or deleted.
Created a fresh disposable checkout using the healthy implementation object
store, then fetched all four authoritative Forgejo refs. Current working copy:
`/private/tmp/b60-nightly-20261101.MMJ32l/repo`, local branch
`codex/b60-nightly-reconcile-20261101`. Preserve the old directory as evidence.

Next operational work: review the new three-runtime-module closure and its
exact migration from the installed diagnostic closure, extend the bounded
source updater only for that reviewed transition, then prepare the next
unexpired reserved restore-only activation with fresh metadata/source pins.
Do not force the old two-module updater to accept different hashes or change
historical profiles. Re-prove backup clocks/chain, resources, owner release,
capture and unchanged restoration margin; never replay November1.

After normal qualification actually passes, separately qualify owner loss and
review candidate/mount/resource restoration before the ranked35B screen. The
recorded research ranking remains ordinary Qwen3.6-35B-A3B on accepted b11429,
reasoning genuinely on/speculation off; no model, download, benchmark, package,
driver, boot, credential or production mutation occurred in this nightly turn.
The programme remains active and27B+ useful-answer p50/p95 success unproved.

This is a **local-only** nightly commit; no push, new timer, deployment or
claimed background execution. The existing capacity record is not a future
activation. No repeat per-model approval is requested.

## Authoritative receipt refresh

All four refs fetched/read in the fresh checkout. Adaptive remains
`d88f8239b6771836c3e56c59229db81a8c18ddd6`, path
`docs/projects/AI Projects/evidence/SA3-expanded-source-quality-inactive-install-preflight-2026-10-29.md`,
SHA-256 `f4f72df5d792f17ce11ec87aae69e856f83865cac5b31b08146c65c32e8ac94a`.
Registry remains `6fb0207fec5190e0c34ed3bc72ea38e128f06127`, path
`docs/projects/Local-AI-Platform-Split.md`, SHA-256
`6bd3106078315a80046a6f917646410698df6a73f6e34c219b32272ce9f935d7`.
Owning booking ref remains `5a9c3471398cfeecc0c6db35bfb264f87d8318f9`, path
`services/local-ai-lease/ASTER-LAB-HOURS-RESERVATION-RUNBOOK.md`, SHA-256
`ed990e68fe04e4c238c192ff94fc81b275cf6cf622c0004e55afb26edda047ba`.
B60 received `b29df19f949052f23aef26efe47e838958ef9dd0`, path
`docs/projects/B60-Inference-Engineering/qualification-armed-20261101.md`,
SHA-256 `e3d2ab5a4eb374a7969786ea4674cf92e162f2f92e9e39cbac4f004aff3307f8`.
GitHub protection read-only ref matches that published B60 commit. Registry /
release records were reread; lifecycle link remains missing as previously
recorded. No new peer reply or reading is inferred, and no peer wait is claimed.
