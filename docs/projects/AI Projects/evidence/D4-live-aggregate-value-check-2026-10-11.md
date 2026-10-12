# D4 live aggregate value check — 2026-10-11

**Decision:** do not build or grant an aggregate-only Doctor capability to a Codex worker as the first connected sysadmin tool. This is a value decision, not permission to expose the existing detailed report. M1 Stage2 and all connected Codex tools remain **HOLD**.

## Question and falsifiable threshold

Could the existing privacy-safe Doctor incident observation give Codex enough evidence to identify a failing service family in a real saved report, without forwarding human-written check summaries? A useful first diagnostic needs at least a source-labelled, fresh, registered failing-check identity. A whole-lab status and check count alone would fail this threshold.

## Evidence and method

On 2026-10-11 Vancouver time, a read-only command inside LXC 104 invoked the installed `doctor_incident_adapter.read_doctor_observation` as the `aster` account against its fixed saved-report path. The command printed only state, observation time, source, count and unavailability reason. It did not print check names, summaries, report bytes, IDs, credentials or the report digest. It did not run Doctor, create a broker request, call a model or change a service.

The projection returned `fail`, observed at `2026-10-11T15:17:08.070360Z`, source `homelab-doctor-report/v1`, and `32` checks. It was available rather than rejected. This is an observation of the saved report at the check time; it does not independently verify current lab health or explain the failure. The installed adapter SHA-256 was `9aa2fd804ff3b8eed20171cccf007f5de78b34056efbc43c5ef02bcbe06574ec`; the tracked adapter was `1a167a3ae492eaba7db3b7e28c3d89533ba19897751f6659466c6c90053d4b4f`. Source inspection showed the installed version predates the tracked no-follow, single-open file-boundary hardening. No deployment was inferred from repository code.

## Result and implication

The observed projection cannot identify which of the 32 checks failed. It therefore fails the predeclared minimum for a Codex diagnostic even while satisfying a useful coarse status function. A dedicated Green-only worker plus grant would add account, policy, audit and recovery work without proving diagnostic value. Retain this aggregate for local status questions and incident context, but do not present it as a Codex sysadmin pilot.

The repository's offline schema-2 candidate can name one registered Aster check without carrying human text, but the prior seven-case comparison found no family-identification gain over the existing local Aster health reader for its one Aster failure. The current `lab.doctor.latest` broker capability and local Aster health reader include dynamic human summaries; their Green or local status does not make them approved for cloud egress. No live schema-2 sidecar, safe per-check Codex capability, blinded real-incident usefulness result or dedicated least-privilege worker was established here.

**Next evidence gate:** choose a bounded diagnostic question with a fixed, useful, privacy-reviewed output, then compare its answers against the existing local Aster path on held-out incidents. Require clear incremental value before amending the M1 gate or creating a connected worker. If no candidate clears that threshold, leave sysadmin diagnosis with human-supervised Codex in its existing separate environment and keep Aster's deterministic/local status path.
