# M4 storage lifecycle and independent review design

Status: proposed operational design, 2026-09-25. Owner: Jason. Implemented scope is
local synthetic evidence and offline verification only. This document does not
approve a deployment, private-data collection, new identity or promotion. It
supports the [canonical programme](Aster-Adaptive-Computing.md); it is not a new queue.

## Data boundary and retention

| Record class | Current location and lifecycle | Proposed operational treatment |
|---|---|---|
| Authored synthetic fixtures, code, sanitized manifests and results | Repository history; retained as reproducibility evidence, including negative results | Continue reviewed publication through Forgejo and its GitHub mirror; never treat either as private-data storage |
| Disposable SQLite ledger and restore copy | Per-run temporary directory; normal exit and handled failures remove it | No scheduled collector or long-lived database exists; unexpected process/host termination may leave temporary files for explicit inspection and cleanup |
| Human decision and accepted checkpoint | No independent decision/custody established yet | Reviewer-controlled decision record identifying exact artifact commit, input digest, ledger head, evaluator version, decision and unresolved limits; writer cannot update or delete it |
| Real prompts, private source output, identifiers, embeddings, credentials or approval material | Prohibited from current datasets and Git | No collection until separate fields/purpose/consent/access/retention/backup/deletion design is approved; no default retention period is silently assigned |

Only bounded synthetic references and approved metadata belong in the current store.
A schema flag is a declaration, not a detector of private text. Review content before
publication. If unexpected private material appears, stop ingestion/publication and
isolate the artifact; do not assume deleting a working-tree file erases Git history,
mirrors or backups. Coordinate any remote/history cleanup as a separate bounded
operation. No automatic deletion job or destructive cleanup is authorized here.

Git retains historical synthetic evidence until an explicit repository lifecycle
change. Disposable measurement databases are not operational recovery dependencies.
A future live pilot must set a numeric retention period and align deletion across
active storage, replicas and backups before collecting its first real event.

## Ownership and authority

| Role | Allowed responsibility | Authority boundary |
|---|---|---|
| Proposer/experiment writer | Draft immutable protocol, run approved fixtures, append measurements, export candidates | Cannot approve itself, change evaluator/permissions, publish without push approval, or promote a runtime |
| Evaluator | Apply a reviewer-accepted, pinned implementation to frozen inputs; produce derived totals | No credentials, private readers, network requests, deployment path or ability to alter its acceptance rule mid-experiment |
| Independent reviewer | Inspect protocol/code/labels; obtain its own artifact copy; rerun verification; retain decision and checkpoint separately | Must use an independently controlled authenticated identity/custody path before review is counted as independent; a `reviewer_ref` string does not establish this |
| Jason/operator | Accept residual risks and storage placement, authorize collection/deployment/promotion, manage recovery | Final authority remains human; fixture verdicts and reviewer recommendations are not execution grants |

Current code runs under the same developer account and does not enforce these OS or
service boundaries. Proposed connected use requires separate writer and reviewer
accounts/access controls, with writer denied modification of accepted checkpoints,
review records and evaluator policy. Choose actual accounts, storage paths and
resource budgets at the bounded deployment gate; none are provisioned by this design.
Reuse established identity/backup mechanisms where suitable, without borrowing an
existing task's credentials or weakening its controls.

## Review and checkpoint custody

1. Freeze the experiment and exact evaluator/dataset/source digests before execution.
   Review the plan for sample independence, leakage, expected labels and acceptance
   rules. The current four synthetic families cannot establish representative quality.
2. Export the complete synthetic event chain. The reviewer obtains a separately
   controlled copy of its expected final head and artifact digest, tied to the accepted
   commit. A hash copied only from the candidate file is a consistency check, not
   independent custody. A Git commit alone does not authenticate measurements.
3. Inspect and pin the verifier and dependencies before running them. Use a clean
   offline environment with no production secrets or service startup. Do not execute
   the experiment runner just to verify a saved result.
4. Run `verify_evidence.py EXPORT --expected-head sha256:...`. It reads at most 2 MiB
   and accepts at most 1,000 events, rejects duplicate JSON keys and duplicate/reordered
   records, reconstructs into disposable SQLite, validates lineage/hashes, and
   recomputes paired totals and case summaries. These are prototype bounds, not a
   performance/service SLA. Larger exports need a reviewed capacity change.
5. Treat success only as structural/arithmetic verification. Check measurement
   provenance, label adequacy, implementation correctness and risks separately.
   The output explicitly reports authenticity unestablished and approval not granted.
6. The reviewer records retain/reject/request-more-evidence against the exact verified
   artifact. Jason's approval, when required, is separate and scoped to the intended
   operation. The writer must not manufacture this record from a passing test.

The verifier uses the same contract/aggregation implementation as the writer. It
helps a separate reviewer reproduce checks; it is not an independent implementation
or substitute for security/code review. Untrusted artifacts are data, not instructions.
No shell or code from the export is executed. This prototype is not a hostile-input
service and is not exposed over a port.

## Recovery and failure handling

Restore the stable assistant independently of the evidence plane. For evidence,
first recover reviewer-approved code/dependencies and the independent checkpoint,
then copy the selected artifact into an isolated work area, verify it, and reconstruct
state. Never overwrite the accepted copy while testing recovery. Start optional
collectors/runners only after their separate authorization and identity checks.

A missing checkpoint, mismatch, ambiguous event, absent case or changed total blocks
acceptance. Retain the last verified artifact; quarantine the candidate and record
the failure. An incomplete measurement output is not a completed experiment and
must not be silently overwritten or relabeled. Retry under a new artifact/run ID;
record why. Idempotent ledger append is for exact retries, not a license to repeat
uncertain external effects. Current fixtures have no such effects.

Before operational adoption, prove writer-denied review updates, authenticated review
identity/revocation, isolated restore from protected backup, retention/deletion
behavior, and baseline operation with the entire evidence plane unavailable. Add
Doctor/monitoring only for deployed actionable failures (stale checkpoint, loss,
capacity and restore age), without prompt/principal labels. Jason owns those alerts.
No inventory, firewall, DNS, wiki or derived-mirror facts change for this local design.

## Acceptance state and next gate

The local verifier and synthetic reconstruction test are implemented. Operational
role separation, independent checkpoint custody, real human review and acceptance of
storage/retention remain unfulfilled; M4 is not graduated. No consent is inferred
from approval to push code. The exact pending decision is whether this design and its
privacy boundaries are acceptable for a later bounded deployment proposal; target,
identities, numeric retention and recovery coverage must still be specified there.

Next independent technical work is M1's review packet and integration reconciliation
with AI-PAM, using read-only inspection and local tests. M3 still needs reviewed
representative labels and bounded local-model/resource evidence. M5 cannot start
before its dependency, collection and deployment gates pass. Do not replace these
remaining gates with more synthetic throughput runs.
