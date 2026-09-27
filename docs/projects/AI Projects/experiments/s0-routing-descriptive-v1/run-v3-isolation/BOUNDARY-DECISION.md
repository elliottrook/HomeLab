# V4 boundary decision after V3

Decision: **NO-GO for accepted-corpus execution**

The disposable VM remains a credible architecture candidate because V2b proved
fresh-image bootstrap, no-vNIC topology, bounded serial export and clean shutdown.
V3 did not prove the worker boundary: the isolation unit failed before publishing
its digest-bound result. Architecture policy requires positive evidence for every
mandatory control, so absence of an observed escape cannot be counted as a pass.

This is a gate decision, not retirement of the VM design. Preserve VM120 stopped
and retain the failed run. Determine the exact cause through the prepared read-only
stopped-disk forensic plan. A correction may proceed only as a new immutable
candidate with a new
run and instance identity, reviewed hashes and a new execution approval. Do not
reuse this cloud-init instance or call a second boot a retry.

Accepted S0 data, routing engines and model comparison remain blocked. No prompt,
model, skill, policy, permission or architecture promotion follows this run.
