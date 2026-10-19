# Owner update receipt and offline admission integration — 2026-10-19

Decision: substantial new owner work RECEIVED; model testing still BLOCKED.
This supersedes B60 statements that no newer owner integration is published.
Receipt does not imply live execution, new approval, private-corpus transfer,
qualified latency or completed programme.

## Exact receipts

Fetched authoritative main `7eabaadfef4853afc1de1f2202ab4e56a21f7481`:
new News TTS reconciliation is a separate project; B60 does not alter TTS.

Adaptive `a2cae9e3e9354f20308f356e1487a0c0bc8be665`:

| Path under `docs/projects/AI Projects/benchmarks/` | SHA-256 |
|---|---|
| `B60-coordination-interface-2026-10-12.md` | `3cbbb9559831dbbf826a85234d9fb2feb4c33fa2422bbfa246c3985ac3271b54` |
| `A1-full-path-admission-run-card-2026-10-13.md` | `d0152400c4fc5bbf446490189dea8acb27970cc598cb34185dfb8e3d46a85b55` |

Platform `442c0c00063d94daac9d0c54d5eb75d2cc8526dc`:

| Path under `services/local-ai-lease/` | SHA-256 |
|---|---|
| `F3-F4-INACTIVE-STAGE-RESULT-20261019.md` | `5571036819462e41cc7b2a46c5efb72a0eda3062936b8639f0962281666d5fd5` |
| `F2-EXACT-CYCLE-ACTIVATION-CARD-20261019.md` | `7a714f68147031da3f00a4376fe01c7e5cb4e50b2d64e10b78cf52c0b02d1727` |
| `FULL-DRAIN-INSTALLED-MANUAL-HELPER-READONLY-20261018.md` | `635883c6a60adefabfa6a143c60cdfc8fd3090a115d3e6badbb4e0bd54060ca5` |

These are Git-byte receipts, not independent live host measurements. B60's
prior publication at resume was `35430cd9f0e2bc1c0289aed09e40933aecc33e8c`.

## What is now resolved offline

Adaptive explicitly credits B60's `6104f422` recovery-trigger finding. Its
guard now rejects a trigger whose 15-minute restoration floor plus one-minute
lag floor reaches/exceeds 04:15, with elapsed UTC arithmetic for that bound.
Imported these exact two owner files into the focused B60 checkout:

- `scripts/aster-adaptive/full_path_admission.py` SHA-256
  `d849f395af73d906428c7f3c4b4bb303e7ad14d019c80b0bfc907099404c65f7`.
- `scripts/aster-adaptive/test_full_path_admission.py` SHA-256
  `52b86f50fc7849f7455490ef9aea7dfc64d81e8dae3f4e5e9b75b1651ab9ce0b`.

B60's former passing OPEN-gap reproduction now asserts the corrected owner
refusal. Do not continue describing that old offline bug as unfixed. These
minimum floors still are not measured host recovery/lag budgets.

Agreed: the whole-host/full-stop lease stops accepted LXC110 inference and
cannot run the Aster control. A1 requires its separate application-only
lease with the accepted backend active, isolated sidecar, no tools, exact
profile, private one-attempt journal and independent application restoration.
The separate full-drain three-request smoke is direct-backend only, not A1.

Agreed: platform and Adaptive now exchange `aster-a1-admission.v2` with both
`restore_start_epoch` and `restore_deadline_epoch`. The active platform boundary
refuses at/after the recovery trigger; the client checks a full batch fits
before trigger, rechecks each request and rejects identity/deadline drift.
Do not map the historical hard `watchdog_deadline_epoch` to a trigger field.
Reviewed source consistency does not authenticate a host or admit a model call.

## Live/deployment status received, not independently remeasured

- F0/F1 inactive installed-path compatibility is now reported complete.
- F2 has exactly dated host timers for **October 20 01:09 preparation and
  01:10 final gate**; daily timers stay disabled. The 01:42 chat observer must
  not start/retry the scan. No three-archive success result exists yet. B60
  must not duplicate that owner, probe during its scan or start another scan.
- F3 writer and F4 consumer are installed inactive, with pinned source,
  target-Linux tests and rollback receipts. Effects remain disabled; no trusted
  future-cycle receipt or lease follows merely from those installs.
- F5–F10 exact preflight, independently armed recovery, separately bounded
  live-drill approval, acquisition and exact restoration remain open. F2
  success cannot retroactively produce F4; F3 release must precede its fresh
  later backup cycle. A1 remains a separate subsequent-cycle lane.
- Platform now explicitly records live helper hash `67ca223d...`, matching
  B60's drift observation. This closes the missing acknowledgment, not the
  continuous-exclusion gap: directory flock is held only during manual
  acquisition. The recurring supervisor design holds it through restoration;
  design/synthetic tests do not prove its deployment or crash/hang recovery.

No blanket live approval is inferred from this receipt, and no new human
request is made before the owner supplies the exact reviewable missing gate.

## Validation and next integration

Focused B60 checkout: 81 inference tests and 11 updated owner-admission tests
pass (92 total, including B60's two peer checks and six margin tests in the
81; do not double-count them). A temporary source-only extraction of the exact
Adaptive commit separately passes 13 admitted-batch, three full-path capture
and six headless-client fake-transport tests (22). That complete peer extraction
supplies its own exact dependencies, unlike B60's older partial imports.
It opens no model connection and is not a live benchmark. The new batch/capture
files are reviewed/tested there, not silently imported into B60 or the full
read-only implementation checkout. No broad-suite or host test is claimed.

Next: consume the October 20 F2 terminal receipt without competing execution,
then the owner-released F3/fresh F4 and recovery evidence in dependency order.
In parallel review the exact source-bound application projection and full-path
profile/dependencies for A1; retain owner custody and original useful-answer
latency bar. Request source-specific measured restoration/lag evidence before
READY. Keep scratch NFS staging only an option, never private evidence custody.
No GPU/model/download/mount, lease, credential, service/timer, production or
policy mutation occurred. This scoped liaison publication is not peer
acknowledgment of B60's response and does not claim background execution.
