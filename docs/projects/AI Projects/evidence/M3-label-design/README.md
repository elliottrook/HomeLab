# M3 label-design checkpoint — 2026-09-25

Base local checkpoint: `f3a2e8075922a3a399fdd843c49abe3e87298e8e`.
M4 procedure acceptance and independent checkpoint custody remain open. “Continue”
was not interpreted as approval. No new routing experiment or real interaction
collection was run.

The [human-label protocol](../../labeling/M3-Human-Label-Protocol.md) inventories
existing smoke/conformance data and excludes it from a fresh human holdout. It
specifies a proposed 30-family S0-only effort/ambiguity pilot, a separately gated
300-family screening design, multi-label taxonomy, required/optional/prohibited
capabilities, privacy inheritance, human content review, blinded second review of
all test families, immutable dual-label/adjudication states, retention proposals,
family splits/custody, fixed statistical definitions and conservative decision
thresholds. Single-owner labels are personalized preference, not independent
correctness. Calibration remains unsupported without adequate independent data.

The [blank case form](../../labeling/CASE-TEMPLATE.md) and
[empty metadata template](../../labeling/batch-template.json) contain no human
labels. The metadata-design validator rejects raw/real fields, claimed human
verification, conflicting/unknown labels, missing mandatory prohibitions,
private-capability/public-egress mismatches, excluded events, cross-split families,
reused references, duplicate JSON and oversized input. Seventeen new tests pass;
the complete harness/evidence suite now passes 73 tests.

Technical review found and prompted corrections to privacy inheritance, executable
pilot ambiguity, incomplete statistical definitions, label independence and S0
content-review assertions. Those corrections are explicit rather than hidden.
Current software still accepts only synthetic fixture metadata. A human-labeled
pilot is **not executable** until the protocol is accepted and a separately reviewed
implementation/storage/retention readiness gate is passed. The document specifies
that future state machine but does not provision identities or authenticate users.

The empty-template result reports zero rows/families/human-verified labels and
both collection/evaluation authorization false. There is no cloud/model call,
package installation, deployed service, scheduled collector or private dataset.
The only web reads checked primary calibration-method references; those sources
are cited in the protocol and do not justify the proposed local sample sizes.

Next exact human decision: accept/reject/revise the S0-only protocol design,
including effort limits, proposed screening thresholds, reviewer requirements and
retention exclusions. Acceptance alone does not activate collection; implementation
and independent storage/custody must first be reviewed. M1 Stage2 and M4 human
review gates remain separately open. No push is authorized for this checkpoint.

Corrective technical review independently reran all73 harness tests and accepted
the corrected semantics. This is software/design review only; it is not Jason's
protocol acceptance, a human label, or independent checkpoint custody.
