# Stream A — remaining delivery map

**Owner-facing checkpoint, 2026-10-09.** This page translates the detailed [programme](Aster-Adaptive-Computing.md) and [Codex delegation gates](Codex-Delegation.md) into the next decisions. It does not authorize a deployment, additional cloud question, new tool grant or Git push. Evidence links control factual claims; an unchecked gate remains open even if a nearby experiment passed.

## Where we are

Aster Companion version 16 is installed in **ordinary mode**. Its manual Codex screen is hidden unless explicitly launched for a supervised experiment. Fourteen earlier fictional turns plus one Nova process-interruption turn are recorded as completed. A reviewed question can reach subscription-backed Codex and its **original** answer can be recovered after the Companion process is restarted; the [one-attempt result](evidence/D3-active-turn-interruption-result-2026-10-09.md) has a possible signal/completion race. No Aster tools or infrastructure permissions were granted for those turns. The [twelve-answer second pass](evidence/D3-existing-answer-second-pass-2026-10-09.md) found eleven clear frozen-rubric matches and one qualified wording concern. A [separate read-only review](evidence/D3-Orion-independent-review-2026-10-11.md) judged the flagged Orion case a qualified pass; the other eleven were not independently re-scored.

This establishes a **bounded manual handoff**, not routine Ask Codex, automatic engine selection or a Codex sysadmin. The existing household/assistant path remains separate. Local Qwen's general-sysadmin trial was closed without promotion; that does not remove local models from cheaper or narrower tasks.

**2026-10-11 backend change:** read-only checks now find the B60 with a 32 GB
physical BAR and the accepted local 9B model served by llama.cpp SYCL FP16,
not Vulkan. The [current-runtime record](evidence/Stream-A-SYCL-runtime-reconciliation-2026-10-11.md)
pins the changed implementation for future routing measurements. No Stream A
quality or latency result for SYCL has yet been established; D3 and M1 gates
do not change. The repository gateway prompt and current references contained
stale Vulkan claims; local corrections and dated evaluation copies are staged,
and a bounded live correction now aligns the deployed deterministic identity,
prompt and curated knowledge with 9B/SYCL. A service-account retrieval check
passes against the full refreshed 1,825-source snapshot. The deterministic
identity shortcut is now represented locally and the staged 199-test suite
passes. The Doctor reader was later transplanted with a 199-test hybrid pass;
the [branch gateway file now exactly matches the deployed file](evidence/SA0-gateway-UI-source-parity-2026-10-12.md). Eight of its nine directly imported local modules also match production; the [Lab Operations difference](evidence/SA0-gateway-module-parity-2026-10-12.md) is an uninstalled operator-only reconciliation candidate plus a now-corrected local 9B response label. This is source reconciliation, not a deployment or whole-application release; integration gates remain separate. Authenticated answer quality
is unverified.

## Remaining milestones, in delivery order

| Milestone | What changes for Jason | Evidence needed to finish | Current state |
|---|---|---|---|
| **1. Decide the limited manual Codex release (D3)** | A reliable, explicitly chosen “Ask Codex” path in Companion, still without infrastructure tools. | Show normal token refresh and prompt behavior without another model question; a release/hold decision with a verified signed rollback. A failed observation means **hold**, not more repeated question trials. | Independent Orion judgment is a qualified pass. [Signed-in request with no Keychain prompt](evidence/D3-natural-session-observation-2026-10-11.md) is a partial pass; actual refresh is unknown. [Version 16](evidence/D3-native-v16-installation-2026-10-11.md) is installed in ordinary mode with a verified v15 rollback; [ordinary sign-in and read-only AI-PAM use](evidence/D3-native-v16-installation-2026-10-11.md) are now observed. Jason reported one first-launch Keychain prompt and selected Always Allow; two read-only AI-PAM observations showed no repeat prompt. No natural refresh event has occurred, so routine release remains **held**. |
| **2. Complete normal Companion job handling (rest of D3)** | Jason can see a job continue/reconnect, distinguish busy, unavailable and quota states, and understand cancellation or an uncertain outcome. | Offline lifecycle tests and a small, separately reviewed ordinary-use check; preserve request IDs, never resubmit uncertain work, and keep basic Aster available when Codex/Mac/Internet fails. Follow-up context and notifications need explicit scope rather than being silently inferred from the pilot. | A [durable failure-category candidate](evidence/D3-durable-failure-category-2026-10-11.md) passes offline suites and is bundled in installed v16; its ordinary-use behavior is unverified. General intake/notification are **not released**. |
| **3. Establish the authority boundary before connected tools (M1 + D4 prerequisite)** | Codex may ask for narrowly scoped read-only evidence; it cannot obtain permissions by choosing a route. | Verify AI-PAM caller binding, demotion/revocation, expiry, stale policy, duplicate approval consumption and recovery; register each read-only target and keep secrets out of model context. Any connected capability has its own deployment gate. | Open; worker identity currently inactive with zero grants. |
| **4. Prove useful read-only sysadmin investigation (first D4 role)** | Aster can hand a real but bounded diagnostic question to Codex and explain findings, uncertainty and evidence. | Representative incidents, provenance and freshness, actual read-only tool behavior, independent technical postchecks, and a clear pass/fail rubric. No fix or generic shell authority follows from diagnostic success. | Not started as a Codex operational role. |
| **5. Qualify one supervised repair class (later D4/SA4)** | Only an exact reversible fix can be proposed and, after Jason's specific approval, carried out. | Precondition/checkpoint, exact target and action, AI-PAM grant, independent postcheck, rollback, uncertain-outcome reconciliation and emergency stop. | Not authorized. |
| **6. Add low-resource automatic handover (M3–M6)** | Routine requests stay on deterministic/local paths; only requests that need stronger capability go to Codex or another approved provider, with privacy and cost controls. | Stable Decision/Capability contracts, representative routing labels, calibrated abstention, shadow comparison, measured latency/privacy/cost, and one evidence-backed promote-or-reject decision. The first route is read-only; a route never grants tools. | Contracts and historical baselines exist. The historical full-file-pinned probe remains frozen; an [explicit offline v2 component-pinned probe](evidence/M3-selector-pin-drift-2026-10-11.md) passes synthetic conformance but does not establish routing quality. Automatic routing and Learning Plane promotion are not live. |
| **7. Operational graduation (M7/SA5)** | Jason can trust the *specific* demonstrated roles in normal use, with recovery and clear explanations. | Independent critical-path passes, degradation/restore checks, monitoring, documented limits and Jason's acceptance. This is role-specific, not a claim of universal autonomous administration. | Open. |

