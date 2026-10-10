# V5b accepted-corpus descriptive result — completed

Date: 2026-09-26
Result: **VALID DESCRIPTIVE RUN; NO ROUTER PROMOTION**

## Execution result

Jason approved frozen release-manifest SHA-256
`721c377dccca4fef1a685427d85f791559f67686b8bbf533439589f88b3a5d0f`.
The first archive extraction introduced 30 macOS AppleDouble `._*` files. Exact-set
validation stopped before ISO or VM creation. Under a second explicit approval, a
hash-bound script verified the complete unexpected set and every intended file,
deleted only those 30 metadata files, and proved the exact 24-file stage.

Fresh VM123 then passed the stopped no-vNIC/no-agent configuration gate. Its
491,520-byte ISO is SHA-256
`2de12b7c2d5e10b0c36d298ac2a89d9fbb7dae304d2c6225fa561a79b8c08627`.
The one offline boot completed the corpus unit and emitted exactly one protocol
envelope. Strict framing and semantic result validation passed:

- run: `corpus-descriptive-002`;
- payload: `dc2a9274ae01c6c56c2216f6ae151f96eecd748103e57dce5638d661879165c0`;
- result: 36,453 canonical bytes, SHA-256
  `accfb55f825605451a6742e6aa5c25b0c52b40722915f2cc737f20342bec3198`;
- capture: 153,377 bytes, SHA-256
  `f85a6a7cdcfd2f16a84e08ca0792e03eea60ff95659d1b49a868ce05b3da71f0`;
- evaluator elapsed time: 118,140,122 ns; peak process RSS: 20.34 MiB;
- stop reason: null; capture exit: 0; host stop: not required; and
- VMs118–123 are stopped after the run.

Both copied remote receipt indexes reproduce with zero mismatches. The raw serial
capture is not committed because it includes boot noise and generated SSH host-key
material. Its bounded hash, size and sanitized decoded result are retained here.

## Descriptive results

All fractions below have exactly ten exposed development families as denominator.
They describe this accepted pilot and are not accuracy, calibration or
generalization estimates.

| Input profile | Engine | Complete | Coverage | Status matches | Missing-capability cases | Extra-capability cases | Covered error fraction |
|---|---|---:|---:|---:|---:|---:|---:|
| Request only | Always abstain | 0/10 | 0% | 0/10 | 0 | 0 | N/A |
| Request only | Existing keyword rules | 4/10 | 60% | 5/10 | 1 | 0 | 33.3% |
| Request only | TF-IDF nearest, fixed 0.2 | 6/10 | 100% | 9/10 | 2 | 4 | 40.0% |
| Request + synthetic context | Always abstain | 0/10 | 0% | 0/10 | 0 | 0 | N/A |
| Request + synthetic context | Existing keyword rules | 3/10 | 70% | 6/10 | 2 | 2 | 57.1% |
| Request + synthetic context | TF-IDF nearest, fixed 0.2 | 8/10 | 100% | 9/10 | 1 | 2 | 20.0% |

No engine predicted a prohibited capability. Request-only pairwise disagreements
were 60%, 100% and 70% for abstain/rules, abstain/nearest and rules/nearest.
Context-assisted disagreements were 70%, 100% and 80% respectively.

On this finite corpus, H1 passed descriptively: keyword rules completed more cases
than always-abstain. H2 passed descriptively: fixed nearest completed more cases
than keyword rules in both profiles. H3 also passed: context changed two keyword
predictions and three nearest predictions. Context produced two nearest gains and
no nearest losses, but produced no keyword gain and one keyword loss. It is
therefore an input-sensitive diagnostic, not a uniformly beneficial feature.

## Latency and overhead

Warm median/p95 routing latency was approximately 8.3/11.4 microseconds for
request-only keyword rules and 26.7/43.8 microseconds for request-only nearest.
With synthetic context it was 16.0/36.3 and 70.7/113.3 microseconds respectively.

The guest reached the evaluator around 131 seconds after boot and powered off near
135 seconds, while evaluator work took about 0.118 seconds. The disposable VM is a
useful evidence boundary but is unsuitable as a per-request serving harness. Most
observed wall overhead came from boot and the image's network-online wait despite
having no vNIC. This is operational evidence for keeping the production decision
path outside this VM mechanism.

## Decision boundary

This result supports retaining both routing implementations as cheap benchmark
baselines and using their disagreements for future labeled evidence. It does not
justify production selection, threshold tuning, model replacement, confidence
claims, privacy claims, policy changes or permissions. The ten development
families are exposed, small and not an independent holdout.

The S0 descriptive experiment is complete. Its result can feed the M3 harness and
routing decision, while M3 remains open pending controlled harness comparisons and
local-model evidence. No retry, promotion, cleanup, VM deletion or Git push follows
from this result.
