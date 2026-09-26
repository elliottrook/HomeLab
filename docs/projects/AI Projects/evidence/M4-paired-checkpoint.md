# M4 paired evaluation checkpoint — 2026-09-25

Jason authorized publication of the lineage checkpoint. Forgejo main advanced to
`7ece81892982fee10a5999cd7844d7360a2d6e25`; a subsequent read-only GitHub ref check
confirmed the automatic mirror reached that same hash. The first mirror check
still showed the preceding commit, so completion was recorded only after it caught
up. This paired-evaluation step is newer local work, outside that completed push.

## Outcome

The [frozen plan](M4-paired-plan.md) ran without tuning: four authored fixture
families, ten measured pairs and two discarded warmups per case. All four families
passed expected completion/tool counts and the candidate-minus-baseline p95 limit
of 5 ms. These are controlled source-slice overhead measurements, not answer quality
or production performance. Ten repetitions do not create ten independent families.

| Case | Baseline p95 ms | Candidate p95 ms | Delta ms |
|---|---:|---:|---:|
| No tool | 0.0430 | 0.0491 | 0.0061 |
| One read | 0.0328 | 0.0543 | 0.0215 |
| Two reads | 0.0369 | 0.0611 | 0.0242 |
| HA read | 0.0493 | 0.0687 | 0.0194 |

The retained [measurement](M4-paired/measurement-001.json) contains 80 measured
outcomes, their registered runs, dataset, experiment, frozen protocol and derived
evaluation: 164 events total. The database backup restored against the final head;
temporary databases were removed. [Manifest](M4-paired/manifest.json) pins source,
schemas, result and plan. Historical M4 artifacts remain unchanged.

The evaluator resolves exact outcome and run events, requires every case/repetition
and both roles, rejects reused or omitted outcomes, and checks experiment/case/role
provenance. Family success requires every case in that family to meet conformance
and overhead rules. The store recomputes totals before accepting the evaluation;
finalization prevents subsequent runs, outcomes or another evaluation. A review can
reference the exact finalized event, but no actual reviewer decision was fabricated.

Fifty-two adaptive tests pass. Seven new tests cover family accounting, omitted and
reused samples, wrong roles/cases/experiments, failed and slow outcomes, fabricated
totals, protocol mutation, finalization and review binding. Legacy Evaluation v1
remains readable but does not provide this paired outcome-derived guarantee.

## Limits and next safe work

No adoption recommendation follows from this small fixture exercise. The original
M3 decision remains retain Aster. Source hashes bind content rather than authenticate
the measuring process; the runner's code defines alternating order and discarded
warmups. P95 with ten samples is the maximum. Source loading, ledger overhead and
aggregation are excluded, and these timings must not be substituted for live load
or full inference latency. Probability calibration is not supported by these
deterministic outcomes; no confidence estimate is invented.

The offline M4 path now covers frozen dataset manifests, authored label provenance,
linked measurements, derived paired evaluation and verified recovery. M4 remains
open for independent proposal/review separation and an approved operational
storage/retention design before connected use. Next safe local work is that design:
record writer/reviewer ownership, independent checkpoint custody, retention and
deletion boundaries, restore order and collection approval gates. Do not create a
collector or deploy a store on the strength of this fixture result. M1 security
review/trust/deployment and M3 representative labels/live-model gates remain open.

No production changes, new dependencies, credentials, private collection, model
requests or network traffic occurred in the experiment. Prior integration decisions
remain applicable: this local prototype creates no new operational service facts
for NetBox, Doctor, monitoring, wiki, mirror, DNS/firewall or service discovery.
The new checkpoint is local; a further push requires explicit authorization.
