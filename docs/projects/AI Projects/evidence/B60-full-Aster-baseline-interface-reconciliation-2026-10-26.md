# B60 full-Aster baseline interface reconciliation — 2026-10-26

## Exact B60 receipt acknowledged

Stream A fetched Forgejo branch `codex/b60-adaptive-coordination` and read exact
commit `11febf11386982cba001ae3e08d6b5df5b67c794`.

The acknowledged file is
`docs/projects/B60-Inference-Engineering/launcher-fix-and-calibration-feasibility-receipt-20261026.md`,
SHA-256
`106ab591f4a855f515d7c9bfbebaade4dc6ad7c9406d35e9444664f616b554ae`.
It correctly treats the old `subprocess.run`/`communicate()` launcher defect as
historical after the installed correction, and it does not claim independent
target verification that B60 did not perform.

The branch had advanced to `64d909bb` when fetched. That later commit does not
change the identity of the exact receipt above.

## What is and is not the full-Aster baseline

NLU calibration coverage, the E5 CPU routing gate, fixed Doctor formatting and
component-only D4 scores are useful subproject evidence. None is the baseline
for admitting a 27B-plus reasoning challenger. The required baseline is the
accepted Qwen3.5-9B Q4_K_M / llama.cpp b11429 / SYCL / reasoning-off stack
executing complete Aster requests through the same production request,
retrieval, answer and response path that a challenger would replace.

The current repository does not yet contain a frozen matched full-Aster
complete-useful-answer baseline with owner-accepted p50/p95 bounds. That is a
source and decision gap, not permission to infer a baseline from NLU or Doctor
results.

## Concrete remaining contract

Before a B60 challenger can be admitted, the owner must freeze one bounded,
representative request packet and the following decision contract:

1. **Quality:** a complete-useful-answer rubric, per-case critical facts,
   citation/provenance requirements where applicable, abstention rules, and a
   minimum overall plus per-family pass floor.
2. **Safety:** zero fabricated tool/effect claims, zero unsafe action advice,
   zero privacy underclassification, and no capability outside the frozen
   allowlist. Model output never grants authority.
3. **Latency:** end-to-end request p50 and p95, time to first token, total wall
   time and timeout rate measured at the Aster boundary. The owner must state
   absolute ceilings and the allowed challenger delta before results exist.
4. **Resources:** prompt/output tokens, queue/prefill/decode timing, peak GPU
   and host memory, and recovery time, all from the same packet and run budget.
5. **Comparability:** the 9B baseline and challenger receive the same sanitized
   input, retrieval snapshot, response schema, retry policy and scoring owner.
   Reasoning content is not retained.

## Admission and recovery mapping

- **D4 candidate-H** supplies a bounded read-only diagnostic workload and its
  complete-useful-answer scoring path. It may be included only after its fresh
  live diagnostic admission succeeds; its inactive installation is not a
  baseline result.
- **M3 NLU** supplies interpretation/routing quality evidence and must remain a
  separate no-authority metric family. Its labels or calibration threshold do
  not substitute for full-answer quality.
- **27B-plus challenger** runs only inside a proven F6 lab-hours transaction:
  acquire the whole-host lease, arm the independent watchdog, isolate the
  competing consumers, start the exact pinned model/runtime, run the frozen
  matched packet, then restore the accepted 9B Q4_K_M/SYCL command, services
  and schedules exactly.
- Admission is complete only after the independent recovery observer verifies
  accepted model identity, service authentication, guest/host health, fixed
  schedules and lease cleanup. An uncertain recovery rejects the challenger
  result regardless of answer quality.

## Current gate

F2 is conditionally scheduled for the October 27 cycle and F3 remains
conditional on three accepted archive rows. F4/F5 and the full F6 recovery
exercise remain open. Therefore B60 may help define the source-only matched
baseline packet and scoring contract now, but no 27B-plus model/runtime launch
or production isolation is admitted yet.

No model request, lease, service change, restart, private-data read, effect or
remote write was performed for this reconciliation.
