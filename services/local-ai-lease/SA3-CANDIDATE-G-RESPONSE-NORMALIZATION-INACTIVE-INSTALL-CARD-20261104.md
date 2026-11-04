# SA3 candidate-g response-normalization inactive install card — 2026-11-04

R7 attempted all 14 model requests but retained 14 `ValueError` results. The
shared runner required metadata-free OpenAI response and choice objects, while
the accepted llama integration's fixed bounded metadata allowlists include the
standard envelope and choice metadata.

Install exactly four files: host workload registry and release manifest, plus
LXC110 runner and wrapper. The runner comes from mirrored Stream A commit
`56d4d2272cad0cdbd0e5b3fbbc71f35690a4fbbb`; unknown metadata remains
fail-closed and strict diagnosis/verification JSON is unchanged.

Create root-only host and guest checkpoint
`/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-response-normalization-r1-20261104`.
Refuse baseline/source/custody drift, existing checkpoint, non-ready lease,
shared state/lock, failed 34-pin load, runtime-pin mismatch, metadata proof or
rollback uncertainty.

This inactive effect makes no booking, model call, service stop/restart,
blind-review decision, route, tool grant or promotion.
