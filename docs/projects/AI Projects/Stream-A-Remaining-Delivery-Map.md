# Stream A — remaining delivery map

**Owner-facing checkpoint, 2026-10-09.** This page translates the detailed [programme](Aster-Adaptive-Computing.md) and [Codex delegation gates](Codex-Delegation.md) into the next decisions. It does not authorize a deployment, additional cloud question, new tool grant or Git push. Evidence links control factual claims; an unchecked gate remains open even if a nearby experiment passed.

## Where we are

Aster Companion version 15 is installed in **ordinary mode**. Its manual Codex screen is hidden unless explicitly launched for a supervised experiment. Fourteen earlier fictional turns plus one Nova process-interruption turn are recorded as completed. A reviewed question can reach subscription-backed Codex and its **original** answer can be recovered after the Companion process is restarted; the [one-attempt result](evidence/D3-active-turn-interruption-result-2026-10-09.md) has a possible signal/completion race. No Aster tools or infrastructure permissions were granted for those turns. The [twelve-answer second pass](evidence/D3-existing-answer-second-pass-2026-10-09.md) found eleven clear frozen-rubric matches and one qualified wording concern, but was not independent.

This establishes a **bounded manual handoff**, not routine Ask Codex, automatic engine selection or a Codex sysadmin. The existing household/assistant path remains separate. Local Qwen's general-sysadmin trial was closed without promotion; that does not remove local models from cheaper or narrower tasks.

## Remaining milestones, in delivery order

| Milestone | What changes for Jason | Evidence needed to finish | Current state |
|---|---|---|---|
| **1. Decide the limited manual Codex release (D3)** | A reliable, explicitly chosen “Ask Codex” path in Companion, still without infrastructure tools. | Independent judgment of the **existing** Orion wording concern; one bounded observation of normal session refresh and prompt behavior without another model question; a release/hold decision with rollback to version 13. A failed observation means **hold**, not more repeated question trials. | Pilot works narrowly; routine release **held**. |
| **2. Complete normal Companion job handling (rest of D3)** | Jason can see a job continue/reconnect, distinguish busy, unavailable and quota states, and understand cancellation or an uncertain outcome. | Offline lifecycle tests and a small, separately reviewed ordinary-use check; preserve request IDs, never resubmit uncertain work, and keep basic Aster available when Codex/Mac/Internet fails. Follow-up context and notifications need explicit scope rather than being silently inferred from the pilot. | Contract and pilot pieces exist; general intake/notification are **not released**. |
| **3. Establish the authority boundary before connected tools (M1 + D4 prerequisite)** | Codex may ask for narrowly scoped read-only evidence; it cannot obtain permissions by choosing a route. | Verify AI-PAM caller binding, demotion/revocation, expiry, stale policy, duplicate approval consumption and recovery; register each read-only target and keep secrets out of model context. Any connected capability has its own deployment gate. | Open; worker identity currently inactive with zero grants. |
| **4. Prove useful read-only sysadmin investigation (first D4 role)** | Aster can hand a real but bounded diagnostic question to Codex and explain findings, uncertainty and evidence. | Representative incidents, provenance and freshness, actual read-only tool behavior, independent technical postchecks, and a clear pass/fail rubric. No fix or generic shell authority follows from diagnostic success. | Not started as a Codex operational role. |
| **5. Qualify one supervised repair class (later D4/SA4)** | Only an exact reversible fix can be proposed and, after Jason's specific approval, carried out. | Precondition/checkpoint, exact target and action, AI-PAM grant, independent postcheck, rollback, uncertain-outcome reconciliation and emergency stop. | Not authorized. |
| **6. Add low-resource automatic handover (M3–M6)** | Routine requests stay on deterministic/local paths; only requests that need stronger capability go to Codex or another approved provider, with privacy and cost controls. | Stable Decision/Capability contracts, representative routing labels, calibrated abstention, shadow comparison, measured latency/privacy/cost, and one evidence-backed promote-or-reject decision. The first route is read-only; a route never grants tools. | Contracts/baseline exist; automatic routing and Learning Plane promotion are not live. |
| **7. Operational graduation (M7/SA5)** | Jason can trust the *specific* demonstrated roles in normal use, with recovery and clear explanations. | Independent critical-path passes, degradation/restore checks, monitoring, documented limits and Jason's acceptance. This is role-specific, not a claim of universal autonomous administration. | Open. |

Milestones 3 and 6 can make **offline** progress in parallel with the passive D3 observation. Connected tools wait for milestone 3; automatic routing does not need to be built before a limited manual Codex release. The earlier SA0–SA5 table records operational requirements and historical Qwen work; it is **not** a second obligation to rerun the closed Qwen general-sysadmin trial. Its still-applicable authority, investigation, repair and acceptance checks map into milestones 3–7.

One offline D4 boundary candidate now closes a file-open race and rejects
symlinked or writable Doctor reports; see [the file-boundary review](evidence/D4-doctor-file-boundary-2026-10-09.md).
It is local only and does not alter the connected-tool gate or release status.

### What the next connected-tool gate actually lacks

Repository evidence shows [M1 Stage1](evidence/M1-stage1-deployment.md)
deployed caller binding and restrictive checks, while the
[Stage2 approver/assurance candidate](evidence/M1-stage2-candidate.md) is **not
deployment-ready**: the current Authentik claim has not been proven to convey
passkey-specific assurance to Companion, and the allowed Aster process can
still supply actor metadata at the approval socket. This is an authority
boundary, not a model-quality problem. Do not solve it by giving Codex SSH,
root, a generic broker token or a broad Keychain exception.

The existing [`sysadmin_investigation.py`](../../../services/aster-agent/sysadmin_investigation.py)
and [`doctor_incident_adapter.py`](../../../services/aster-agent/doctor_incident_adapter.py)
are useful **offline** building blocks: registered evidence types, bounded
incident state and a fixed-path, aggregate Doctor observation. They are not a
connected Codex tool. The Doctor adapter currently supplies status, check
count and report digest, not enough per-check evidence to diagnose a real
fault. The generic observation contract permits free-text summary/fact values,
so source-local sanitization and an explicit data projection remain necessary
before any model egress. The smallest next implementation is a fixed-target,
read-only evidence projection and denial tests, reviewed against M1 before
connection; it is not another framework or a live sysadmin pilot.

## Immediate next action and stop rule

No new live Codex question is needed now. Preserve version 15 in ordinary mode and its signed version-13 rollback. Observe one natural session-refresh opportunity through ordinary Companion use without printing tokens or changing Keychain access; if sign-in or prompt behavior is ambiguous, record **unknown** rather than forcing a refresh. Seek an independent judgment on the existing Orion answer only if limited routine release is otherwise worth pursuing. Then decide **release limited manual handoff** or **hold**. Continue offline M1/D4 boundary design while waiting; do not grant tools, start a gateway worker or enable automatic routing under this checkpoint.
