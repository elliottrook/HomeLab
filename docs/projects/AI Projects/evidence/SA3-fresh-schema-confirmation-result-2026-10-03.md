# SA3 fresh schema-confirmation result

Status: **format-conformance gate passed; no operational-provider selection**

The fixed local Qwen schema configuration ran once against the newly sealed
private 20-case confirmation set. It produced 20/20 valid allowed outcome
tokens, 20/20 complete required-control sets, 20/20 empty effects arrays, and
zero invalid or runner-error records. Median model latency was 8.662 seconds.

The private answer-key scorer reported 18/20 semantic matches and zero unsafe
effects. The preregistered gate was output-format conformance, so the semantic
mismatch does not negate that narrow pass. It also does not establish diagnostic
quality or overturn the earlier 12/20 operational baseline failure.

A deterministic ordinal identifier remap was required before scoring because
the fixed runner assigned default ordinal IDs while the fresh key used the
predeclared `sa3-fresh-*` IDs. The remap changed identifiers only, not model
outputs or answer-key content. This is a harness defect to repair on development
data before any later comparison.

Temporary runner, prompt, output, and error files were removed from LXC 110 and
its host. No service, policy, tool, credential, routing, or production action
changed.
