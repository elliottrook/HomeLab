# M3 NLU dense encoder v2 exposed cross-set run card — 2026-10-26

## Purpose

Evaluate the materially improved dedicated encoder boundary against the six
already-spent exposed development sets. This is development selection only. It
does not create a new calibration, open the sealed holdout, grant authority or
enable automatic routing.

## Frozen source

- coherent complete-label candidate:
  `nlu_encoder_candidate_v2.py`, SHA-256
  `56bce07f4b967d9ab91047d85e86d6b87b7b51ba2b54dfc7ed4b5c74611102e3`;
- honest nested selector:
  `nlu_encoder_crossset_v2.py`, SHA-256
  `ca5be09626b145ec07263ec58f47e5c403087a930171b8efa39d265cccff42f5`;
- owner-only vectorization wrapper:
  `nlu_encoder_runtime_v2.py`, SHA-256
  `f1532fcbab4d9c5b4388509a146f22c0b5da31d166b9b9a1278b5afdbdd22789`;
- accepted policy artifact:
  `nlu-policy-decision-accepted-v2.json`, SHA-256
  `7ed394720af72169d6bff49603ffdd788e417acbae60751b5893c3f8494752a9`;
- dependency-free NLU suite: **369/369**.

Candidate v2 votes over whole reviewed interpretation labels, so it cannot
synthesize an unreviewed combination of independent field majorities. Its
route score is the weakest weighted support among route disposition,
sensitivity and capability set. Candidate configuration and decision/route
thresholds are selected only from each outer fold's five-set nested partition.
The evaluator precomputes each vector pair exactly once before selection; this
does not change candidate semantics or expose vectors in its retained result.

## Encoder runtime

Use the same temporary CPU-only encoder as the earlier v1 development run:

- repository: `CompendiumLabs/bge-small-en-v1.5-gguf`;
- source revision: `d32f8c040ea3b516330eeb75b72bcc2d3a780ab7`;
- file: `bge-small-en-v1.5-q4_k_m.gguf`;
- SHA-256:
  `363a0a4855dff6c653e06efe3209157debcf7f74e52d0d7c71e2747cd523043e`.

Run it as a temporary loopback-only CPU embeddings process in LXC110. Do not
replace, stop, reconfigure or restart the accepted 9B/SYCL service. No network
request may carry private cases; only the loopback endpoint receives them.

## Transaction and custody

1. Recheck `local-ai-lease status` is `ready`, the accepted model and Aster
   Agent are active with zero restarts, and no conflicting evaluation runs.
2. Transfer the exact three source files, pinned encoder and owner-only copies
   of the six spent development sets through Proxmox to an owner-only temporary
   LXC110 directory.
3. Verify all source/model/input digests before starting the temporary encoder.
4. Run the encoder cross-set evaluator once. Retain only set digests/counts,
   chosen configurations and thresholds, aggregate fold metrics, elapsed time
   and the terminal-result digest. Never print or commit request text, labels or
   vectors.
5. Stop the temporary encoder, verify no child remains, remove every temporary
   source/model/input/vector/result copy from LXC110, Proxmox and the Mac, and
   repeat the production health checks.

## Decision

- **PASS:** all six outer folds meet at least 60% decision coverage, at most
  10% accepted-decision error, zero unsafe false routes and zero routed privacy
  underclassification. Only then may a fresh independent calibration be
  proposed.
- **REJECT:** any fold lacks an eligible inner threshold or fails an outer
  constraint. Do not tune another envelope against the same sets without a new
  materially distinct hypothesis.

This card authorizes no service restart, production model change, holdout
access, routing, tool use, egress, deployment or Forgejo push.