Milestones 3 and 6 can make **offline** progress in parallel with the passive D3 observation. Connected tools wait for milestone 3; automatic routing does not need to be built before a limited manual Codex release. The earlier SA0–SA5 table records operational requirements and historical Qwen work; it is **not** a second obligation to rerun the closed Qwen general-sysadmin trial. Its still-applicable authority, investigation, repair and acceptance checks map into milestones 3–7.

The existing D4 aggregate Doctor adapter now closes a file-open race, rejects
symlinked or writable reports, and fails closed on malformed status types; see
the [live boundary record](evidence/D4-doctor-adapter-live-boundary-2026-10-11.md).
It remains aggregate-only and does not alter the connected-tool gate or release status.

The existing ARR aggregate report can answer a simple named-service status
question locally. Its [offline file-boundary hardening](evidence/ARR-report-file-boundary-2026-10-09.md)
does not turn that question into a Codex sysadmin role or grant access to a
repair candidate.
The [malformed-input review](evidence/ARR-report-malformed-input-boundary-2026-10-11.md)
also found two local fail-closed gaps and a path-bearing OS error in that
reader. The narrow fix passed 110 focused/integration tests, was reconciled
against the installed file and deployed with an exact-hash checkpoint. Aster
health and the six-service sanitized report passed postchecks. This is reader
hardening only; it is not a Codex diagnostic or a new permission.
The completed Home Assistant advisor's saved report had become stale even
though cron continued to invoke its producer. The [freshness recovery](evidence/HA-report-freshness-recovery-2026-10-11.md)
pins a cron-PATH failure, a one-line absolute `qm` path repair, fresh delivery
and reader hardening. This repairs the local report-backed status path; it does
not add Home Assistant control authority or release Codex routing.
An offline Doctor check now detects a missing or over-15-minute HA report file,
and the Aster health wording no longer claims the old Vulkan backend or
unmeasured GPU offload. This script edit is local only until repository
synchronization and operator adoption; it is not an always-on alert.
The [Forgejo/NetBox report reader boundary](evidence/source-report-reader-boundary-2026-10-11.md)
received the same narrow file and malformed-field hardening after a 124-test
local pass. Both existing source reports and Aster health passed postchecks;
no producer, source service or Codex authority changed.

An [offline D3 view candidate](evidence/D3-manual-uncertain-result-2026-10-10.md)
now checks the recorded request after an uncertain native bridge result and
offers only the existing recovery/reconciliation path where the journal proves
one. It is not installed and does not change the limited-release HOLD.
The [recorded-job status candidate](evidence/D3-job-state-presentation-2026-10-10.md)
also distinguishes waiting, offered, accepted, last-reported-running and
uncertain work in the disabled remote-worker view. It is presentation only;
quota classification and routine job handling remain open.
The [terminal-failure acknowledgement candidate](evidence/D3-terminal-failure-ack-2026-10-10.md)
lets a verified failed/stopped native turn be acknowledged before a new
reviewed question, while uncertain turns remain blocked. It is offline only.
The later [failure-category candidate](evidence/D3-durable-failure-category-2026-10-11.md)
retains only an allowlisted code with a confirmed failed turn so the native
view can distinguish limits and outages after a restart. It is bundled in
installed v16, but real provider-code behavior and the release gate are unproven.

### What the next connected-tool gate actually lacks

