# M4 measured-outcome lineage checkpoint — 2026-09-25

The authorized push published checkpoints through `c10bf84b020860616cd26fe6b10be4a64aa63d35`.
Direct read-only checks through Forgejo guest 108 verified both its main ref and
GitHub's main ref at that full hash. No direct GitHub push occurred. The initial
Git query on the Proxmox host failed because Git was absent; the guest query then
provided the verification. This new lineage step is local and not included in that push.

## Change and evidence

Dataset manifests retain case/family IDs, hashes of synthetic inputs and expected
labels, and explicit authored-label provenance. Registered runs must reference a
previously registered dataset case, a frozen experiment and its exact declared
baseline/candidate artifact. Linked outcomes reference the exact run event and
must match both experiment and run identity. Run identities and outcomes cannot
be duplicated under new event IDs; reviewed experiments reject further runs/outcomes.

The [plan](M4-lineage-plan.md) preceded execution. A fresh four-case exercise passed
4/4 expected completion/tool-count checks. Its ten-event ledger restored against
the original head. [Measured events](M4-lineage/measurement-001.json) include the
preregistration head, source manifests, run/outcome metadata and restore head.
The temporary databases were removed; JSON retains the synthetic evidence. Source,
schema and result hashes are recorded in the [manifest](M4-lineage/manifest.json).
Forty-five adaptive tests pass, including five new lineage tests for changed
datasets/cases, artifact and experiment substitution, duplicate runs/outcomes,
outcome/run mismatch and restoration. An initial test-fixture list violated the
strict tuple schema; correcting that fixture resolved the five setup errors.

## Limits and resume

This exercise records one observation per case and has no paired baseline or
aggregate evaluation. It establishes persistence/linkage, not timing superiority,
representative quality or independent label review. Frozen artifact hashes are
content checks, not authenticity attestations. The source-slice hash identifies
Aster code; the evaluator manifest additionally pins the wrapper and store code.
Legacy unlinked outcome records remain supported and must not be treated as linked
measurements. Existing Evaluation v1 still accepts declared totals rather than
deriving them from outcome event references; it is not used in this exercise.

The prior checkpoint's security/retention limits and integration assessment still
apply. No new dependencies, service, network path, credentials, private data,
production mutation or broker authority were introduced. The old storage proof and
manifest remain historical snapshots; their source hashes intentionally differ
from the extended implementation.

Next safe local step: preregister a paired synthetic experiment with an aggregate
evaluation bound to its exact outcome events, denominator/family accounting and
fixed acceptance rules. Do not turn these four timings into an adoption result or
retroactively register old M3 evidence. M4 remains open for that evaluation path,
independent review separation, provenance/calibration where supported and approved
operational storage/retention. M1 security and M3 representative/model gates remain
open; connected collection and deployment stay gated. New lineage work awaits a
separately authorized push.
