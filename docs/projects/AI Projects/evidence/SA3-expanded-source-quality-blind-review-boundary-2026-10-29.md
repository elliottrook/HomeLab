# SA3 expanded-source quality blind-review boundary — 2026-10-29

Status: **SOURCE-ONLY PASS; AWAITING PREDICTIONS**

The complete expanded-quality source suite passes **31/31**.

The post-run review path is now defined before any model output exists. The
offline builder accepts only the exact 20-case frozen packet and a complete,
error-free, no-retry result bound to its canonical digest. It emits a review
packet under a neutral candidate alias and removes the model identity, latency,
answer keys and mechanical expected answers.

Every reviewer response must bind the canonical review-packet SHA-256, identify
the reviewer, assert that the review was model blind, cover all 20 identities
exactly once and provide booleans for diagnosis, evidence, freshness, scope,
verification and no-false-completion. Missing, duplicate, malformed or
non-boolean judgments fail closed. Only the projected review rows are later
combined with the separate answer key by the existing fair scorer.

This source boundary makes no model call and does not pre-fill or predict any
review judgment. A runtime error, retry, incomplete response, effect claim,
unknown capability or identity mismatch prevents creation of a review packet.
The boundary does not qualify a model and grants no routing, tool or repair
authority.
