# D4 Doctor evidence projection gate — 2026-10-10

**Status:** offline design decision; no Doctor, Aster, AI-PAM or Codex tool deployment. Connected sysadmin investigation remains HOLD.

## Repository evidence

`scripts/build-aster-health-report.py` converts Doctor's colored free-text lines into up to 32 records containing `name`, `status` and `summary`. Each record currently has the same name, `HomeLab Doctor`; its summary is free text capped at 500 characters. `scripts/doctor.sh` produces many dynamic summaries containing service state, addresses, counters and command-derived text. The existing `doctor_incident_adapter.py` intentionally projects only overall status, check count and report digest. This avoids forwarding raw summaries but cannot identify which subsystem failed. No live report contents were read for this decision.

**Architectural inference:** Parsing the summaries downstream with regex would create a fragile, privacy-sensitive second interpretation of Doctor's human output. A future local or cloud model must not receive arbitrary summary text merely because the report is called “sanitized.” The current aggregate adapter is adequate for “is the lab healthy?” and inadequate evidence for “why did this service fail?”

## Smallest useful contract

Add a stable, producer-owned `check_id` to a separately versioned report schema for a deliberately small set of diagnostic checks. The identifier must be selected at the check site, not guessed from the rendered sentence. Emit an allowlisted `state` (`pass`, `warn`, `fail`, `unavailable`), observation time and source/report digest; omit command output, hostnames, addresses, raw summaries and arbitrary facts from the model-facing projection. Unknown or unregistered IDs become `unavailable` for that capability. Keep the existing human-readable Doctor report and aggregate Aster path compatible while the new projection is evaluated offline.

Start with one bounded service family, such as Aster agent/inference health, rather than encoding all Doctor checks. The registry should name the source owner, privacy class, maximum age, permitted inference use and exact follow-up observation, with no tool grant implied by the check ID. A request for deeper evidence still passes M1 identity, policy and capability gates; the projection itself must not call Doctor, SSH or a remediation.

## Falsifiable experiment before promotion

**Hypothesis:** one source-owned check ID plus state lets a blinded reviewer identify the affected subsystem more accurately than the aggregate-only observation without exposing dynamic Doctor text.

Use frozen synthetic Doctor outputs for healthy, one-failure, stale, malformed, unknown-ID and injected-summary cases. Build both aggregate and candidate projections from the same input. Compare correct subsystem identification, false specificity, abstention, bytes disclosed and processing latency against a predeclared rubric. Require zero leakage of fixture addresses/tokens/summary text, zero unauthorized producer execution, stable replay, and no regression in existing aggregate consumers. If the candidate adds no useful diagnostic accuracy, reject it and retain the aggregate path.

**Promotion boundary:** only an offline read-only evidence adapter may be considered after those checks. Real incident use, model egress and connected Codex tools still require the independent M1 authority gate, representative incident evidence and separate rollout approval. No general shell or repair ability follows from this experiment.
