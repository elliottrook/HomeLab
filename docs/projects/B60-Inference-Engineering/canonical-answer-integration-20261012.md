# Adaptive canonical capture/scorer integration

Date: 2026-10-12. Status: local offline integration, not a model-quality result
or an accepted production benchmark. No new model/tool/GPU call or permission.

## Receipt and single interface

Read published Adaptive commit
`71d9a41debd827b9dc90d3cc8c35b84e1c48076b`: capture, explicit review scorer,
tests and updated protocol. B60 now uses this owner-defined development format,
not a second task bar. The prior B60 hash-only capture prototype is retained
for regression/history; it is not the integration interface for reviewed runs.
No answer can be reconstructed from that earlier hash-only output and no missing
route/context/inference phase timing may be invented to convert it.

Pins:

- Fixture `b5e7748d5c90a30992cb22dd98aa333b3c7c14ea093a16ea3c29069df5661ef0`.
- Validator `a48c028618c3d3f905863b88a3ee838090d9abed938a0279b4c01568c252e3a2`.
- Capture source `86d9c14cffc569a5f8974d0ce00a8a76b483402836b6a952e192006c5770b199`.
- Review scorer `c1fd4b982eab2b5066355d5952cb05b346850d0a3b265d7206bdcda83e0d9d46`.

## B60 wrapper behavior

`adaptive_answer_review.py` uses the pinned Adaptive functions. It requires
original synthetic attempts, actual capture bytes and a review tied to those
capture bytes. It recomputes capture from source attempts and compares normalized
bytes, rejecting injected fields or timing changes. Caller-provided hashes do
not prove actual backend provenance; that remains a separate invocation gate.
No endpoint, model runner, credentials or deployment function is supplied.

It reports per-class attempt/label-pass/boundary/failure/timeout counts and
descriptive terminal-observed latency using all attempts. If any case in a
class fails its supplied review, label-passed completion percentiles are null,
not recomputed after discarding that case. All-success completion timing is
explicitly **conditioned on supplied review labels**, not an independent quality
or stable-p95 claim. Human review independence is unverified. The output cannot
feed the production release gate and never grants promotion/tool/routing rights.

Eight additional fake-data integration tests cover a complete canonical flow,
timeout preservation, prohibited claims despite completed status, tampered timing,
raw-text injection, stale review, missing attempt and drifted source pins.
All 87 B60 harness tests, 13 Adaptive answer-fixture/capture/review tests and
eight Adaptive route tests pass: 108 total. Fake labels intentionally exercise
schema behavior only; they are not real adjudication of model answers.

## Joint decisions still needed

Adaptive's actual scorer resolves the output-format question; B60 accepts its
development format. Still open: independent/blind reviewer custody and answer
artifact retention; qualification cases; mandatory quality/safety floors;
frozen current-9B per-class complete-answer latency budgets; representative
cache/load/context profiles; actual source-local Aster-path capture/phase
instrumentation; consented comparable Codex adapter; verified shared host lease.

Proposed next action: keep protocol v0 explicitly draft, add a frozen measurement
profile and actual capture invocation identity, then conduct the first six-case
current-control feasibility run only inside the verified lease. Retain all raw
synthetic attempts under approved source-local custody, obtain explicit human
rubric judgments, and export only the canonical content-free summary/review.
That first feasibility run cannot serve as qualification or p95 acceptance.
Independently frozen qualification and sufficient diverse samples follow.

No independent cutoff, mount, storage expansion, scheduler or production change
is made by this integration. Candidate host-backed staging and 04:15 restoration
still depend on the platform-owned tested lease. Publication of this local
integration remains separately approved; the existing return branch contains
the prior prototype, not this newer canonical wrapper, until another push.