Repository evidence shows [M1 Stage1](evidence/M1-stage1-deployment.md)
deployed caller binding and restrictive checks, while the
[Stage2 approver/assurance candidate](evidence/M1-stage2-candidate.md) is **not
deployment-ready**: the current Authentik claim has not been proven to convey
passkey-specific assurance to Companion, and the allowed Aster process can
still supply actor metadata at the approval socket. This is an authority
boundary, not a model-quality problem. Do not solve it by giving Codex SSH,
root, a generic broker token or a broad Keychain exception.
The Aster-as-approver Stage2 candidate is retained for provenance but
superseded as a deployment shape by the separate-verifier proposal.
The [approval-ingress options](evidence/M1-approval-ingress-options-2026-10-10.md)
record a dedicated verifier as the preferred candidate if in-app privileged
approval remains required. A [read-only live recheck](evidence/M1-live-approval-boundary-recheck-2026-10-11.md)
confirmed Aster's approval-socket group membership and a deployed broker
source difference from the repository candidate. The verifier is not deployed,
and the passkey-claim proof is still missing. A [synthetic independent-ingress
candidate](evidence/M1-independent-approval-ingress-candidate-2026-10-11.md)
passes local denial tests and a disposable HTTP-to-broker socket check, but has
no production process or network authority yet. This check did not prove the
real passkey claim or remove Aster's socket access.
An uninstalled process factory now fails closed on missing/mismatched identity
configuration and deliberately has no passkey-promotion setting. The focused
suite passes 23 tests. Separate UID, socket directory, private listener and
proxy-route proofs still gate any deployment.
Retained aggregate proxy logs do not establish routine Yellow approval use;
the separate-ingress **production rollout is deferred** on value/overhead
grounds while Stage2 and connected tools stay held. Keep the offline candidate
for a concrete later need rather than creating a new service by default.
The [Green-only admission assessment](evidence/M1-Green-only-admission-assessment-2026-10-11.md)
finds a possible narrower route to one fixed read-only diagnostic, but the
existing `hlabagent` has broader live capabilities and cannot be reused for
Codex. A distinct least-privilege worker and an explicit M1 gate amendment
would be required; neither is authorized or deployed.
The [live aggregate value check](evidence/D4-live-aggregate-value-check-2026-10-11.md)
found a fresh saved Doctor observation of `fail` across 32 checks but no
failing-check identity. That fails the minimum usefulness threshold for an
aggregate-only Codex diagnostic. Do not create a Green worker or grant merely
for that aggregate; require a privacy-reviewed, named diagnostic output and
held-out value evidence before revisiting the M1 gate.
An [approval-socket lifecycle check](evidence/M1-approval-socket-lifecycle-2026-10-10.md)
also found that a main-broker restart had removed the independent approval
listener's pathname while the service still reported active. The listener was
restored, and a one-line systemd fix was deployed and verified across one
normal main-broker restart. It does not prove full-stop independence or satisfy
the Stage2 identity/assurance gate.

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
The [Doctor projection gate](evidence/D4-Doctor-structured-evidence-gate-2026-10-10.md)
specifies why free-text parsing is insufficient and how one producer-owned
check ID can be tested offline before any model sees diagnostic evidence.
The [typed-check fixture preflight](evidence/D4-Doctor-structured-fixture-result-2026-10-10.md)
now passes locally, including fail-closed pairing and private-text exclusion.
It is not deployed or connected. Review of the deployed Aster health tool
found a broader existing baseline: it already supplies Doctor's bounded
free-text summaries to Aster's model context. The typed candidate therefore
needs to show a useful privacy/specificity tradeoff against **that** path, not
just against the aggregate-only adapter. Blinded usefulness, M1 authority and
real-incident gates remain open. Do not promote schema 2 or expand model egress
on the strength of the parser tests.
The [seven-case offline contract comparison](evidence/D4-Doctor-structured-fixture-result-2026-10-10.md)
found no family-identification gain over today's human-summary path for its
single Aster failure. It did demonstrate that the current Aster reader forwards
dynamic text and does not reject a stale report. The next low-complexity
candidate was to harden that existing reader and keep aggregate status for
simple questions; schema 2 remains unpromoted. On 2026-10-11, the candidate
was tested against a copy of the deployed gateway, including required imports.
All 199 gateway tests passed. The narrow reader change was deployed with a
retained source checkpoint; Aster stayed healthy and its service account could
still read the current 32-check report. This changes the existing local
health path only. The D4 connected-tool, schema 2, blinded usefulness and M1
authority gates remain open.

## Immediate next action and stop rule

No new live Codex question is needed now. Preserve version 16 in ordinary mode and its verified version-15 rollback. The natural signed-in request and absence of a Keychain prompt are recorded, but token refresh remains unknown. Seek a future ordinary-use observation after a known expiry boundary without printing tokens, changing Keychain access or forcing repeated questions. Then decide **release limited manual handoff** or **hold**. Continue offline M1/D4 boundary design while waiting; do not grant tools, start a gateway worker or enable automatic routing under this checkpoint.
