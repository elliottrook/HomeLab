# M4 review preparation checkpoint — 2026-09-25

The authorized push published `a86a4283fed99d70c3b41285c22fc4a021549527` to Forgejo.
Read-only checks verified Forgejo main and GitHub's automatic mirror at that full
hash. This subsequent review-preparation work is local, not included in that push.

The [storage/review design](../M4-Storage-and-Review-Design.md) now specifies record
classes, synthetic retention, separate writer/reviewer responsibilities, independent
checkpoint custody, restore order, failure handling and connected-use gates. It is
a proposed operational design, not an approval record or provisioning instruction.
No accounts, services, collection, deletion schedule or deployment were created.

The new offline export verifier reconstructs events in disposable SQLite, checks
exact event ordering and chain/lineage, and derives paired totals without invoking
measurement code. It requires a supplied external head, rejects duplicate JSON keys
and caps input at 2 MiB/1,000 events. This is a local reviewer tool, not a network
service or independently implemented evaluator.

Fifty-six adaptive tests pass, including four new verifier tests for reconstruction,
input preservation, checkpoint/chain mismatch, duplicate/reordered records, ambiguous
JSON and oversized input. A separate replay of the retained paired proof verified
164 events with network connections blocked and rejected a forged summary. See
[verification report](M4-review/export-verification.json) and
[source/report manifest](M4-review/manifest.json).

The test head was obtained from the same workspace: independent custody is explicitly
not established. The result grants no human review, authentic measurement provenance
or promotion authority. Old manifests/results remain historical and unchanged.
The main M4 checkbox stays open for real proposal/review separation and accepted
operational storage/privacy design. Calibration remains unsupported by these
deterministic outcomes; no probabilities are claimed.

Next safe independent work: prepare M1's exact independent-review packet and reconcile
its local authority candidate with the separate AI-PAM safe-write candidate through
read-only inspection and local tests. Preserve the other checkout's edits and require
bounded authorization before any combined deployment. M3 representative labels and
local-model/resource gates also remain open. M5 collection/deployment remains gated.

No production, dependencies or operational inventory changed; the prior integration
assessment remains applicable. New review-preparation work awaits separate push
authorization. Jason remains the programme and risk-acceptance owner.
