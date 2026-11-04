# D4 candidate-g r7 response-envelope NO-GO and source correction — 2026-11-04

## Terminal result

Booking `aster-stream-a-sa3-envelope-20261104-1530-r7` is spent and **NO-GO**.
It claimed exactly at 15:30:00 and ended at 15:33:58 after 238 seconds. The
terminal record is `owner-transaction` / `OWNER_TRANSACTION_FAILED_RESTORED`
with `production_restored=true` and no retained result.

All 14 intended model requests were attempted. The bounded guest projection is
`candidate-g result errors:count=14;classes=ValueError`. No prompt, answer,
case identity, response body or exception message was retained.

## Independent restoration

The lease is ready; Doctor is healthy with zero codes; drain state, drain lock,
operation lock and port-11436 listener are absent. EPUB, dispatcher, Doctor,
Proxmox daemons, LXC104/110/116, Aster Agent, accepted 9B/SYCL llama and Speech
are healthy, with zero core restarts.

## Deterministic source defect

Every request used the same response parser. That parser required the entire
OpenAI-compatible response object to contain only `choices`, and each choice to
contain only `message` and `finish_reason`. The accepted llama.cpp integration
already defines and tests its bounded standard metadata allowlists: top-level
`id`, `object`, `created`, `model`, `system_fingerprint`, `usage`, `timings` and
`choices`, plus choice-level `index`, `logprobs`, `stop_reason`, `message` and
`finish_reason`. Other current runners normalize those fields before strict
content parsing.

The candidate-g source correction applies the same fixed allowlists, requires
`choices`, `message` and `finish_reason`, and keeps unknown fields fail closed.
It does not expose, retain or relax the strict diagnosis/verification JSON
schema. A realistic bounded llama metadata fixture now passes, while an unknown
top-level extension still becomes deterministic fallback with `ValueError`.
The runner/batch/envelope suite passes 16/16.

## Next gate

The correction is source-only. A platform update must bind the new runner hash
into the wrapper and workload registry, update the release manifest, install
the exact guest and host files reversibly, and validate the real installed
imports/pins without a model call. R7 cannot be retried or reviewed.
