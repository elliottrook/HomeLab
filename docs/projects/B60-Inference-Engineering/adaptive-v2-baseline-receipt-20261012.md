# A1 v2 baseline received; candidate intake prepared offline

RECEIVED Adaptive `aa1d6dc9` and its publication record for
`835692b909048cf18b34afa169be731330504cdd`, 2026-10-12. Reviewed the v2 result,
admission/custody record, both content-free score exports and ASGI clock design.
The source branch and files, not a chat summary, are the receipt authority.

Recomputed exact export hashes:

- First score: `16e9428e48896e4692a9f874299fb9373ec601e44ea89758c3d341c473fca431`.
- Second score: `7e88c3959ad344f037f47acf4639e0e81af8725f65254fdab23914bd6a81aba3`.

Both scores bind the same packet and raw-capture digest. Recomputed published
row aggregates: 14/20 full-rubric passes each; pass/fail agreement 20/20;
outcome agreement 20/20; calendar-plus-web 0/2. The observed direct-backend
completed median is 1178.5 ms and maximum 2152 ms. B60 did not receive cases,
hidden labels, raw attempts or review packets, and cannot independently
reproduce the judgments or verify the original invocation. Two AI reviewers
agreeing is not proof of independent truth or human adjudication. No stable
p95, full-path latency, safe tool grant or qualified route follows.

## Implemented now, without GPU access

`scripts/b60-inference/holdout_review_receipt.py` checks publication byte pins,
exact content-free schema, unique cases, strict labels/counts, aggregate/row
consistency and review-to-capture alignment. It rejects injected answer text,
wrong pins, false pass/aggregate claims, Boolean counts, nonfinite timing,
capture mismatch and attempts to relabel direct timing as Aster user latency.
It preserves per-class failures and reports agreement, never scores answers.
Output explicitly sets qualification/deployment false and useful-answer
median/p95 null. The owner scorer remains authoritative; this is a receipt
and integrity boundary, not a second benchmark or release policy.
Ten new offline tests pass, including the two exact published exports. Full
focused revalidation totals 142 tests. No endpoint/model/tool/credential call,
private corpus transfer, model download, lease or production change occurred.

## Agreed next candidate interface

B60 agrees with Mini-side owner-custody execution: keep v2 candidate-visible
inputs and hidden keys in Adaptive's existing restricted store. After a
candidate is admitted, Adaptive's runner sends only fictional label-free cases
to the reviewed candidate endpoint. Do not copy keys/packets to B60, reconstruct
requests from score rows or substitute the exposed six-case set. The private
raw-capture digest and public score binding remain separate from manifest proof.

Freeze candidate model/quant, reasoning/token limits, prompt, adapter, runtime,
device allocation, endpoint/egress/retention, clock boundary and pre/post control
cards before invocation. Preserve default EOS-respecting answer tests; forced
128-token throughput is a separate diagnostic. Candidate and control profiles
must be paired; the present aggregate direct-backend timing cannot supply the
original per-class useful-answer ceiling or excuse a slower reasoning stack.
The ASGI clock is in-process app-entry-to-body wiring, not the client accepted/
displayed boundary; full-path instrumentation/admission remains necessary.

Requested Adaptive follow-up: publish the owner-held runner's reviewed candidate
adapter contract and full-path admission plan, finalize per-class quality floors/
sample policy, and verify protected evidence backup (currently UNKNOWN). No
fresh live comparison should be claimed READY from this receipt alone.
Platform-owner shared lease/expiry/recovery and reviewed staging still gate
exclusive trials. Continue safe offline/read-only work concurrently; do not wait
for the exclusive window to finish these implementation tasks.
