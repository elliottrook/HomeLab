# Fixture harness source pin — 2026-09-26

Status: local correction verified; no source, schema, production or remote mutation.
Owner: Jason. This closes the independent source-pin gap identified in the
[contract comparison](M2-contract-reconciliation.md).

`source-definition.json` now independently fixes the expected full Aster source
SHA-256 to `62a8b3410856d218ad57aeac8c233d3e70a21354995b88a25dd064ce2a40a407`, the
integrated Stage1 source last changed at `39221b7`. The same source was pinned in
the compared selector profile. This pin governs offline fixture compilation, not
a claim that the full Aster file or local approval candidate is deployed.

The strict definition fixes source path, schema version and offline scope. The
loader reads it and hashes source before AST parsing or compilation, then compiles
those same bytes. Missing/malformed definitions and any source drift fail without
updating the pin. Both payload-slice and chat-loop extraction use this check.
There is no CLI flag to accept current source automatically. Changing a pin requires
an explicit reviewed experiment revision and new output artifact, not editing old
measurements to make their provenance match current code.

New benchmark/preload, lineage, paired and tool-loop outputs record expected,
observed and definition digests separately. Lineage/paired evaluator manifests also
include the policy loader and definition. Historical results and their implementation
hashes remain unchanged. Timing values were not regenerated or used for a new
adoption claim.

Sixty-two adaptive tests pass, including six new source-pin tests: provenance,
pre-parse drift denial, nonexecuting drift, single-read compilation, malformed/missing
policy and refusal to auto-update. A disposable four-case lineage run restored
successfully; all eight Aster tool-loop cases passed once with connections blocked.
Only conformance/provenance, not fresh timing samples, is retained in
[validation](M2-source-pin/validation.json). The
[manifest](M2-source-pin/manifest.json) pins this implementation and evidence.

This is content integrity relative to a locally controlled review record, not
cryptographic reviewer authentication or a sandbox for arbitrary source. Someone
who can alter both definition and code can replace both. M4 independent custody
and review remain necessary. Existing test imports of the actual ASGI application
are separately scoped synthetic tests, not measurement compilation paths.

No dependency installation, model request, private-data collection, new service,
production change or push occurred. No operational inventory/integration update is
needed. Local work remains ahead of the last synchronized checkpoint. Before the
next integration, reconcile the newer authoritative ref and concurrent AI-PAM work;
do not automatically update this source pin to accommodate that merge. Stage2
assurance/process-trust, M3 representative/model evidence and M4 independent-review
gates remain open.
