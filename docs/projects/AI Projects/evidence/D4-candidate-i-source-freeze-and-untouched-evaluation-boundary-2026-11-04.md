# D4 candidate-i source freeze and untouched-evaluation boundary — 2026-11-04

Candidate-i is now source-frozen as a diagnosis-only model role with fully
deterministic verification and controls. Its exact six-file source identity
is validated, while authority, tools, repair, model calls, routing and
promotion remain denied.

The future evaluation contract is fixed before a packet exists: 20 cases, at
least six abstentions, three distinct model-blind reviewers, at least 18/20
full consensus passes, every abstention passing, and zero false-completion
failures. Both spent candidate-f and candidate-g packet hashes are explicitly
forbidden. Any future packet must be new and untouched by implementation or
selection.

The source freeze now includes the exact untouched packet, diagnosis-only
runner and key-free batch path. The runner accepts only one `diagnosis` field,
normalizes only the fixed known llama response metadata, and fails closed to a
deterministic diagnosis on malformed, expanded, unsafe or failed output. The
batch binds the 20-case packet hash and requires exactly 14 model requests;
the six abstentions make no transport call. Neither runtime module imports the
answer keys or review code.

Twenty-two combined candidate-i tests pass, covering exact file hashes,
diagnosis-only response shape, deterministic verification, the exact 14/6
request split, no retries/effects/authority, key-free imports, authority and
gate weakening, both spent packet exclusions, and missing, changed or symlinked
source. No booking, model call or effect exists. The packet remains unexposed
to candidate-i, a model or a reviewer. The next milestone is platform
registration and inactive transaction construction.
