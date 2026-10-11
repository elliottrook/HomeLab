# D4 Doctor typed-check fixture result — 2026-10-10

**Decision:** retain the offline candidate for further evaluation. Connected Codex tools, model egress, deployment and real incident use remain **HOLD**. This is a contract/privacy preflight, not proof of diagnostic competence.

## What was built locally

- `scripts/doctor.sh` now has an opt-in machine descriptor that emits only `aster.agent_inference` plus `pass`, `fail` or `unavailable` at the existing `check_aster()` site. It emits nothing in ordinary runs. The helper lives inside `doctor.sh` because existing lab-operations deployment paths copy that script without arbitrary new libraries.
- `scripts/build-aster-health-report.py` retains schema 1 and its normal publication path. Only a fresh, explicitly requested `--structured-output` invocation captures the producer event in a private inherited file descriptor and writes a separate local schema-2 candidate. Its run ID, time and SHA-256 digest bind that candidate to the schema-1 report produced by the same process. Captured-input mode and `--publish` cannot be combined with the candidate option.
- The separate `doctor_structured_incident_adapter.py` is **not imported by a gateway**. It reads two explicitly supplied local paths without invoking Doctor, SSH or any tool. It requires the expected file owner, regular non-symlink files, bounded sizes, safe permissions, exact schemas, one registered check, matching report time and digest, UTC age at most 36 hours, and a known state. Failure returns `unavailable` without a subsystem fact. A valid result contains the check ID and state, but no human summary or command-derived value.

## Reproducible fixture checks

Synthetic fixtures tested a same-run Aster failure with a private-text marker in the human summary, typed pass/warn/unavailable, missing and duplicate events, wrong run ID, unknown check ID, duplicate JSON field, stale/future timestamps, digest/time mismatch, extra field, unsafe permissions, wrong owner and symlink. In the one-failure fixture, the existing aggregate adapter reported only overall failure and check count; the candidate identified the Aster service family. The marker did not appear in the candidate observation. The candidate made no root-cause or repair claim.

The schema-2 writer also uses an exclusive, private temporary file and atomic replacement. A synthetic preexisting symlink at the output path was replaced without writing its target. This specifically avoids copying the existing schema-1 writer's predictable `.tmp` filename into the new candidate path; changing the schema-1 writer is outside this experiment.

Validation: five structured-builder tests, four structured-adapter tests, four existing aggregate-adapter tests and six existing Doctor video-archiver tests passed. `bash -n scripts/doctor.sh`, Python compilation with a sandbox-local cache and `git diff --check` passed. No live Doctor run, model call, SSH diagnostic, production file, credential or deployment was used for this experiment. The initial Python compilation attempt was blocked only because the default macOS bytecode cache lies outside the workspace; rerunning with `PYTHONPYCACHEPREFIX=/private/tmp/aster-pycache` succeeded.

## Limits and next gate

The fixtures establish parsing, file and disclosure behavior, not a blinded diagnostic accuracy estimate, latency distribution, sustained reliability or real incident usefulness. The candidate does not yet verify a fixed production path or independent M1 caller authority. Its run ID is checked at event capture; downstream pairing relies on the report digest, timestamp and file ownership, not on a second independently signed run record. The descriptor and run ID can be inherited by Doctor's child processes, so this channel is **not** an authorization or tamper-proof provenance boundary. The current scheduled report still uses captured-input schema 1, so schema 2 is not produced by normal operation.

Next: review the local diff for cross-consumer risk, then run the predeclared synthetic comparison with a blinded reviewer or deterministic scoring harness that cannot see the candidate's expected label. If it adds no useful specificity or leaks dynamic text, reject it. Any live read-only producer trial, model egress or connected Codex capability requires a separate approved gate after M1 identity/policy controls are verified. No general shell or repair grant follows from this candidate.
